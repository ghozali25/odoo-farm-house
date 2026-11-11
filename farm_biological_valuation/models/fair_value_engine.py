# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class AgriFairValueMixin(models.AbstractModel):
    """
    [US-014-05] Biological Asset Fair Value Real-time Conversion Mixin
    Provides dynamic valuation logic for biological assets over their growth cycle.
    """
    _name = 'farm.biological.valuation.mixin'
    _description = 'Biological Asset Fair Value Real-time Conversion DNA'

    # 1. Core valuation indicators (KPIs)
    current_growth_progress = fields.Float("Growth Progress (%)", help="Current growth progress, calculated by the agronomic model")
    current_yield_potential = fields.Float("Estimated Yield (at maturity)", help="Forecast output at maturity")
    current_market_unit_price = fields.Float("Current Market Price (per Unit)", help="Current market fair unit price")

    fair_value = fields.Monetary("Fair Value (Real-time)", compute='_compute_fair_value', store=True, currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string="Currency", default=lambda self: self.env.company.currency_id)

    # 2. Status tracking
    last_valuation_date = fields.Datetime("Last Revaluation", default=fields.Datetime.now)
    valuation_method = fields.Selection([
        ('market_price', 'Market Price Method (Fair Value)'),
        ('cost_accumulation', 'Cost Accumulation')
    ], string="Valuation Method", default='market_price')

    @api.depends('current_growth_progress', 'current_yield_potential', 'current_market_unit_price')
    def _compute_fair_value(self):
        """
        Fair value formula:
        Fair Value = (Forecast Output * Market Unit Price) * Growth Progress Factor
        """
        for rec in self:
            if rec.valuation_method == 'market_price':
                # Core agronomic conversion algorithm
                rec.fair_value = (rec.current_yield_potential * rec.current_market_unit_price) * (rec.current_growth_progress / 100.0)
            else:
                # Cost method logic (submodules accumulate costs)
                rec.fair_value = rec._get_accumulated_costs()

    def _get_accumulated_costs(self):
        """ [Hook] Cost-method retrieval, implemented by the concrete business module """
        return 0.0

    def action_recalculate_fair_value(self):
        """
        [Process Engine] Actively trigger a revaluation and decide whether
        to generate an accounting entry based on volatility.
        """
        self.ensure_one()
        old_value = self.fair_value

        # 1. Trigger agronomic progress update (specific calculation implemented by submodules)
        self._update_biological_progress()

        # 2. Force the computation
        self._compute_fair_value()

        self.last_valuation_date = fields.Datetime.now()

        # 3. Audit and automatic reconciliation
        if old_value > 0 and abs(self.fair_value - old_value) / old_value > 0.05:
            self._on_fair_value_significant_change(old_value, self.fair_value)

        return True

    def _update_biological_progress(self):
        """ [Hook] Update biological growth progress, e.g. accumulated temperature (GDD) calculation, age increment """
        pass

    def _on_fair_value_significant_change(self, old_val, new_val):
        """ [Hook] Callback when the value moves by more than 5%, typically used to generate an accounting entry """
        self.message_post(body=_("SIGNIFICANT VALUE CHANGE: %s -> %s (Variance > 5%%)") % (old_val, new_val))

    @api.model
    def cron_recalculate_fair_values(self):
        """ Scheduled recalculation of fair values (see data/cron_fair_value.xml).

        No concrete model inherits this mixin yet, so there is nothing to
        recalculate; concrete models override this hook to recalculate their
        own records. Kept so the cron record stays valid if it is enabled.
        """
        _logger.info("Fair value recalculation: no concrete model uses farm.biological.valuation.mixin yet, nothing to do.")
        return True
