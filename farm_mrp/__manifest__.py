{
    'name': 'Farm MRP Base',
    'version': '18.0.1.1.0',
    'category': 'Industries/Agriculture',
    'summary': 'Agricultural extensions for MRP models',
    'description': """
        Agricultural-specific extensions for MRP models.

        It adds an industry classification to Bills of Materials and
        manufacturing orders, plus a destination stocking-density guard
        on production confirmation.
    """,
    'author': 'genin IT, jeffery <jeffery9@gmail.com>',
    'website': 'http://www.geninit.cn',
    'depends': ['mrp', 'stock', 'farm_core', 'farm_operation'],
    'data': [
        'security/ir.model.access.csv',
        'views/stock_matter_tracking_mrp_views.xml',
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}
