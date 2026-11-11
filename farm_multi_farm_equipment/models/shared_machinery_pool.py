from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class SharedMachineryPool(models.Model):
    """
    Shared machinery pool [US-042-08]
    """
    _name = 'shared.machinery.pool'
    _description = 'Shared Machinery Pool'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Machinery Name', required=True)
    code = fields.Char('Machinery Code', required=True, copy=False)
    cooperative_id = fields.Many2one('cooperative.entity', string='Cooperative', required=True)
    owner_member_id = fields.Many2one('cooperative.member', string='Owner Member', required=True)
    equipment_id = fields.Many2one('fleet.vehicle', string='Equipment', required=True)
    hourly_rate = fields.Float('Hourly Rate')
    daily_rate = fields.Float('Daily Rate')
    availability_status = fields.Selection([
        ('available', 'Available'),
        ('in_use', 'In Use'),
        ('maintenance', 'Under Maintenance'),
        ('out_of_service', 'Out of Service'),
    ], string='Availability Status', default='available', required=True)
    location = fields.Char('Current Location')
    description = fields.Text('Description')
    is_active = fields.Boolean('Is Active', default=True)

    @api.model
    def create(self, vals):
        if 'code' not in vals or not vals['code']:
            vals['code'] = self.env['ir.sequence'].next_by_code('shared.machinery.pool') or '/'
        return super().create(vals)

    def action_set_available(self):
        """Set to available"""
        self.availability_status = 'available'

    def action_set_in_use(self):
        """Set to in use"""
        self.availability_status = 'in_use'

    def action_set_maintenance(self):
        """Set to under maintenance"""
        self.availability_status = 'maintenance'

    def action_set_out_of_service(self):
        """Set to deactivated"""
        self.availability_status = 'out_of_service'