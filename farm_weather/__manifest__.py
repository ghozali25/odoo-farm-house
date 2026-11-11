{
    'name': 'Farm Weather Forecast',
    'version': '18.0.1.0.1',
    'category': 'Industries/Agriculture',
    'summary': 'Weather Forecast Integration for Farm Management',
    'description': """
        Weather module for Odoo 18 Farm Management System.
        - Fetch 7-day weather forecast via external API
        - Link weather to GIS locations (parcels)
        - Weather-based alerts (Frost, Storm, High Temp)
    """,
    'author': 'Jeffery',
    # NOTE (porting 19.0 -> 18.0, batch 4): upstream depended on 'farm_iot',
    # but no code in this module references farm_iot / iiot.* at all
    # (grep = 0 outside the manifest) -- the dependency was pruned so this
    # module installs on its own. Re-add it only if a future change actually
    # uses an IoT model.
    'depends': ['farm_core'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/weather_forecast_views.xml',
        'views/res_config_settings_views.xml',
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}
