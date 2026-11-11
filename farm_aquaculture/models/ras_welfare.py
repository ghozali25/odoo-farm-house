from odoo import models, fields, api, _

# NOTE (18.0 port, batch 3) — farm_iot pruning, correction of the
# handover note: this file does NOT reference farm_iot/iiot at all
# (verified by grep). Its only out-of-batch touchpoint is the
# farm_financial_valuation hook below, which is already guarded by
# hasattr() — 'asset_id' does not exist on agri.isl.ras.production,
# so the block is skipped; the test test_ras_welfare.py self-skips
# for the same reason. No code removed here.
# The message_post() call in the onchange below DID need a fix, but
# in ras_isl.py, not here: 'mail.thread' was added to
# agri.isl.ras.production (no model in its chain had it, and _inherits
# does not delegate methods), so an ammonia spike used to raise
# AttributeError.
class FarmRasProduction(models.Model):
    _inherit = 'agri.isl.ras.production'
    
    # [US-SCENARIO-30] RAS Water Quality & Fish Welfare
    lss_status = fields.Selection([('normal', 'Normal'), ('emergency', 'Emergency Mode')], default='normal')
    ammonia_level = fields.Float("Ammonia Level (ppm)")
    
    @api.onchange('ammonia_level')
    def _onchange_ammonia_trigger_lss(self):
        if self.ammonia_level > 2.0:
            self.lss_status = 'emergency'
            self.message_post(body=_("EMERGENCY LSS ENGAGED: Ammonia spiked to %s ppm!") % self.ammonia_level)
            
            # Auto-calculate mortality impact
            # farm_financial_valuation is NOT part of batch 3 (and
            # 'asset_id' does not exist on this model) — the hasattr()
            # guard below skips the whole block. Kept as upstream.
            if hasattr(self, 'asset_id') and self.asset_id:
                # 5% mortality drop
                self.asset_id.base_weight_kg *= 0.95
                if hasattr(self.asset_id, 'trigger_financial_revaluation'):
                    self.asset_id.trigger_financial_revaluation(reason="Ammonia Spike Mortality")

