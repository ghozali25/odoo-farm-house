{
    'name': 'Farm Marketing & Traceability',
    'version': '18.0.1.0.3',
    'category': 'Industries/Agriculture',
    'summary': 'Consumer Traceability, Marketing QR Codes and Brand Story',
    'description': """
        Marketing module for Odoo 18 Farm Management System.
        - Consumer-facing Traceability Portal [US-008-01]
        - Product Story & Quality Certificate Display
        - Integration with Agritourism & CRM

        Changelog 18.0.1.0.3: stock.lot now inherits agri.quality.gate.mixin
        (farm_core) so quality_status exists for the integrity score compute;
        fixes install crash (AttributeError) on databases with existing lots.
    """,
    'author': 'Jeffery',
    'depends': ['farm_core', 'farm_operation', 'website', 'loyalty'],
    'data': [
        'security/ir.model.access.csv',
        'views/gi_registry_views.xml',
        'views/farm_lot_views.xml',
        'views/partner_views.xml',
        'views/sale_order_views.xml',
        'views/traceability_templates.xml',
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}
