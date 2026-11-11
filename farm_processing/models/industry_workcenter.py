# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class FarmIndustryWorkcenter(models.Model):
    _name = 'farm.industry.workcenter'
    _description = 'Specialized Production Facility'
    _inherits = {'mrp.workcenter': 'workcenter_id'}

    workcenter_id = fields.Many2one('mrp.workcenter', string='Base Workcenter', required=True, ondelete='cascade')
    
    # --- Specialized Facility Metadata ---
    facility_type = fields.Selection([
        ('crop_field', 'Open Field'),
        ('greenhouse', 'Greenhouse'),
        ('livestock_pen', 'Animal Pen / Barn'),
        ('fish_pond', 'Aquaculture Pond'),
        ('factory_line', 'Processing Line'),
        ('lab_bench', 'Laboratory Bench')
    ], string='Physical Facility Type', default='factory_line', required=True)

    # Spatial & Environmental Stats
    surface_area = fields.Float("Surface Area (sqm)")
    volume_capacity = fields.Float("Volume Capacity (m3)")
    has_climate_control = fields.Boolean("Climate Controlled")
    
    # IoT Integration (Sync with EPIC-TECH-03)
    main_sensor_topic = fields.Char("Primary Telemetry Topic", help="Main sensor topic associated with this facility (e.g. pond temperature).")
