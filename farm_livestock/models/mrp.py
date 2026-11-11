# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _hook_pre_start(self):
        """[US-003-02] Livestock Health Gating before starting"""
        super()._hook_pre_start()
        if self.industry_type == 'livestock':
            # Identify the biological lot (animal group)
            # In farm_livestock, lot_id is often used on the intervention/task
            lot = getattr(self, 'lot_producing_id', False) # Odoo standard
            if lot and hasattr(lot, 'health_state') and lot.health_state == 'quarantine':
                raise UserError(_("HEALTH BLOCK: Cannot start intervention on animals in quarantine!"))

    def _get_isl_model(self):
        # NOTE (18.0 port): the base hook lived in farm_mrp 19.0 but was
        # dropped when farm_mrp was rewritten for batch 1 (ISL machinery
        # removed) -- the plain super() call would raise AttributeError.
        # Same guard pattern as farm_field_crops (installed, batch 1).
        res = False
        try:
            res = super(MrpProduction, self)._get_isl_model()
        except AttributeError:
            res = False
        if self.industry_type == 'livestock':
            return 'agri.isl.livestock.task'
        return res

class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    # NOTE (18.0 port): upstream farm_livestock assumes ``mrp.bom`` has an
    # ``intervention_type`` field -- the ``active_feeding_bom_id`` domain in
    # farm_lot.py filters on it, and the module's own tests create BoMs
    # with ``intervention_type='feeding'``. Neither Odoo 18 core nor the
    # ported farm_mrp defines it on mrp.bom (it exists only on
    # mrp.production via farm_operation), in 19.0 upstream either. The
    # field is added here with the exact same 10-value selection and
    # default ('process') as mrp.production, so the domain and the tests
    # work; a BoM only counts as a feeding recipe once its type is set
    # to 'feeding' (there is no view exposing the field yet -- set it
    # from the BoM form via debug mode or from the shell/API).
    intervention_type = fields.Selection([
        ('tillage', 'Soil Preparation'),
        ('sowing', 'Sowing/Planting'),
        ('fertilizing', 'Fertilizing'),
        ('irrigation', 'Irrigation'),
        ('protection', 'Crop Protection'),
        ('aerial_spraying', 'Aerial Spraying'),
        ('harvesting', 'Harvesting'),
        ('feeding', 'Feeding'),
        ('medical', 'Medical/Prevention'),
        ('process', 'General Process'),
    ], string='Intervention Type', default='process')

    industry_type = fields.Selection(selection_add=[
        ('livestock', 'Livestock'),
    ], ondelete={'livestock': 'set null'})

    def _get_isl_model(self):
        # NOTE (18.0 port): same missing-base-hook guard as above and as
        # in farm_field_crops (batch 1).
        res = False
        try:
            res = super(MrpBom, self)._get_isl_model()
        except AttributeError:
            res = False
        if self.industry_type == 'livestock':
            return 'agri.isl.livestock.recipe'
        return res
