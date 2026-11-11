# -*- coding: utf-8 -*-
from odoo import models, fields, api

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _get_isl_model(self):
        # NOTE (18.0 port): no base _get_isl_model exists anywhere in the
        # ported tree (the hook lived in farm_mrp, pruned of farm_isl in
        # batch 1) — defensive super(), same pattern as
        # farm_field_crops/models/mrp.py. Returned model name also
        # corrected: 'agri.isl.aquaculture.production' does not exist;
        # the actual ISL model is agri.isl.aquaculture.task.
        res = False
        try:
            res = super(MrpProduction, self)._get_isl_model()
        except AttributeError:
            res = False
        if self.industry_type == 'aquaculture':
            return 'agri.isl.aquaculture.task'
        return res

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    industry_type = fields.Selection(selection_add=[
        ('aquaculture', 'Aquaculture'),
    ], ondelete={'aquaculture': 'set null'})

    def _get_isl_model(self):
        # NOTE (18.0 port): defensive super() — see MrpProduction above.
        # Returned model name corrected: 'agri.isl.aquaculture.bom' does
        # not exist; the actual ISL model is agri.isl.aquaculture.recipe.
        res = False
        try:
            res = super(MrpBom, self)._get_isl_model()
        except AttributeError:
            res = False
        if self.industry_type == 'aquaculture':
            return 'agri.isl.aquaculture.recipe'
        return res
