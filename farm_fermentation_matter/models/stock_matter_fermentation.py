# -*- coding: utf-8 -*-
from odoo import fields, models

class StockMatterTracking(models.Model):
    _inherit = 'stock.matter.tracking'

    fermentation_order_id = fields.Many2one(
        comodel_name='farm.fermentation.order',
        string="Fermentation Order",
        ondelete='set null',
        index=True
    )
