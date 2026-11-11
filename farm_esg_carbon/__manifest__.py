{
    'name': 'Farm Carbon Extensions',
    'version': '18.0.1.0.0',
    'category': 'Industries/Agriculture',
    'summary': 'Product Carbon Factors, MRP Carbon Calculations, and Batch Carbon Tracking',
    'description': """
        Carbon extension module for Odoo 18 Farm Management System.
        - Product carbon emission factors
        - MRP production carbon calculation
        - Stock lot carbon footprint tracking
    """,
    'author': 'Jeffery',
    'depends': [
        'base',
        'farm_esg',
        # NOTE (port 19.0 -> 18.0): farm_esg_environmental is ported in the
        # same batch by another worker; it owns agri.carbon.ledger, which
        # this module extends (carbon_tokenization) and references
        # (farm.exchange.asset.origin_ledger_id). Keep this depends.
        'farm_esg_environmental',
        'mail',
        'product',
        'mrp',
        'stock',
        'farm_core',
        'farm_operation',
    ],
    'data': [
        'security/ir.model.access.csv',
        # Access for farm.exchange.asset (defined in models/carbon_tokenization.py);
        # the other models in this module only extend existing models.
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}