from odoo import models, fields, api, _
import logging
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class AgriSustainabilityDashboard(models.Model):
    """
    Sustainability dashboard model - US-101-01: triple bottom line metrics unified management
    Integrates with existing ESG dashboard features
    """
    _name = 'agri.sustainability.dashboard'
    _description = 'Agricultural Sustainability Dashboard'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Dashboard Name', required=True, default='Sustainability Overview Dashboard')
    description = fields.Text('Description')
    period_type = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly')
    ], 'Reporting Period', default='monthly', required=True)
    start_date = fields.Date('Start Date', required=True, default=fields.Date.today)
    end_date = fields.Date('End Date', required=True, default=lambda self: fields.Date.today())

    # Triple Bottom Line Metrics
    economic_score = fields.Float('Economic Score', compute='_compute_scores', store=True, precompute=True)
    environmental_score = fields.Float('Environmental Score', compute='_compute_scores', store=True, precompute=True)
    social_score = fields.Float('Social Score', compute='_compute_scores', store=True, precompute=True)
    overall_score = fields.Float('Overall Score', compute='_compute_scores', store=True, precompute=True)

    # Key Metrics
    total_circular_flows = fields.Integer('Circular Economy Flow Count', compute='_compute_kpis', store=True, precompute=True)
    total_circular_value = fields.Float('Total Circular Economy Value', compute='_compute_kpis', store=True, precompute=True)
    waste_reduced = fields.Float('Waste Reduced', compute='_compute_kpis', store=True, precompute=True)
    resource_saved = fields.Float('Resources Saved', compute='_compute_kpis', store=True, precompute=True)

    # Integrate existing carbon footprint data
    total_carbon_footprint = fields.Float('Total Carbon Footprint', compute='_compute_kpis', store=True, precompute=True)

    # Trend Metrics
    economic_trend = fields.Float('Economic Trend %', compute='_compute_trends', store=True, precompute=True)
    environmental_trend = fields.Float('Environmental Trend %', compute='_compute_trends', store=True, precompute=True)
    social_trend = fields.Float('Social Trend %', compute='_compute_trends', store=True, precompute=True)

    # Status
    is_active = fields.Boolean('Active', default=True)
    last_calculated = fields.Datetime('Last Calculated', readonly=True)

    @api.depends('start_date', 'end_date')
    def _compute_scores(self):
        """Compute triple bottom line scores"""
        for dashboard in self:
            # Fetch metric data for the period
            economic_metrics = self.env['agri.sustainability.metric'].search([
                ('category', '=', 'economic'),
                ('is_active', '=', True)
            ])

            environmental_metrics = self.env['agri.sustainability.metric'].search([
                ('category', '=', 'environmental'),
                ('is_active', '=', True)
            ])

            social_metrics = self.env['agri.sustainability.metric'].search([
                ('category', '=', 'social'),
                ('is_active', '=', True)
            ])

            # Compute per-dimension scores (simple average achievement rate)
            economic_score = sum(m.progress_rate for m in economic_metrics) / len(economic_metrics) if economic_metrics else 0
            environmental_score = sum(m.progress_rate for m in environmental_metrics) / len(environmental_metrics) if environmental_metrics else 0
            social_score = sum(m.progress_rate for m in social_metrics) / len(social_metrics) if social_metrics else 0

            dashboard.economic_score = economic_score
            dashboard.environmental_score = environmental_score
            dashboard.social_score = social_score
            dashboard.overall_score = (economic_score + environmental_score + social_score) / 3 if (economic_score + environmental_score + social_score) > 0 else 0

    @api.depends('start_date', 'end_date')
    def _compute_kpis(self):
        """Compute Key Metrics"""
        for dashboard in self:
            # Count circular economy flows
            circular_flows = self.env['agri.sustainability.circular.flow'].search([
                ('start_date', '>=', dashboard.start_date),
                ('end_date', '<=', dashboard.end_date),
                ('status', '=', 'completed')
            ])

            dashboard.total_circular_flows = len(circular_flows)
            dashboard.total_circular_value = sum(f.economic_value for f in circular_flows)

            # Waste-reduction and resource-saving logic can be added here
            dashboard.waste_reduced = sum(f.input_quantity for f in circular_flows if f.flow_type in ['waste_to_resource', 'recycling'])
            dashboard.resource_saved = sum(f.output_quantity for f in circular_flows if f.flow_type in ['waste_to_resource', 'recycling'])

            # Integrate carbon footprint data
# NOTE (port 19.0->18.0, batch 5): 'agri.sustainability.carbon.footprint.calculation' is not defined anywhere in the odoo-farm repo (phantom
        # upstream reference); guard so the dashboard/report degrades to 0.0.
            try:
                carbon_calculations = self.env['agri.sustainability.carbon.footprint.calculation'].search([
                    ('calculation_date', '>=', dashboard.start_date),
                    ('calculation_date', '<=', dashboard.end_date)
                ])
            except KeyError:
                carbon_calculations = []
            dashboard.total_carbon_footprint = sum(c.total_carbon_footprint for c in carbon_calculations)

    @api.depends('start_date', 'end_date')
    def _compute_trends(self):
        """Compute trends"""
        for dashboard in self:
            # Fetch previous-period data for comparison
            period_delta = {
                'daily': relativedelta(days=1),
                'weekly': relativedelta(weeks=1),
                'monthly': relativedelta(months=1),
                'quarterly': relativedelta(months=3),
                'yearly': relativedelta(years=1)
            }[dashboard.period_type]

            prev_start = dashboard.start_date - period_delta
            prev_end = dashboard.end_date - period_delta

            # Compute previous scores for trend analysis
            prev_economic_score = self._calculate_period_score('economic', prev_start, prev_end)
            curr_economic_score = self._calculate_period_score('economic', dashboard.start_date, dashboard.end_date)

            prev_environmental_score = self._calculate_period_score('environmental', prev_start, prev_end)
            curr_environmental_score = self._calculate_period_score('environmental', dashboard.start_date, dashboard.end_date)

            prev_social_score = self._calculate_period_score('social', prev_start, prev_end)
            curr_social_score = self._calculate_period_score('social', dashboard.start_date, dashboard.end_date)

            # Compute trendsPercent
            dashboard.economic_trend = self._calculate_trend(prev_economic_score, curr_economic_score)
            dashboard.environmental_trend = self._calculate_trend(prev_environmental_score, curr_environmental_score)
            dashboard.social_trend = self._calculate_trend(prev_social_score, curr_social_score)

    def _calculate_period_score(self, category, start_date, end_date):
        """Compute score for a given period and category"""
        metrics = self.env['agri.sustainability.metric'].search([
            ('category', '=', category),
            ('is_active', '=', True)
        ])
        if not metrics:
            return 0.0

        # Simplified score computation; real use may need in-period values
        return sum(m.progress_rate for m in metrics) / len(metrics)

    def _calculate_trend(self, previous, current):
        """Compute trendsPercent"""
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        return ((current - previous) / previous) * 100.0

    def action_calculate_dashboard(self):
        """Manually recalculate dashboard data"""
        for dashboard in self:
            # Trigger recomputation of stored fields
            dashboard.invalidate_recordset()
            dashboard._compute_scores()
            dashboard._compute_kpis()
            dashboard._compute_trends()
            dashboard.last_calculated = fields.Datetime.now()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Calculation Complete'),
                'message': _('Sustainability dashboard data has been recalculated'),
                'type': 'success'
            }
        }

    def action_view_economic_metrics(self):
        """View Economic Metrics"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Economic Metrics'),
            'res_model': 'agri.sustainability.metric',
            'view_mode': 'list,form',
            'domain': [('category', '=', 'economic')],
            'context': self.env.context
        }

    def action_view_environmental_metrics(self):
        """View Environmental Metrics"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Environmental Metrics'),
            'res_model': 'agri.sustainability.metric',
            'view_mode': 'list,form',
            'domain': [('category', '=', 'environmental')],
            'context': self.env.context
        }

    def action_view_social_metrics(self):
        """View Social Metrics"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Social Metrics'),
            'res_model': 'agri.sustainability.metric',
            'view_mode': 'list,form',
            'domain': [('category', '=', 'social')],
            'context': self.env.context
        }

    def action_view_circular_flows(self):
        """View Circular Economy Flows"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Circular Economy Flows'),
            'res_model': 'agri.sustainability.circular.flow',
            'view_mode': 'list,form',
            'domain': [('status', '=', 'completed')],
            'context': self.env.context
        }

    def action_view_carbon_footprints(self):
        """View Carbon Footprint Data"""
        # NOTE (port 19.0->18.0, batch 5): 'agri.sustainability.carbon.footprint
        # .calculation' is not defined anywhere in the odoo-farm repo (phantom
        # upstream reference); show a warning instead of opening a dead action.
        try:
            self.env['agri.sustainability.carbon.footprint.calculation']
        except KeyError:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Carbon Footprint Data Unavailable'),
                    'message': _('Carbon footprint calculations are not available (model not installed).'),
                    'type': 'warning',
                }
            }
        return {
            'type': 'ir.actions.act_window',
            'name': _('Carbon Footprint Data'),
            'res_model': 'agri.sustainability.carbon.footprint.calculation',
            'view_mode': 'list,form',
            'context': self.env.context
        }


class AgriSustainabilityReport(models.Model):
    """
    Sustainability report model - for periodic reports
    Integrates existing ESG reporting
    """
    _name = 'agri.sustainability.report'
    _description = 'Agricultural Sustainability Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'report_date desc'

    name = fields.Char('Report Name', required=True)
    report_date = fields.Date('Report Date', required=True, default=fields.Date.today)
    period_start = fields.Date('Period Start', required=True)
    period_end = fields.Date('Period End', required=True)

    # Report Content
    executive_summary = fields.Html('Executive Summary')
    economic_analysis = fields.Html('Economic Analysis')
    environmental_analysis = fields.Html('Environmental Analysis')
    social_analysis = fields.Html('Social Analysis')

    # Quantified Data
    economic_score = fields.Float('Economic Score')
    environmental_score = fields.Float('Environmental Score')
    social_score = fields.Float('Social Score')
    overall_score = fields.Float('Overall Score')

    # Integrate carbon footprint data
    total_carbon_footprint = fields.Float('Total Carbon Footprint')

    # Circular Economy Results
    circular_flows_count = fields.Integer('Circular Economy Flow Count')
    circular_value_created = fields.Float('Circular Economy Value Created')
    waste_diverted = fields.Float('Waste Diverted')
    resource_efficiency_improvement = fields.Float('Resource Efficiency Improvement %')

    # Status Management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('published', 'Published')
    ], 'Status', default='draft')

    author_id = fields.Many2one('res.users', 'Author', default=lambda self: self.env.user)
    reviewer_id = fields.Many2one('res.users', 'Reviewer')
    approved_by = fields.Many2one('res.users', 'Approver')
    approval_date = fields.Datetime('Approval Date')

    # Appendices & Attachments
    report_attachment_ids = fields.Many2many('ir.attachment', string='Related Attachments')

    @api.model
    def create_report(self, period_start, period_end):
        """Auto-generate sustainability report"""
        # Compute per-dimension scores
        economic_metrics = self.env['agri.sustainability.metric'].search([('category', '=', 'economic'), ('is_active', '=', True)])
        environmental_metrics = self.env['agri.sustainability.metric'].search([('category', '=', 'environmental'), ('is_active', '=', True)])
        social_metrics = self.env['agri.sustainability.metric'].search([('category', '=', 'social'), ('is_active', '=', True)])

        economic_score = sum(m.progress_rate for m in economic_metrics) / len(economic_metrics) if economic_metrics else 0
        environmental_score = sum(m.progress_rate for m in environmental_metrics) / len(environmental_metrics) if environmental_metrics else 0
        social_score = sum(m.progress_rate for m in social_metrics) / len(social_metrics) if social_metrics else 0

        # Aggregate carbon footprint data
# NOTE (port 19.0->18.0, batch 5): 'agri.sustainability.carbon.footprint.calculation' is not defined anywhere in the odoo-farm repo (phantom
        # upstream reference); guard so the dashboard/report degrades to 0.0.
        try:
            carbon_calculations = self.env['agri.sustainability.carbon.footprint.calculation'].search([
                ('calculation_date', '>=', period_start),
                ('calculation_date', '<=', period_end)
            ])
        except KeyError:
            carbon_calculations = []
        total_carbon_footprint = sum(c.total_carbon_footprint for c in carbon_calculations)

        # Aggregate circular economy data
        circular_flows = self.env['agri.sustainability.circular.flow'].search([
            ('start_date', '>=', period_start),
            ('end_date', '<=', period_end),
            ('status', '=', 'completed')
        ])

        # Create report record
        report = self.create({
            'name': f'Sustainability Report {period_start.strftime("%Y-%m-%d")} to {period_end.strftime("%Y-%m-%d")}',
            'report_date': fields.Date.today(),
            'period_start': period_start,
            'period_end': period_end,
            'economic_score': economic_score,
            'environmental_score': environmental_score,
            'social_score': social_score,
            'overall_score': (economic_score + environmental_score + social_score) / 3,
            'total_carbon_footprint': total_carbon_footprint,
            'circular_flows_count': len(circular_flows),
            'circular_value_created': sum(f.economic_value for f in circular_flows),
            'waste_diverted': sum(f.input_quantity for f in circular_flows if f.flow_type in ['waste_to_resource', 'recycling']),
            'executive_summary': self._generate_executive_summary(economic_score, environmental_score, social_score, total_carbon_footprint),
            'economic_analysis': self._generate_economic_analysis(circular_flows),
            'environmental_analysis': self._generate_environmental_analysis(circular_flows, total_carbon_footprint),
            'social_analysis': self._generate_social_analysis()
        })

        return report

    def _generate_executive_summary(self, economic_score, environmental_score, social_score, total_carbon_footprint):
        """Generate executive summary"""
        return f"""
        <p>This period the company made significant sustainability progress:</p>
        <ul>
            <li>Economic score: {economic_score:.2f}%</li>
            <li>Environmental score: {environmental_score:.2f}%</li>
            <li>Social score: {social_score:.2f}%</li>
            <li>Overall score: {(economic_score + environmental_score + social_score) / 3:.2f}%</li>
            <li>Total carbon footprint: {total_carbon_footprint:.2f} kg CO2e</li>
        </ul>
        <p>The company performed strongly in the circular economy, achieving effective resource use and value creation.</p>
        """

    def _generate_economic_analysis(self, circular_flows):
        """Generate economic analysis"""
        total_value = sum(f.economic_value for f in circular_flows)
        return f"""
        <p>Economic analysis:</p>
        <ul>
            <li>Completed {len(circular_flows)} circular economy flows</li>
            <li>Total economic value created: {total_value:,.2f}</li>
            <li>Average value created per flow: {total_value/len(circular_flows) if circular_flows else 0:,.2f}</li>
        </ul>
        """

    def _generate_environmental_analysis(self, circular_flows, total_carbon_footprint):
        """Generate environmental analysis"""
        waste_reduced = sum(f.input_quantity for f in circular_flows if f.flow_type in ['waste_to_resource', 'recycling'])
        return f"""
        <p>Environmental analysis:</p>
        <ul>
            <li>Waste reduced through the circular economy: {waste_reduced:,.2f} units</li>
            <li>Implemented {len(circular_flows)} resource-recycling flows</li>
            <li>Total carbon footprint: {total_carbon_footprint:.2f} kg CO2e</li>
            <li>Reduced environmental load and improved resource efficiency</li>
        </ul>
        """

    def _generate_social_analysis(self):
        """Generate social analysis"""
        return """
        <p>Social analysis:</p>
        <ul>
            <li>Sustainability practices improved the company social image</li>
            <li>Created jobs and economic value for the local community</li>
            <li>Set an example for sustainable development in the industry</li>
        </ul>
        """

    def action_confirm(self):
        """Confirm Report"""
        self.write({
            'state': 'confirmed',
            'reviewer_id': self.env.user.id
        })

    def action_approve(self):
        """Approve Report"""
        self.write({
            'state': 'published',
            'approved_by': self.env.user.id,
            'approval_date': fields.Datetime.now()
        })

    def action_print_report(self):
        """Print Report"""
        return self.env.ref('farm_sustainability.action_sustainability_report').report_action(self)