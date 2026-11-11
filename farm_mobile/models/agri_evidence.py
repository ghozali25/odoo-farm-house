# -*- coding: utf-8 -*-
"""Mobile extension of ``agri.evidence`` (batch 7).

RECONCILIATION (port 19.0 -> 18.0, batch 7): upstream ``farm_mobile``
defines ``agri.evidence`` as its OWN concrete model (``_name`` +
``_inherit = ['mail.thread', 'mail.activity.mixin']``), but batch 6
already created the concrete ``agri.evidence`` in ``farm_subsidy``
(``farm_subsidy/models/agri_evidence.py``) because subsidy code needed
it — with CONFLICTING field definitions:

* ``res_id``: subsidy Integer vs mobile Many2oneReference
* ``worker_id``: subsidy res.users vs mobile hr.employee
* ``is_on_site``: subsidy plain Boolean vs mobile computed Boolean
* ``evidence_hash``: subsidy via mixin (plain Char) vs mobile computed
* ``photo``: only mobile, required=True
* ``_inherit``: subsidy mail.thread + agri.evidence.mixin vs mobile
  mail.thread + mail.activity.mixin

Two ``_name = 'agri.evidence'`` definitions with different field types
would fail the registry. Per the batch-6 note ("if a later batch ports
a module that defines agri.evidence itself, that definition must be
changed to extend this one"), this file is now an EXTENSION
(``_inherit = 'agri.evidence'`` only, no ``_name``) that keeps the
subsidy definition canonical and adds only the mobile-only parts:

* ``photo`` Binary — NOT required (subsidy evidence is created without
  a photo; required=True would break the subsidy flow).
* ``evidence_hash`` compute override (same Char type as the mixin
  field) + ``verify_evidence_integrity()`` override with the
  tamper-alert message_post.
* ``is_on_site`` compute override (same Boolean type). Guarded: only
  evidence linked to ``farm.location`` / ``mrp.production`` is
  geofence-checked; other res_models keep False (the subsidy default).
* ``res_id`` stays Integer, ``worker_id`` stays res.users — mobile code
  passes plain ids / never sets worker_id on evidence, so both work.
* ``mail.activity.mixin`` is NOT added: adding a mixin to an existing
  model via ``_inherit`` list would need ``_name`` and would create a
  new model; nothing in farm_mobile needs activity scheduling on
  evidence (``message_post`` comes from mail.thread).

The upstream mobile docstring (CJK) is translated in the method
docstrings below.
"""
from odoo import models, fields, api, _
import hashlib
import json


class AgriEvidence(models.Model):
    _inherit = 'agri.evidence'

    photo = fields.Binary(
        "Evidence Photo", attachment=True,
        help="Field photo captured from the mobile app. Optional: subsidy "
             "evidence is created without a photo.")

    # Overrides of the canonical farm_subsidy definition (same types,
    # computed variants so the hash is stored and tamper-checkable).
    evidence_hash = fields.Char(
        "Evidence Hash", compute='_compute_evidence_hash', store=True,
        precompute=True, readonly=True,
        help="SHA256 hash of evidence data for integrity verification")
    is_on_site = fields.Boolean(
        "Location Verified", compute='_compute_site_verification',
        store=True, precompute=True)

    @api.depends('photo', 'gps_lat', 'gps_lng', 'taken_at', 'worker_id', 'note')
    def _compute_evidence_hash(self):
        """Compute the SHA256 hash of the evidence data (US-055-05)."""
        for rec in self:
            if rec.photo:
                evidence_data = {
                    'photo': rec.photo.decode('utf-8') if isinstance(rec.photo, bytes) else str(rec.photo),
                    'gps_lat': rec.gps_lat,
                    'gps_lng': rec.gps_lng,
                    'taken_at': str(rec.taken_at),
                    'worker_id': rec.worker_id.id if rec.worker_id else None,
                    'note': rec.note or '',
                    'create_uid': rec.create_uid.id if rec.create_uid else None,
                    'create_date': str(rec.create_date) if rec.create_date else '',
                }
                data_str = json.dumps(evidence_data, sort_keys=True, default=str)
                rec.evidence_hash = hashlib.sha256(data_str.encode('utf-8')).hexdigest()
            else:
                rec.evidence_hash = None

    def verify_evidence_integrity(self):
        """Verify evidence integrity (US-055-05): recompute the hash and
        compare with the stored one; post an alert on mismatch."""
        for rec in self:
            if rec.photo:
                evidence_data = {
                    'photo': rec.photo.decode('utf-8') if isinstance(rec.photo, bytes) else str(rec.photo),
                    'gps_lat': rec.gps_lat,
                    'gps_lng': rec.gps_lng,
                    'taken_at': str(rec.taken_at),
                    'worker_id': rec.worker_id.id if rec.worker_id else None,
                    'note': rec.note or '',
                    'create_uid': rec.create_uid.id if rec.create_uid else None,
                    'create_date': str(rec.create_date) if rec.create_date else '',
                }
                data_str = json.dumps(evidence_data, sort_keys=True, default=str)
                current_hash = hashlib.sha256(data_str.encode('utf-8')).hexdigest()
                if current_hash == rec.evidence_hash:
                    rec.is_hash_verified = True
                else:
                    rec.is_hash_verified = False
                    rec.message_post(body=_("EVIDENCE INTEGRITY ALERT: Evidence hash mismatch detected. Data may have been tampered with."))
        return True

    @api.depends('gps_lat', 'gps_lng', 'res_model', 'res_id')
    def _compute_site_verification(self):
        """Check whether the capture location is inside the parcel
        boundary (US-053-01). Only farm.location / mrp.production
        evidence is geofence-checked; anything else stays False."""
        for rec in self:
            if not rec.gps_lat or not rec.res_model:
                rec.is_on_site = False
                continue
            parcel = False
            if rec.res_model == 'farm.location':
                parcel = self.env[rec.res_model].browse(rec.res_id)
            elif rec.res_model == 'mrp.production':
                mo = self.env[rec.res_model].browse(rec.res_id)
                parcel = mo.agri_task_id.land_parcel_id if mo.agri_task_id else False
            else:
                rec.is_on_site = False
                continue
            if parcel and parcel.gps_coordinates:
                temp_fence = self.env['agri.geospatial.geofence'].new(
                    {'coordinates': parcel.gps_coordinates})
                rec.is_on_site = temp_fence.is_point_inside(rec.gps_lng, rec.gps_lat)
            else:
                # No boundary defined: treated as compliant (upstream behaviour).
                rec.is_on_site = True
