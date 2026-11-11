# -*- coding: utf-8 -*-
from odoo import models, fields, api

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _get_isl_model(self):
        # NOTE (18.0 port): the hook lives in farm_mrp, which is being
        # pruned of farm_isl in batch 1 -- if farm_mrp drops the hook, the
        # plain super() call would raise AttributeError at install. The
        # returned model names are also corrected: 'farm.crop.production'
        # and 'farm.crop.bom' do not exist; the actual ISL models defined
        # in this module are farm.crop.task and farm.crop.recipe.
        res = False
        try:
            res = super(MrpProduction, self)._get_isl_model()
        except AttributeError:
            res = False
        if self.industry_type == 'crop':
            return 'farm.crop.task'
        return res

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    industry_type = fields.Selection(selection_add=[
        ('crop', 'Crop Farming'),
    ], ondelete={'crop': 'set null'})

    def _get_isl_model(self):
        res = False
        try:
            res = super(MrpBom, self)._get_isl_model()
        except AttributeError:
            res = False
        if self.industry_type == 'crop':
            return 'farm.crop.recipe'
        return res
