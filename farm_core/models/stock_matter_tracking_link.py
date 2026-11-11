# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class StockMatterTrackingLink(models.Model):
    _name = 'stock.matter.tracking.link'
    _description = 'SFC Genealogy Directed Graph Link / Edge'
    _order = 'timestamp desc, id desc'

    parent_id = fields.Many2one(
        'stock.matter.tracking',
        string='Parent / Ancestor SFC',
        required=True,
        ondelete='cascade',
        index=True
    )
    child_id = fields.Many2one(
        'stock.matter.tracking',
        string='Child / Descendant SFC',
        required=True,
        ondelete='cascade',
        index=True
    )
    transition_type = fields.Selection([
        ('sequential', 'Sequential Flow'),
        ('split', 'Fission Split'),
        ('merge', 'Consolidation Merge')
    ], string='Transition Type', required=True, default='sequential', index=True)

    quantity_transferred = fields.Float(
        string='Quantity Transferred',
        default=0.0
    )
    timestamp = fields.Datetime(
        string='Execution Timestamp',
        default=fields.Datetime.now,
        required=True,
        index=True
    )
