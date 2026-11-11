# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging
import json

_logger = logging.getLogger(__name__)

class FarmAquacultureRecipe(models.Model):
    """
    Aquaculture Stocking Recipe (ISL Layer) [De-industrialized]
    """
    _name = 'agri.isl.aquaculture.recipe'
    _description = 'Aquaculture Stocking Recipe'
    _inherits = {'mrp.bom': 'recipe_id'}
    _inherit = ['agri.bom.mixin']

    recipe_id = fields.Many2one('mrp.bom', string='Base Recipe', required=True, ondelete='cascade')

    # Environment Setpoints [US-109-02]
    min_dissolved_oxygen = fields.Float("Min Dissolved Oxygen (mg/L)", default=4.0)
    optimal_temp_range = fields.Char("Optimal Temp Range (℃)")
    max_stocking_density = fields.Float("Max Density (kg/m³)")

class FarmLotAquaculture(models.Model):
    """
    Aquaculture Asset Batch (ISL Layer) [De-industrialized]
    """
    _name = 'agri.isl.lot.aquaculture'
    _description = 'Aquaculture Asset Batch'
    _inherits = {'stock.lot': 'lot_id'}
    _inherit = ['agri.biological.inventory.mixin', 'agri.geospatial.mixin']

    lot_id = fields.Many2one('stock.lot', string='Base Lot', required=True, ondelete='cascade')

    # Water Body Metrics [US-109-01]
    water_volume_m3 = fields.Float("Water Volume (m³)", default=1000.0)
    current_density = fields.Float("Current Density (kg/m³)", compute='_compute_aquaculture_kpi')

    @api.depends('total_biomass', 'water_volume_m3')
    def _compute_aquaculture_kpi(self):
        for rec in self:
            rec.current_density = rec.total_biomass / rec.water_volume_m3 if rec.water_volume_m3 > 0 else 0.0

class FarmAquacultureTask(models.Model):
    """
    Aquaculture Growth Task (ISL Layer) [De-industrialized]
    """
    _name = 'agri.isl.aquaculture.task'
    _description = 'Aquaculture Growth Task'
    _inherits = {'mrp.production': 'intervention_id'}
    _inherit = [
        'agri.intervention.mixin',
        'agri.agent.instruction.mixin',
        'agri.incident.alert.mixin',
        'agri.odoo19.performance.security.mixin',
        # NOTE (18.0 port, batch 3, fix B13): 'mail.thread' added —
        # report_incident() (agri.incident.alert.mixin) creates a
        # mail.activity, and mail.activity.create() calls
        # message_subscribe() on the target record. Without
        # mail.thread this model had no such method
        # (AttributeError on every low-DO telemetry call), because
        # _inherits = {'mrp.production': ...} delegates fields,
        # not methods. Same convention as agri.isl.ras.production
        # (ras_isl.py) and agri.intervention, which both inherit
        # mail.thread. No chatter needed in the view — activities
        # can be created without it.
        'mail.thread',
    ]

    intervention_id = fields.Many2one('mrp.production', string='Base Intervention', required=True, ondelete='cascade')

    # NOTE (18.0 port): upstream declared this as a stored precomputed
    # field with compute='_compute_aquaculture_kpi', but that method is
    # only defined on agri.isl.lot.aquaculture — this model has no such
    # method and no biomass/water-volume inputs to compute a density from
    # (fields.determine() would raise AttributeError on every create,
    # because precompute+store forces the compute at insert). The field
    # is kept (the form view displays it) as a plain stored Float;
    # the real KPI stays on the lot model.
    current_density = fields.Float(
        "Current Density (kg/m³)",
        default=0.0,
    )

    aquaculture_config = fields.Json(
        "Aquaculture Configuration",
        default=dict,
        help="JSON-based configuration for aquaculture-specific parameters"
    )

    # Real-time Sensors [US-109-04]
    latest_do_level = fields.Float("Latest Dissolved Oxygen (mg/L)")
    latest_water_temp = fields.Float("Latest Temp (℃)")
    
    def handle_aquaculture_telemetry(self, data):
        """
        [Active Defense] Triggers aeration if DO is low.

        NOTE (18.0 port, batch 3): transport-agnostic hook — it takes a
        plain ``data`` dict, no farm_iot/iiot model is imported or read
        here, so nothing had to be pruned. The future farm_iot module can
        call this method with live sensor payloads.
        """
        self.ensure_one()
        do_level = data.get('dissolved_oxygen')
        temp = data.get('temperature')

        if do_level is not None:
            self.latest_do_level = do_level
            # NOTE (18.0 port): upstream read 'self.recipe_id', a field
            # this model does NOT have (it lives on the recipe model, not
            # the task) — every call with a DO reading raised
            # AttributeError. The task's BoM comes from its _inherits
            # parent mrp.production as 'bom_id'; the ISL recipe is looked
            # up by that BoM.
            recipe = False
            if self.bom_id:
                recipe = self.env['agri.isl.aquaculture.recipe'].search([('recipe_id', '=', self.bom_id.id)], limit=1)
            threshold = recipe.min_dissolved_oxygen if recipe else 4.0
            
            if do_level < threshold:
                self.report_incident(
                    severity='critical', 
                    category='Oxygen Depletion', 
                    description=_("CRITICAL: Pond %s Dissolved Oxygen dropped to %s mg/L!") % (self.intervention_id.name, do_level)
                )
                self.apply_aeration_skill()
        
        if temp: self.latest_water_temp = temp
        return True

    def apply_aeration_skill(self):
        # NOTE (18.0 port, batch 3): no live actuator call — the payload is
        # only written to agent_instruction_json for a future IoT gateway
        # (farm_iot, next batch) to consume. Kept as upstream.
        """ Level 4 DNA: Direct control command to IoT Actuators. """
        self.ensure_one()
        payload = {
            'action': 'set_aerator',
            'state': 'on',
            'duration_minutes': 60,
            'pond': self.intervention_id.name
        }
        self.agent_instruction_json = json.dumps(payload, indent=2)
        self.agent_status_feedback = 'executing'
        _logger.warning("AQUACULTURE SKILL: Emergency Aeration triggered for %s", self.intervention_id.name)

    def action_confirm(self):
        """ Enforce stocking density check on confirm. """
        return super(FarmAquacultureTask, self).action_confirm()
