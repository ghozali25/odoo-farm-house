# -*- coding: utf-8 -*-
from odoo import models, fields


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    # Industry classification kept from the former ISL layer; the ISL
    # redirection machinery (agri.isl.model.redirector, isl_record_type,
    # create/write/unlink guards, get_formview_action) was removed with
    # farm_isl (not part of batch 1).
    industry_type = fields.Selection(selection=[
        ('food_processing', 'Food Processing'),
        ('pharmaceutical', 'Pharmaceutical'),
        ('chemical', 'Chemical'),
        ('general', 'General Manufacturing'),
        ('standard', 'Standard'),
        ('livestock', 'Livestock'),
        ('processing', 'Processing'),
        ('aquaculture', 'Aquaculture'),
        ('crop', 'Crop'),
    ], ondelete={
        'food_processing': 'set null',
        'pharmaceutical': 'set null',
        'chemical': 'set null',
        'general': 'set null',
        'standard': 'set null',
        'livestock': 'set null',
        'processing': 'set null',
        'aquaculture': 'set null',
        'crop': 'set null',
    }, string="Industry Type", default='standard')
