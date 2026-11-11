# -*- coding: utf-8 -*-
from odoo import models, fields


class FarmProductionLicenseCategory(models.Model):
    """Generic production license category.

    Replaces the China-specific ``farm.sc.category`` (SC food
    production license categories). Categories are configuration
    data: a country can be attached, so Indonesian schemes (e.g.
    PIRT, halal, BPOM) or any other national scheme can be
    registered as plain records instead of hard-coded values.
    """
    _name = 'farm.production.license.category'
    _description = 'Production License Category'

    name = fields.Char('Category Name', required=True)
    code = fields.Char('Category Code')
    country_id = fields.Many2one('res.country', string='Country')
    active = fields.Boolean('Active', default=True)
