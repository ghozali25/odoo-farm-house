from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class ProjectTask(models.Model):
    _inherit = 'project.task'
    _description = 'Multi-Industry Activity Production'

    # Industry type to support multi-industry operations
    industry_type = fields.Selection([
        ('field_crops', 'Field Crops'),
        ('protected_cultivation', 'Protected Cultivation'),
        ('orchard_horticulture', 'Orchard Horticulture'),
        ('livestock', 'Livestock'),
        ('aquaculture', 'Aquaculture'),
        ('medicinal_plants', 'Medicinal Plants'),
        ('mushroom', 'Mushroom Cultivation'),
        ('apiculture', 'Apiculture'),
        ('agricultural_processing', 'Agricultural Processing'),
        ('agritourism', 'Agritourism'),
        ('mixed', 'Mixed Operations'),
    ], string='Industry Type',
       help='Type of agricultural industry this task belongs to',
       default='field_crops')

    campaign_id = fields.Many2one(
        'farm.agricultural.campaign',
        string="Campaign/Season",
        help="Link this production task to a specific season."
    )

    # Inherits farm_core asset logic
    land_parcel_id = fields.Many2one('farm.location', string="Land Parcel/Pond", domain=[('is_land_parcel', '=', True)])
    gps_lat = fields.Float(related='land_parcel_id.gps_lat', store=True)
    gps_lng = fields.Float(related='land_parcel_id.gps_lng', store=True)

    # Weather Forecast [US-Weather]
    # forecast_ids = fields.Many2many(
        # 'agri.weather.forecast',
        # compute='_compute_weather_forecasts',
        # string="Weather Forecasts"

    def _compute_weather_forecasts(self):
        for task in self:
            if task.planned_date_begin and task.land_parcel_id:
                # Find forecasts for the planned period
                # task.forecast_ids = self.env[('id', '=', 0)].search([
                    ('location_id', '=', task.land_parcel_id.id),
                    ('date', '>=', task.planned_date_begin),
                    ('date', '<=', task.date_deadline or task.planned_date_begin)
                
            else:
                task.forecast_ids = False

    biological_lot_id = fields.Many2one('stock.lot', string="Biological Asset/Lot", domain="[('is_animal', '=', True)]")

    # Ekylibre Mapping: ActivityProduction [US-Mapping]
    support_id = fields.Many2one('product.product', string="Support Object", help="The land parcel, animal or group this task is performed on.")
    size_value = fields.Float("Production Size", help="Area in hectares (or sqm) or quantity of individuals.")

    # Demand-driven link [US-003-01]
    sale_order_id = fields.Many2one('sale.order', string="Source Sale Order")

    intervention_ids = fields.One2many(
        'mrp.production',
        'agri_task_id',
        string="Agri Interventions"
    )

    # Nutrient totals [US-001-03]
    total_n = fields.Float("Total Nitrogen (kg)", compute='_compute_nutrients', store=True, precompute=True)
    total_p = fields.Float("Total Phosphorus (kg)", compute='_compute_nutrients', store=True, precompute=True)
    total_k = fields.Float("Total Potassium (kg)", compute='_compute_nutrients', store=True, precompute=True)

    # Nutrient density (kg/ha) [US-001-03 Algorithm]
    n_density = fields.Float("N Density (kg/ha)", compute='_compute_agri_math')
    p_density = fields.Float("P Density (kg/ha)", compute='_compute_agri_math')
    k_density = fields.Float("K Density (kg/ha)", compute='_compute_agri_math')

    # Safe-harvest check [US-031-03 Algorithm]
    is_safe_to_harvest = fields.Boolean("Safe to Harvest", compute='_compute_agri_math')
    days_to_safety = fields.Integer("Days to Safety", compute='_compute_agri_math')

    def _compute_agri_math(self):
        for task in self:
            # 1. Nutrient density calculation
            area = task.size_value or task.land_parcel_id.land_area or 1.0
            task.n_density = task.total_n / area
            task.p_density = task.total_p / area
            task.k_density = task.total_k / area

            # 2. Safety check
            today = fields.Datetime.now()
            lot = task.biological_lot_id
            if lot and hasattr(lot, 'withdrawal_end_datetime') and lot.withdrawal_end_datetime:
                if lot.withdrawal_end_datetime > today:
                    task.is_safe_to_harvest = False
                    task.days_to_safety = (lot.withdrawal_end_datetime - today).days + 1
                else:
                    task.is_safe_to_harvest = True
                    task.days_to_safety = 0
            else:
                task.is_safe_to_harvest = True
                task.days_to_safety = 0

    def action_view_telemetry(self):
        """Open the telemetry trend chart linked to this task [US-031-03].
        Requires the farm_iot module (batch 2); without it the action is
        unavailable instead of crashing on the missing xml id."""
        self.ensure_one()
        try:
            action = self.env["ir.actions.actions"]._for_xml_id("farm_iot.action_farm_telemetry")
        except ValueError:
            raise UserError(_(
                "IoT telemetry is not available: the farm_iot module is not "
                "installed. Install it to view sensor trends for this task."
            ))
        action['domain'] = [('production_id', '=', self.id)]
        action['context'] = {
            'default_production_id': self.id,
            'default_land_parcel_id': self.land_parcel_id.id,
            'group_by': 'timestamp:hour'
        }
        return action

    @api.depends('intervention_ids.state', 'intervention_ids.move_raw_ids.product_uom_qty')
    def _compute_nutrients(self):
        for task in self:
            n = p = k = 0.0
            # Only count fertilizing interventions that are done or confirmed
            fertilizing_ops = task.intervention_ids.filtered(lambda i: i.intervention_type == 'fertilizing' and i.state != 'cancel')
            for op in fertilizing_ops:
                for move in op.move_raw_ids:
                    n += (move.product_uom_qty * (move.product_id.n_content / 100.0))
                    p += (move.product_uom_qty * (move.product_id.p_content / 100.0))
                    k += (move.product_uom_qty * (move.product_id.k_content / 100.0))
            task.total_n = n
            task.total_p = p
            task.total_k = k

    def _update_nutrient_balance(self):
        """Manual trigger, callable from tests or specific flows."""
        self._compute_nutrients()

    @api.model
    def cron_generate_feeding_proposals(self):
        """Daily scheduled job: generate suggested feeding interventions
        for aquaculture [US-001-03 Algorithm].
        NOTE (porting): the task state search below uses 'inprogress', which
        is not a project.task state code in Odoo 18 ('01_in_progress' is);
        upstream bug, left as-is — this cron is not registered in data."""
        # Find active aquaculture tasks
        tasks = self.search([
            ('project_id.activity_family', 'in', ['livestock', 'aquaculture']),
            ('state', '=', 'inprogress'), # assumed state
            ('biological_lot_id', '!=', False)
        ])

        for task in tasks:
            lot = task.biological_lot_id
            product = lot.product_id

            # Compute age
            if lot.born_at:
                age = (fields.Datetime.now() - lot.born_at).days
                # Get expected weight and feeding rate from the growth curve
                expected_weight = product.get_expected_weight(age)
                # Find the matching growth-curve line to get the feeding rate
                curve_line = product.growth_curve_ids.filtered(lambda c: c.age_days <= age).sorted('age_days', reverse=True)
                feed_rate = curve_line[0].daily_feed_rate if curve_line else 0.0

                if feed_rate > 0:
                    # Suggested feed qty = estimated biomass = count * avg weight
                    estimated_biomass = lot.animal_count * expected_weight
                    suggested_feed_qty = estimated_biomass * (feed_rate / 100.0)

                    # Send the suggestion or create a draft MO
                    task.message_post(body=_("DAILY FEED PROPOSAL: Age %s days. Estimated Biomass: %s kg. Suggested Feed: %s kg.") % (
                        age, estimated_biomass, suggested_feed_qty
                    ))

    # Required Qualifications for Task [US-040-08]

    @api.constrains('land_parcel_id', 'industry_type')
    def _check_land_use_restriction(self):
        """US-041-01: Hard-block non-crop tasks on protected farmland.
        (Upstream wording referenced a China-specific farmland class; the
        rule is kept generic here — the land_nature code value itself lives
        in farm_core and is unchanged.)"""
        for task in self:
            if task.land_parcel_id.land_nature == 'basic_farmland':
                if task.industry_type not in ['field_crops', 'mixed']:
                    raise ValidationError(_(
                        "LAND-USE RESTRICTION: Land parcel '%s' is designated as "
                        "protected farmland. Non-crop production activities "
                        "(such as tourism or livestock) are not permitted on "
                        "protected farmland."
                    ) % task.land_parcel_id.name)


    @api.onchange('industry_type')
    def _onchange_industry_type(self):
        """When industry type changes, update task fields and behaviors"""
        if self.industry_type:
            # Update project or task based on industry type
            industry_project_mapping = {
                'field_crops': 'Field Crops Operations',
                'protected_cultivation': 'Protected Cultivation Operations',
                'orchard_horticulture': 'Orchard Operations',
                'livestock': 'Livestock Operations',
                'aquaculture': 'Aquaculture Operations',
                'medicinal_plants': 'Medicinal Plants Operations',
                'mushroom': 'Mushroom Operations',
                'apiculture': 'Apiculture Operations',
                'agricultural_processing': 'Processing Operations',
                'agritourism': 'Agritourism Operations',
            }

            # Update or create project if needed
            if self.industry_type in industry_project_mapping:
                project_name = industry_project_mapping[self.industry_type]
                project = self.env['project.project'].search([('name', '=', project_name)], limit=1)
                if project:
                    self.project_id = project.id


