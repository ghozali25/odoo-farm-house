{
    'name': 'Farm Dashboard & Cockpit',
    'version': '18.0.1.0.1',
    'category': 'Industries/Agriculture',
    'summary': 'Unified Dashboard for Farm Operations and Metrics',
    'description': """
        Dashboard module for Odoo 18 Farm Management System.
        - Integrated view of production, inventory and weather
        - Resource availability overview
        - Critical alerts and safety status
    """,
    'author': 'Jeffery',
    'depends': ['farm_operation', 'farm_weather', 'farm_iot', 'farm_financial'],
    'data': [
        'views/farm_dashboard_views.xml',
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'application': True,
    'license': 'AGPL-3',
}
