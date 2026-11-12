{
    'name': 'Farm Field Crops',
    'version': '18.0.1.0.1',
    'category': 'Industries/Agriculture',
    'summary': 'Field Crops Management - Plots, Sowing, Harvesting, Mechanized Operations',
    'description': """
        Field Crops Management Module for Odoo 18 Farm Management System.

        Features:
        - Field crop plot management with specific field crops attributes
        - Sowing and harvesting operations for field crops
        - Mechanized operations tracking for large scale farming
        - Planting density and seeding rate management
        - Fertilizer application planning and tracking
        - Large scale irrigation management
        - Harvest yield tracking and analysis

        Changelog:
        - 18.0.1.0.1: Merged duplicate "Field Crops" root menu (kept
          farm_field_crops_menu_root; moved Operations under it).
    """,
    'author': 'Jeffery',
    'depends': [
        'farm_core',
        'farm_operation',
        'farm_mrp',
        'project',
        'stock',
        'mrp',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/field_crop_operation_views.xml',
        'views/crop_isl_views.xml',
        'views/menu.xml',
    ],
    'demo': [
    ],
    
    'assets': {
        'web.assets_tests': [
            'farm_field_crops/static/tests/tours/**/*',
        ],
    },
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}