{
    'name': 'Farm IoT Management Center',
    'version': '18.0.1.2.3',
    'category': 'Industries/Agriculture',
    'summary': 'IoT Management Center - Digital Twin, Global Mapping & Command Orchestration',
    'description': """
        Management Center for Odoo 18 Farm IoT Architecture. [US-203]
        - Centralized IoT Device Mapping & Business Orchestration.
        - Digital Twin Management for Agricultural Assets.
        - Global Command Audit Log (Independent Management Audit).
    """,
    'author': 'jeffery <jeffery9@gmail.com>',
    # NOTE (porting 19.0 -> 18.0): author cleaned of CJK characters
    # (upstream listed a Chinese vendor name); vendor website removed.
    'depends': ['farm_core', 'project', 'agri_iot', 'maintenance', 'stock', 'mrp'],
    'data': [
        'security/ir.model.access.csv',
        'data/iot_cron_data.xml',
        'views/iot_mapping_views.xml',
        'views/farm_telemetry_views.xml',
        'views/farm_automation_views.xml',
        'views/farm_event_correlation_views.xml',
        
        'views/iiot_device_views.xml',
        'views/digital_twin_views.xml',
        'views/storage_env_views.xml',
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'application': True,
    'license': 'AGPL-3',
}
