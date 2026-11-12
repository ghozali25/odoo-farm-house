{
    'name': 'Farm Aquaculture',
    'version': '18.0.1.0.3',
    'category': 'Industries/Agriculture',
    'summary': 'Aquaculture Management - Water Quality, Feeding, Growth Tracking, Dissolved Oxygen Monitoring',
    'description': """
        Aquaculture Management Module for Odoo 18 Farm Management System.

        Features:
        - Water quality monitoring and management
        - Aquatic species feeding management
        - Growth tracking for aquatic species
        - Dissolved oxygen and pH monitoring
        - Pond/tank management
        - Aquaculture specific harvest management
        - Water treatment and circulation management

        Changelog:
        - 18.0.1.0.3: Merged duplicate "Aquaculture" root menu (kept
          farm_aquaculture_menu_root; moved Operations and Water Quality
          Logs under it).
    """,
    'author': 'Jeffery',
    'depends': [
        'farm_core',
        'farm_operation',
        'farm_mrp',
        # NOTE (18.0 port, batch 3): 'farm_iot' PRUNED — it belongs to the
        # next batch (IoT/weather) and is not installed in test18. The only
        # IoT touchpoints in this module were transport-agnostic dict hooks
        # (handle_aquaculture_telemetry / handle_lss_telemetry, taking a
        # plain data dict) plus docstrings; no model field referenced
        # farm_iot/iiot.device. See PORTING.d/farm_aquaculture.md.
        'project',
        'stock',
        'mrp',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/aquaculture_operation_views.xml',
        'views/aquaculture_isl_views.xml',
        'views/updated_aquaculture_production_view.xml',
        'views/menu.xml',
    ],
    'demo': [
    ],
    
    'assets': {
        'web.assets_tests': [
            'farm_aquaculture/static/tests/tours/**/*',
        ],
    },
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}