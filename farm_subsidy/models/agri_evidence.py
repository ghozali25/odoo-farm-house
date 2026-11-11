# -*- coding: utf-8 -*-
"""Concrete ``agri.evidence`` model (batch 6).

NOTE (port 19.0 -> 18.0, batch 6): upstream ``farm_subsidy`` uses
``env['agri.evidence']`` in six places and even declares a class
``_inherit = 'agri.evidence'``, but NO module in the repo defines a
concrete ``agri.evidence`` model — only the abstract mixin
``agri.evidence.mixin`` exists in ``farm_core`` (the concrete model
presumably lives in a module that was never ported, e.g. ``farm_gov``).
Without this file the registry fails at install. This minimal concrete
model provides exactly the fields/method the subsidy code and the
QWeb handbook template use (``name``, ``res_model``/``res_id``,
``taken_at``, ``gps_lat``/``gps_lng``, ``is_on_site``, ``note``,
``worker_id``, ``is_hash_verified``, ``verify_evidence_integrity()``)
plus the ``subsidy_application_id`` link from the upstream
``_inherit`` class (merged here) and the evidence fields of the core
mixin (``evidence_hash`` etc.). If a later batch ports a module that
defines ``agri.evidence`` itself, that definition must be changed to
extend this one instead of redefining ``_name``.
"""
from odoo import models, fields, api, _


class AgriEvidence(models.Model):
    _name = 'agri.evidence'
    _description = 'Agricultural Evidence Record'
    _inherit = ['mail.thread', 'agri.evidence.mixin']
    _order = 'taken_at desc'

    name = fields.Char("Evidence Reference", required=True, default=lambda self: _('New'))
    res_model = fields.Char("Related Model", help="Model of the record this evidence proves (e.g. farm.location, project.task).")
    res_id = fields.Integer("Related Record ID")
    taken_at = fields.Datetime("Captured At", default=fields.Datetime.now)
    gps_lat = fields.Float("GPS Latitude", digits=(10, 7))
    gps_lng = fields.Float("GPS Longitude", digits=(10, 7))
    is_on_site = fields.Boolean("On-Site Verified", default=False)
    note = fields.Text("Notes")
    worker_id = fields.Many2one('res.users', string="Captured By", default=lambda self: self.env.user)
    is_hash_verified = fields.Boolean("Hash Verified", default=False, readonly=True)

    subsidy_application_id = fields.Many2one(
        'farm.subsidy.application', string="Subsidy Application",
        ondelete='set null', index=True)

    def verify_evidence_integrity(self):
        """Minimal integrity check: an evidence record counts as verified
        when it carries a hash (the core mixin only stubs hash
        generation — ``_generate_evidence_hash`` returns False)."""
        for rec in self:
            rec.is_hash_verified = bool(rec.evidence_hash)
        return True
