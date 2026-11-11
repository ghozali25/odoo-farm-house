{
    "name": "Farm ESG Environmental Assessment",
    "summary": "ESG environmental assessments using ecological data within ESG governance framework (from farm_esg) - VRA Environmental Impact Assessment (Epic 80)",
    "version": "18.0.1.0.1",
    "category": "Farming",
    "author": "genin IT, jeffery <jeffery9@gmail.com>",
    "maintainers": ["jeffery"],
    "description": """
ESG Environmental Assessment module for Odoo 19 Farm Management System - Epic 80 Implementation.
- VRA carbon footprint calculation and reduction analysis
- Water body protection VRA strategies with buffer zones
- Soil health VRA models with health metrics integration
- Environmental risk assessment and compliance
- Integration with ESG governance framework for comprehensive sustainability tracking
    """,
    "depends": [
        "base",
        "mail",
        "farm_core",
        "farm_esg",
        # NOTE (port 19.0->18.0, batch 5): upstream depends 'farm_ecology'
        # and 'farm_equipment' trimmed — 0 code references to farm_ecology,
        # and farm_equipment was only used by models/equipment_log_extension.py
        # (fuel-log -> carbon-ledger bridge), which is dropped with this trim.
        # The Scope-1 fuel bridge returns when farm_equipment is ported.
        "farm_agri_science",
        "farm_operation",  # For interventions
        "farm_iot",  # For sensor data
    ],
    "data": [
        "security/security_groups.xml",
        "security/ir.model.access.csv",
        "views/esg_settings_views.xml",
        "data/ir_sequence_data.xml",
        "views/environmental_views.xml",
        "views/carbon_accounting_views.xml",
        "views/esg_red_line_monitoring_views.xml",
        "views/vra_carbon_footprint_views.xml",
        "views/vra_water_protection_views.xml",
        "views/vra_soil_health_views.xml",
        "views/menu.xml",
    ],
    "demo": [
    ],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "auto_install": False,
    "license": "AGPL-3",
    "website": "http://www.geninit.cn"
}