# -*- coding: utf-8 -*-
from odoo import models, fields, _
from odoo.exceptions import ValidationError


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    industry_type = fields.Selection(related="bom_id.industry_type", string="Industry Standard", store=True, readonly=True)

    # NOTE (18.0): the Odoo 19 compatibility shim lot_producing_id
    # (compute/inverse/search over lot_producing_ids) was removed.
    # Odoo 18 core mrp.production already provides lot_producing_id
    # as a plain Many2one; redefining it as computed would break core.
    # The ISL redirection (create/get_formview_action/write/unlink
    # guards, _trigger_isl_hook, action_view_isl_record) was removed
    # with farm_isl (not part of batch 1).

    def action_confirm(self):
        for order in self:
            if order.location_dest_id:
                # Resolve destination capacity constraints
                farm_loc = order.location_dest_id

                if getattr(farm_loc, 'max_stocking_density', 0.0) > 0.0:
                    # Calculate future density including pending production qty
                    existing_quants = self.env['stock.quant'].search([
                        ('location_id', '=', order.location_dest_id.id)
                    ])
                    current_qty = sum(existing_quants.mapped('quantity'))
                    future_qty = current_qty + order.product_qty

                    if getattr(farm_loc, 'land_area', 0.0) > 0.0:
                        future_density = future_qty / farm_loc.land_area
                        if future_density > farm_loc.max_stocking_density:
                            raise ValidationError(_(
                                "Backpressure Limit Reached: Confirming production of %.2f units would exceed "
                                "maximum stocking density (%.2f units/m²) of destination %s."
                            ) % (order.product_qty, farm_loc.max_stocking_density, farm_loc.name))

        return super(MrpProduction, self).action_confirm()
