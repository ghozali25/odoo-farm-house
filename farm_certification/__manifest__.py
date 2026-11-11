{
    'name': 'Farm Certification & Compliance',
    'version': '18.0.1.0.1',
    'category': 'Industries/Agriculture',
    'summary': 'Organic, Green and GI Certification Management',
    'description': """
        Certification module for Odoo 19 Farm Management System.
        - Manage Certification Levels (Organic, Green, Conventional)
        - Track Organic Conversion Periods
        - Certificate Document Management & Expiry Alerts
        - Automatic Certification Inheritance for Harvested Lots
    """,
    'author': 'Jeffery',
    'depends': ['farm_core', 'farm_operation', 'purchase', 'farm_quality'],
    'data': [
        'security/ir.model.access.csv',
        'views/certification_views.xml',
        'views/gap_certification_views.xml',  # batch 6: was never loaded upstream (needs gap_certification import)
        'views/certification_report.xml',
        'views/certification_renewal_wizard_views.xml',  # batch 6: new wizard view
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}
