{
    'name': 'Farm Circular Economy',
    'version': '18.0.1.0.0',
    'category': 'Industries/Agriculture',
    'summary': 'Circular Economy and Resource Flow Models (Epic 27)',
    'description': """
Circular economy module for Odoo 19 Farm Management System - Epic 27 Implementation.
- Circular flow economics and resource utilization optimization
- Waste-to-resource conversion tracking
- Hazardous waste compliance management (US-057-03)
- Biogas and energy recovery quantification (US-057-04)
- Cooperative resource sharing coordination (US-057-05)
- GIS-driven geospatial cycle network (US-057-06)
- Regional circular economy governance (US-057-07)
    """,
    'author': 'Jeffery',
    'depends': [
        'base',
        'mail',
        'farm_core',
        # NOTE (port 19.0->18.0, batch 5): upstream 'farm_equipment' trimmed —
        # 0 references to any farm.equipment.* model in this module; the only
        # equipment reference is core 'maintenance.equipment' (biogas digester),
        # available via farm_operation -> maintenance.
        'farm_operation',
        'farm_esg',
        'farm_esg_environmental',
         # For integration with ESG compliance
        'product',  # For product references
        'uom',      # For unit of measure
        'hr',  # For hr.department (responsible department); core module.
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/circular_flow_views.xml',
        'views/hazardous_waste_views.xml',
        'views/biogas_energy_views.xml',
        'views/cooperative_coordination_views.xml',
        'views/geospatial_coordination_views.xml',
        'views/regional_governance_views.xml',
        'views/menu.xml',
        'data/ir_sequence_data.xml',
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}