from odoo import models, fields, api

class AgriQualityCheck(models.Model):
    _inherit = 'agri.quality.check'

    def action_trigger_recall(self):
        """ Creates a recall simulation from a failed QC """
        self.ensure_one()
        # farm.supply.recall lives in farm_supply, which is not part of
        # batch 1: fail with a clear message instead of a registry error.
        if 'farm.supply.recall' not in self.env:
            raise UserError(_(
                "Emergency recall is unavailable: the farm.supply.recall "
                "model (farm_supply module) is not installed."))
        recall = self.env['farm.supply.recall'].create({
            'triggering_qc_id': self.id
        })
        return {
            'name': 'Emergency Recall',
            'view_mode': 'form',
            'res_model': 'farm.supply.recall',
            'res_id': recall.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }
