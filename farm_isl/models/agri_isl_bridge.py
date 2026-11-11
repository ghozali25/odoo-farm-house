# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class StockLot(models.Model):
    _inherit = 'stock.lot'

    def action_upcast_to_industry(self):
        """ 
        [ISL Bridge] Automatically creates the corresponding industry proxy model 
        based on the product's industry_type.
        """
        self.ensure_one()
        industry_type = getattr(self.product_id, 'industry_type', False)
        
        mapping = {
            'livestock': 'farm.lot.livestock',
            'aquaculture': 'farm.lot.aquaculture',
            'floriculture': 'farm.lot.flower',
            'medicinal': 'farm.lot.medicinal',
            'tea': 'farm.lot.tea',
            'essential_oil': 'farm.lot.essential_oil',
            'ham': 'farm.lot.ham',
            'aquatic_processing': 'farm.lot.aquatic_product'
        }
        
        proxy_model = mapping.get(industry_type)
        # Port 19.0 -> 18.0 (batch 2): proxy models farm.lot.livestock,
        # farm.lot.aquaculture, farm.lot.flower and farm.lot.medicinal belong
        # to vertical modules that are NOT installed (farm_livestock,
        # farm_aquaculture, farm_floriculture, farm_medicinal_plants).
        # self.env[missing_model] raises KeyError, which would break
        # stock.move._action_done for every receipt. Skip silently when the
        # proxy model is absent; the bridge fires again once that module
        # is installed. No business logic changed for existing proxies.
        if proxy_model and proxy_model not in self.env:
            return False
        if proxy_model:
            # Check if proxy already exists
            existing = self.env[proxy_model].search([('lot_id', '=', self.id)], limit=1)
            if not existing:
                _logger.info("ISL BRIDGE: Upcasting Lot %s to %s", self.name, proxy_model)
                return self.env[proxy_model].create({'lot_id': self.id})
        return False

class StockMove(models.Model):
    _inherit = 'stock.move'

    def _action_done(self, cancel_backorder=False):
        """ 
        [ISL Bridge] Hook into move completion to trigger industry upcasting 
        and DNA inheritance on newly created lots.
        """
        res = super(StockMove, self)._action_done(cancel_backorder=cancel_backorder)
        for move in self:
            for lot in move.lot_ids:
                lot.action_upcast_to_industry()
        return res
