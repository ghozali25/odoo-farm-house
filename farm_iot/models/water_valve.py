# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class FarmWaterValve(models.Model):
    """
    Autonomous Farm Water Valve ([De-industrialized] / BDD Safe)
    """
    _name = 'farm.water.valve'
    _description = 'Farm Water Valve'
    _inherit = ['mail.thread']

    name = fields.Char("Valve Name", required=True)
    status = fields.Selection([
        ('cutoff', 'Emergency Cutoff'),
        ('open', 'Open'),
        ('closed', 'Closed')
    ], default='closed', tracking=True)
    pressure_psi = fields.Float("Operating Pressure PSI", default=0.0)

    @api.constrains('pressure_psi')
    def _check_pressure_safety(self):
        """Ensure water pressure does not exceed safety limits (150.0 PSI)"""
        for rec in self:
            if rec.pressure_psi > 150.0:
                # Safely transition status to cutoff and raise safety block exception
                rec.status = 'cutoff'
                raise ValidationError(_("WATER_PRESSURE_OVERLOAD_BLOCK: Pressure %s PSI exceeds maximum safety threshold (150.0 PSI).") % rec.pressure_psi)

    def write(self, vals):
        # Intercept pressure writes for safety backpressure protection
        if 'pressure_psi' in vals:
            pressure = vals['pressure_psi']
            if pressure > 120.0:
                # Force cutoff and zero pressure
                vals['status'] = 'cutoff'
                vals['pressure_psi'] = 0.0
                
                # Post red safety alert card on Chatter
                for record in self:
                    card_html = _(
                        "<div style='background-color: #f8d7da; border: 1px solid #f5c6cb; padding: 10px; border-radius: 4px; color: #721c24;'>"
                        "<strong>⚠️ HIGH PRESSURE WARNING</strong><br/>"
                        "Actuator pressure of <strong>%.2f PSI</strong> exceeds safety limit (120 PSI). Backpressure safety loop engaged: Emergency Cutoff activated."
                        "</div>"
                    ) % pressure
                    record.message_post(body=card_html)
                    
        return super(FarmWaterValve, self).write(vals)
