from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class StockPickingType(models.Model):
    """
    Extend stock.picking.type to support"advance-funding distribution"type [US-078-04]
    """
    _inherit = 'stock.picking.type'

    is_advancing_distribution = fields.Boolean(
        'Is Advancing Distribution',
        default=False,
        help='Check if this operation type is for advancing distribution to members'
    )