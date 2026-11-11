# -*- coding: utf-8 -*-
"""Extend ``cooperative.member`` with the financial links (batch 6).

NOTE (port 19.0 -> 18.0, batch 6): upstream ``farm_multi_farm``
deliberately left these One2many fields commented out in
``extension_models.py`` ("moved to downstream modules to avoid circular
dependency") — but the downstream module ``farm_multi_farm_financial``
never defined them, while its ``member_share_views.xml`` form for
``cooperative.member`` shows them as stat buttons
(``share_transaction_ids`` / ``dividend_line_ids``) with
``action_view_share_transactions`` / ``action_view_dividends`` buttons.
Without this file the view fails validation at install
("action_view_share_transactions is not a valid action on
cooperative.member"). The fields + methods are defined here, in the
downstream module, as the upstream comment intended.
"""
from odoo import models, fields, _


class CooperativeMemberFinancialExtension(models.Model):
    _inherit = 'cooperative.member'

    share_transaction_ids = fields.One2many(
        'share.transaction', 'member_id', string="Share Transactions")
    dividend_line_ids = fields.One2many(
        'dividend.line', 'member_id', string="Dividend Lines")
    credit_transaction_ids = fields.One2many(
        'credit.transaction', 'member_id', string="Credit Transactions")

    def action_view_share_transactions(self):
        self.ensure_one()
        return {
            'name': _('Share Transactions'),
            'type': 'ir.actions.act_window',
            'res_model': 'share.transaction',
            'view_mode': 'list,form',
            'domain': [('member_id', '=', self.id)],
            'context': self.env.context,
        }

    def action_view_dividends(self):
        self.ensure_one()
        return {
            'name': _('Dividends'),
            'type': 'ir.actions.act_window',
            'res_model': 'dividend.line',
            'view_mode': 'list,form',
            'domain': [('member_id', '=', self.id)],
            'context': self.env.context,
        }
