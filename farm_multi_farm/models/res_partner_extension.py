from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    """
    Extend res.partner to support internal credit balances [US-078-04]
    """
    _inherit = 'res.partner'

    internal_credit_balance = fields.Float(
        'Internal Credit Balance',
        default=0.0,
        help='Internal credit balance for cooperative transactions'
    )