# -*- coding: utf-8 -*-
# [US-039-26] [LOSSLESS] Agricultural Menu & Action Interceptor
from odoo import models, fields, api, _

class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    def read(self, fields=None, load='_classic_read'):
        """Intercept menu reads and replace names in real time."""
        res = super(IrUiMenu, self).read(fields=fields, load=load)
        if not self.env.context.get('skip_agri_mapping'):
            TermMapping = self.env['term.mapping']
            industry = self.env.context.get('industry_context', 'general')
            for menu in res:
                if 'name' in menu:
                    menu['name'] = TermMapping.apply_term_mapping_to_text(menu['name'], industry_context=industry)
        return res

class IrActionsActWindow(models.Model):
    _inherit = 'ir.actions.act_window'

    def read(self, fields=None, load='_classic_read'):
        """Intercept action reads and replace titles in real time."""
        res = super(IrActionsActWindow, self).read(fields=fields, load=load)
        if not self.env.context.get('skip_agri_mapping'):
            TermMapping = self.env['term.mapping']
            industry = self.env.context.get('industry_context', 'general')
            for action in res:
                if 'name' in action:
                    action['name'] = TermMapping.apply_term_mapping_to_text(action['name'], industry_context=industry)
                if 'help' in action and isinstance(action['help'], str):
                    action['help'] = TermMapping.apply_term_mapping_to_text(action['help'], industry_context=industry)
        return res
