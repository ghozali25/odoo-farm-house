# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class StockLot(models.Model):
    _inherit = 'stock.lot'

    def _get_isl_summary_parts(self):
        # NOTE (18.0 port): no base _get_isl_summary_parts exists anywhere
        # in the ported tree (the hook lived in farm_mrp, pruned of
        # farm_isl in batch 1) — defensive super(), same pattern as
        # farm_field_crops/models/stock_lot.py. Field name also corrected:
        # agri.isl.lot.aquaculture has no 'current_count' (the count lives
        # in 'animal_count' from agri.biological.inventory.mixin).
        res = []
        try:
            res = super(StockLot, self)._get_isl_summary_parts()
        except AttributeError:
            res = []
        isl = self.env['agri.isl.lot.aquaculture'].search([('lot_id', '=', self.id)], limit=1)
        if isl:
            res.append(_("Aqua: %s, Count: %s") % (isl.animal_count, isl.water_volume_m3))
        return res
