# -*- coding: utf-8 -*-
from odoo import models, fields, api


class FarmProductionLicense(models.Model):
    """Generic production license.

    Replaces the China-specific ``farm.sc.license`` (SC food
    production license). The model is deliberately generic: any
    national production license (e.g. Indonesian PIRT, halal, BPOM)
    is a record of this model linked to one or more license
    categories (farm.production.license.category).
    """
    _name = 'farm.production.license'
    _description = 'Production License'

    name = fields.Char("License No.", required=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    expiry_date = fields.Date("Expiry Date", required=True)
    category_ids = fields.Many2many('farm.production.license.category', 'farm_production_license_category_rel', 'license_id', 'category_id', string="Permitted Categories")
    is_active = fields.Boolean("Is Active", compute='_compute_is_active', store=True, precompute=True)

    @api.depends('expiry_date')
    def _compute_is_active(self):
        today = fields.Date.today()
        for rec in self:
            rec.is_active = rec.expiry_date and rec.expiry_date >= today
