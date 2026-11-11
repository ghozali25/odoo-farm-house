from odoo import models, fields, api

class PosOrder(models.Model):
    _inherit = 'pos.order'

    # Link the picking parcel [US-002-02]
    picking_location_id = fields.Many2one(
        'stock.location', 
        string="Picking Source Plot",
        domain=[('is_land_parcel', '=', True)],
        help="The specific land parcel where these products were picked."
    )

    def _prepare_invoice_vals(self):
        vals = super()._prepare_invoice_vals()
        # Pass parcel info to the invoice
        return vals

class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    # Support line-level lot assignment
    lot_id = fields.Many2one('stock.lot', string="Production Lot")
