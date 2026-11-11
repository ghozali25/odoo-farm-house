# -*- coding: utf-8 -*-
"""Renewal wizard for GAP certifications (batch 6).

NOTE (port 19.0 -> 18.0, batch 6): upstream
``FarmGAPCertification.action_renew_certificate`` creates a
``farm.certification.renewal.wizard`` record and opens it, but no
module in the repo defines that wizard model — the button would raise
``KeyError`` at runtime. This minimal TransientModel provides exactly
the fields the action passes (``certification_id``,
``certification_model``) plus a ``new_expiry_date`` (default: current
expiry + 3 years, the standard GAP validity noted in
``certification.py``) and ``action_confirm_renewal`` which extends the
certificate and re-validates it.
"""
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta


class FarmCertificationRenewalWizard(models.TransientModel):
    _name = 'farm.certification.renewal.wizard'
    _description = 'GAP Certificate Renewal Wizard'

    certification_id = fields.Many2one(
        'farm.gap.certification', string="Certificate", required=True,
        readonly=True)
    certification_model = fields.Char("Certificate Model", readonly=True)
    new_expiry_date = fields.Date(
        "New Expiry Date", required=True,
        default=lambda self: (self.certification_id.expiry_date +
                              relativedelta(years=3))
        if self.certification_id and self.certification_id.expiry_date
        else fields.Date.context_today(self) + relativedelta(years=3))

    def action_confirm_renewal(self):
        self.ensure_one()
        cert = self.certification_id
        if not cert:
            raise UserError(_("No certificate linked to this renewal."))
        if self.new_expiry_date <= cert.issue_date:
            raise UserError(_("New expiry date must be after the issue date."))
        cert.write({
            'expiry_date': self.new_expiry_date,
            'next_audit_date': self.new_expiry_date - relativedelta(months=3),
            'status': 'valid',
        })
        cert.message_post(body=_(
            "Certificate renewed: new expiry date %s.") %
            self.new_expiry_date)
        return {'type': 'ir.actions.act_window_close'}
