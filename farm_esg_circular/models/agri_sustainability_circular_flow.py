from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import drop_view_if_exists
import logging

_logger = logging.getLogger(__name__)


class AgriSustainabilityCircularFlow(models.Model):
    """
    Circular economy flow model - US-101-03: circular economy value assessment, US-100-04: defective-product recycling market
    Complements the existing carbon footprint model; focuses on resource recycling value
    """
    _name = 'agri.sustainability.circular.flow'
    _description = 'Agricultural Circular Flow'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char('Flow Name', required=True, copy=False)
    code = fields.Char('Flow Code', required=True, copy=False)
    flow_type = fields.Selection([
        ('waste_to_resource', 'Waste to Resource'),
        ('byproduct_to_sale', 'By-product to Sale'),
        ('recycling', 'Recycling'),
        ('energy_recovery', 'Energy Recovery'),
        ('composting', 'Composting'),
        ('biogas_production', 'Biogas Production')
    ], 'Flow Type', required=True, default='waste_to_resource')
    description = fields.Text('Flow Description')

    # Input/Output Products
    input_product_id = fields.Many2one('product.product', 'Input Product / Raw Material', required=True)
    output_product_id = fields.Many2one('product.product', 'Output Product / Resource', required=True)
    input_quantity = fields.Float('Input Quantity', required=True)
    output_quantity = fields.Float('Output Quantity', required=True)

    # Time Range
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    duration_days = fields.Integer('Duration (Days)', compute='_compute_duration', store=True, precompute=True)

    # Value Metrics
    economic_value = fields.Float('Economic Value', compute='_compute_economic_value', store=True, precompute=True)
    environmental_impact = fields.Float('Environmental Impact Score', compute='_compute_environmental_impact', store=True, precompute=True)
    social_impact = fields.Float('Social Impact Score', compute='_compute_social_impact', store=True, precompute=True)

    # Cost-Benefit
    processing_cost = fields.Float('Processing Cost')
    revenue = fields.Float('Revenue')
    net_benefit = fields.Float('Net Benefit', compute='_compute_net_benefit', store=True, precompute=True)

    # Status & Management
    status = fields.Selection([
        ('planned', 'Planned'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('suspended', 'Suspend'),
        ('cancelled', 'Cancelled')
    ], 'Status', default='planned', required=True)

    responsible_person_id = fields.Many2one('res.users', 'Responsible Person')
    department_id = fields.Many2one('hr.department', 'Responsible Department')

    # Business Links
    related_production_id = fields.Many2one('mrp.production', 'Related Manufacturing Order')
    related_sale_order_id = fields.Many2one('sale.order', 'Related Sales Order')
    # Integrate existing carbon footprint data

    # Link to geospatial network (US-057-06)
    geospatial_network_id = fields.Many2one('agri.geospatial.circular.network', string='Related Geospatial Network')

    # Link to regional governance (US-057-07)
    regional_governance_id = fields.Many2one('agri.regional.circular.governance', string='Related Regional Governance')

    # Link to farm participation (US-057-07)
    farm_participation_id = fields.Many2one('agri.farm.circular.participation', string='Related Farm Participation')

    # Record Information
    created_by = fields.Many2one('res.users', 'Created By', default=lambda self: self.env.user)
    create_date = fields.Datetime('Creation Date', readonly=True)
    write_date = fields.Datetime('Last Modified', readonly=True)

    @api.depends('start_date', 'end_date')
    def _compute_duration(self):
        """Compute Duration (Days)"""
        from datetime import date
        for flow in self:
            if flow.start_date and flow.end_date:
                duration = (flow.end_date - flow.start_date).days
                flow.duration_days = max(0, duration)  # Ensure non-negative
            else:
                flow.duration_days = 0

    @api.depends('processing_cost', 'revenue')
    def _compute_net_benefit(self):
        """Compute Net Benefit"""
        for flow in self:
            flow.net_benefit = flow.revenue - flow.processing_cost

    @api.depends('output_quantity', 'output_product_id')
    def _compute_economic_value(self):
        """Compute Economic Value"""
        for flow in self:
            if flow.output_product_id and flow.output_quantity:
                # Use the product's standard price as the basis
                price = flow.output_product_id.standard_price or flow.output_product_id.lst_price
                flow.economic_value = flow.output_quantity * price
            else:
                flow.economic_value = 0.0

    @api.depends('related_production_id', 'input_product_id', 'input_quantity')
    def _compute_environmental_impact(self):
        """[US-101-03] Mass_Balance Recursive Value Flow Algorithm"""
        # NOTE (port 19.0->18.0, batch 5): 'agri.sustainability.algorithms' is
        # defined in farm_esg_compliance (which depends on THIS module), so it
        # must not be a hard requirement here; likewise the product impact
        # fields live in farm_esg_compliance / farm_esg_carbon. Without them
        # the mass-balance branch is skipped and the simple-multiplier
        # fallback below applies.
        try:
            algo = self.env['agri.sustainability.algorithms']
        except KeyError:
            algo = None
        for flow in self:
            if flow.related_production_id and algo is not None:
                # Use Mass Balance Recursive Algorithm
                inputs = []
                for move in flow.related_production_id.move_raw_ids:
                    inputs.append({
                        'qty': move.product_uom_qty,
                        'env_score': getattr(move.product_id, 'environmental_impact', 50.0) or 50.0,
                        'soc_score': getattr(move.product_id, 'social_impact', 50.0) or 50.0,
                        'eco_score': getattr(move.product_id, 'economic_impact', 50.0) or 50.0,
                        'carbon': getattr(move.product_id, 'carbon_emission_factor', 0.0) or 0.0
                    })

                results = algo.calculate_recursive_mass_balance(inputs, flow.output_quantity)
                flow.environmental_impact = results.get('environmental_score', 50.0)
                flow.social_impact = results.get('social_score', 50.0)
                flow.economic_value = flow.output_quantity * (flow.output_product_id.standard_price or 1.0)
            else:
                # Fallback to simple multiplier logic
                base_score = 50.0
                type_multiplier = {'waste_to_resource': 1.2, 'biogas_production': 1.4}
                multiplier = type_multiplier.get(flow.flow_type, 1.0)
                flow.environmental_impact = min(100, base_score * multiplier)

    @api.depends('flow_type', 'output_quantity')
    def _compute_social_impact(self):
        """Compute Social Impact Score (0-100)"""
        for flow in self:
            base_score = 30  # Base score

            # Adjust score by flow type
            type_multiplier = {
                'waste_to_resource': 1.0,
                'byproduct_to_sale': 1.2,
                'recycling': 1.1,
                'composting': 0.9,
                'biogas_production': 1.3,
            }

            multiplier = type_multiplier.get(flow.flow_type, 1.0)

            flow.social_impact = min(100, base_score * multiplier)

    @api.constrains('input_quantity', 'output_quantity')
    def _check_positive_quantities(self):
        """Check quantities are positive"""
        for flow in self:
            if flow.input_quantity <= 0:
                raise ValidationError(_('Input quantity must be greater than 0'))
            if flow.output_quantity < 0:  # Output quantity may be 0 (fully converted)
                raise ValidationError(_('Output quantity must not be negative'))

    @api.constrains('start_date', 'end_date')
    def _check_date_range(self):
        """Check date range validity"""
        for flow in self:
            if flow.start_date and flow.end_date and flow.start_date > flow.end_date:
                raise ValidationError(_('Start date cannot be later than end date'))

    def action_activate_flow(self):
        """Activate Flow"""
        for flow in self:
            if flow.status == 'planned':
                flow.status = 'active'

    def action_complete_flow(self):
        """Complete Flow"""
        for flow in self:
            if flow.status in ['planned', 'active']:
                flow.status = 'completed'

    def action_suspend_flow(self):
        """Suspend Flow"""
        for flow in self:
            if flow.status in ['planned', 'active']:
                flow.status = 'suspended'

    @api.model
    @api.model_create_multi
    def create(self, vals_list):
        """Set defaults and business logic on create"""
        for vals in vals_list:
            if "code" not in vals or not vals['code']:
                # Try the new sequence first, fall back to the old one for compatibility
                new_sequence = self.env['ir.sequence'].next_by_code('agri.sustainability.circular.flow')
                if new_sequence:
                    vals['code'] = new_sequence
                else:
                    vals['code'] = self.env['ir.sequence'].next_by_code('farm.sustainability.circular.flow') or '/'

        record = super().create(vals_list)

        # Additional logic for linked production or sales orders can be added here
        return record

    def name_get(self):
        """Custom display name"""
        result = []
        for record in self:
            name = f"[{record.code}] {record.name}"
            result.append((record.id, name))
        return result


class AgriSustainabilityCircularFlowAnalysis(models.Model):
    """
    Circular economy flow analysis model - for generating analysis reports
    """
    _name = 'agri.sustainability.circular.flow.analysis'
    _description = 'Agricultural Circular Flow Analysis'
    _auto = False  # This is a view model; no physical table is created

    flow_id = fields.Many2one('agri.sustainability.circular.flow', 'Circular Economy Flow', readonly=True)
    flow_type = fields.Selection(related='flow_id.flow_type', string='Flow Type', readonly=True)
    input_product_id = fields.Many2one(related='flow_id.input_product_id', string='Input Product', readonly=True)
    output_product_id = fields.Many2one(related='flow_id.output_product_id', string='Output Product', readonly=True)
    economic_value = fields.Float(related='flow_id.economic_value', string='Economic Value', readonly=True)
    environmental_impact = fields.Float(related='flow_id.environmental_impact', string='Environmental Impact', readonly=True)
    net_benefit = fields.Float(related='flow_id.net_benefit', string='Net Benefit', readonly=True)
    status = fields.Selection(related='flow_id.status', string='Status', readonly=True)
    month = fields.Char('Month', readonly=True)
    year = fields.Char('Year', readonly=True)

    def init(self):
        """Initialize view"""
        drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    cf.id as id,
                    cf.id as flow_id,
                    cf.flow_type,
                    cf.input_product_id,
                    cf.output_product_id,
                    cf.economic_value,
                    cf.environmental_impact,
                    cf.net_benefit,
                    cf.status,
                    TO_CHAR(cf.create_date, 'YYYY-MM') as month,
                    TO_CHAR(cf.create_date, 'YYYY') as year
                FROM agri_sustainability_circular_flow cf
                WHERE cf.status = 'completed'
            )
        """ % self._table)