from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    """
    Extend account.move to auto-deduct credit when a supplier bill is created [US-078-04]
    """
    _inherit = 'account.move'

    def action_post(self):
        """Override to handle credit deductions for vendor bills"""
        res = super().action_post()

        # Process only vendor bills
        for move in self:
            if move.move_type == 'in_invoice' and move.partner_id:
                # Calculate total bill amount
                total_amount = move.amount_total

                # Check if partner has sufficient internal credit balance
                partner = move.partner_id
                if partner.internal_credit_balance >= total_amount:
                    # Deduct the amount from internal credit balance
                    new_balance = partner.internal_credit_balance - total_amount
                    partner.internal_credit_balance = new_balance

                    # Add a message to the chatter
                    move.message_post(
                        body=f"Paid with internal credit: -{total_amount}，Remaining credit balance: {new_balance}"
                    )
                else:
                    # If insufficient credit, we might want to partially pay or raise an exception
                    # For now, we'll just log the situation
                    if partner.internal_credit_balance > 0:
                        remaining_amount = total_amount - partner.internal_credit_balance
                        move.message_post(
                            body=f"Partially paid with internal credit: -{partner.internal_credit_balance}，Remaining amount payable: {remaining_amount}"
                        )
                        partner.internal_credit_balance = 0.0

        return res