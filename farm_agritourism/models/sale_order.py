from odoo import models, fields, api, _


class ProjectTask(models.Model):
    _inherit = 'project.task'

    # Port fix (batch 7): upstream sale.order.agri_task_ids is a One2many
    # on project.task with inverse 'sale_order_id', and action_confirm
    # creates tasks with 'sale_order_id' — but Odoo 18 core project.task
    # has NO such field (only sale_line_id). Registry setup then fails
    # with KeyError: 'sale_order_id' on any full -u rebuild (proven in
    # the farm_core .0.4 upgrade run), even though a plain server start
    # happened to load. Define the inverse here.
    sale_order_id = fields.Many2one(
        'sale.order', string='Sale Order', ondelete='set null', index=True,
        help='Sale order that auto-generated this farm task.')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    agri_task_ids = fields.One2many('project.task', 'sale_order_id', string="Farm Tasks")
    booking_ids = fields.One2many('farm.booking', 'sale_order_id', string="Farm Bookings")
    booking_count = fields.Integer(compute='_compute_booking_count')

    @api.depends('booking_ids')
    def _compute_booking_count(self):
        for order in self:
            order.booking_count = len(order.booking_ids)

    def action_confirm(self):
        # US-009-01: Lead-time check
        today = fields.Date.today()
        for order in self:
            for line in order.order_line:
                if line.product_id.growth_duration > 0:
                    # Check whether the promised delivery date leaves enough time
                    delivery_date = order.commitment_date or order.expected_date
                    if delivery_date:
                        days_to_delivery = (fields.Date.to_date(delivery_date) - today).days
                        if days_to_delivery < line.product_id.growth_duration:
                            # Show a warning message
                            # Here we log to the chatter and raise a UserError to keep the production plan feasible
                            from odoo.exceptions import UserError
                            raise UserError(_("LEAD-TIME WARNING: Crop '%s' requires %s days to grow, but delivery is requested in %s days!") % (
                                line.product_id.name, line.product_id.growth_duration, days_to_delivery
                            ))

        res = super(SaleOrder, self).action_confirm()
        for order in self:
            for line in order.order_line:
                # 1. 1. Demand-driven production tasks [US-003-01]
                if line.product_id.is_variety:
                    self.env['project.task'].create({
                        'name': _('Demand: %s for %s') % (line.product_id.name, order.name),
                        'project_id': self.env['project.project'].search([('activity_family', '=', 'planting')], limit=1).id,
                        'description': _('Auto-generated from Sale Order %s. Quantity: %s') % (order.name, line.product_uom_qty),
                        'sale_order_id': order.id,
                    })
                
                # 2. 2. Auto-book the experience activity [US-002-04]
                if line.product_id.is_experience_package:
                    self.env['farm.booking'].create({
                        'name': _('Booking for %s') % order.name,
                        'partner_id': order.partner_id.id,
                        'booking_date': fields.Date.today(),
                        'sale_order_id': order.id,
                        'booking_type': 'visit',
                    })
        return res

    def action_view_bookings(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("farm_agritourism.action_farm_booking")
        action['domain'] = [('sale_order_id', '=', self.id)]
        action['context'] = {'default_sale_order_id': self.id, 'default_partner_id': self.partner_id.id}
        return action

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_experience_package = fields.Boolean("Is Experience Package", default=False, help="Products like 'Family Day Package' which include bookings.")

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    lot_id = fields.Many2one(
        'stock.lot', 
        string="Production Lot",
        domain="[('product_id', '=', product_id)]"
    )