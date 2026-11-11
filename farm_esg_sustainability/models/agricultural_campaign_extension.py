from odoo import models, fields, api

class AgriculturalCampaign(models.Model):
    _inherit = 'farm.agricultural.campaign'

    # Aggregate nutrient inputs of all tasks in this season
    task_ids = fields.One2many("project.task", "campaign_id", string="Tasks")
    total_n = fields.Float("Total Nitrogen (kg)", compute='_compute_campaign_nutrients', store=True, precompute=True)
    total_p = fields.Float("Total Phosphorus (kg)", compute='_compute_campaign_nutrients', store=True, precompute=True)
    total_k = fields.Float("Total Potassium (kg)", compute='_compute_campaign_nutrients', store=True, precompute=True)

    # Reduction comparison metrics [US-008-03]
    n_reduction_rate = fields.Float("N Reduction %", compute='_compute_reduction_rates')
    p_reduction_rate = fields.Float("P Reduction %", compute='_compute_reduction_rates')
    k_reduction_rate = fields.Float("K Reduction %", compute='_compute_reduction_rates')

    def _compute_reduction_rates(self):
        for campaign in self:
            # Find the previous season of the same family
            prev_campaign = self.search([
                ('date_start', '<', campaign.date_start or fields.Date.today()),
                ('id', '!=', campaign.id)
            ], order='date_start desc', limit=1)

            if prev_campaign and prev_campaign.total_n > 0:
                campaign.n_reduction_rate = ((prev_campaign.total_n - campaign.total_n) / prev_campaign.total_n) * 100
            else:
                campaign.n_reduction_rate = 0.0

            if prev_campaign and prev_campaign.total_p > 0:
                campaign.p_reduction_rate = ((prev_campaign.total_p - campaign.total_p) / prev_campaign.total_p) * 100
            else:
                campaign.p_reduction_rate = 0.0

            if prev_campaign and prev_campaign.total_k > 0:
                campaign.k_reduction_rate = ((prev_campaign.total_k - campaign.total_k) / prev_campaign.total_k) * 100
            else:
                campaign.k_reduction_rate = 0.0

    @api.depends('task_ids.total_n', 'task_ids.total_p', 'task_ids.total_k')
    def _compute_campaign_nutrients(self):
        for campaign in self:
            tasks = self.env['project.task'].search([('campaign_id', '=', campaign.id)])
            campaign.total_n = sum(tasks.mapped('total_n'))
            campaign.total_p = sum(tasks.mapped('total_p'))
            campaign.total_k = sum(tasks.mapped('total_k'))