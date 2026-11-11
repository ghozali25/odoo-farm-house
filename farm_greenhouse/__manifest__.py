{
    'name': 'Farm Smart Greenhouse Control',
    'version': '18.0.1.0.1',
    'category': 'Industries/Agriculture',
    'summary': 'Automated Greenhouse Environment and Nutrient Control',
    'description': """
        Smart Greenhouse module for Odoo 19.
        - Environmental Multi-parameter Control [US-057-01]
        - Nutrient Solution & Irrigation Management [US-057-02]
        - Energy Optimization & Carbon Monitoring [US-057-03]
        - Government Regulatory Platform Integration [US-057-04]
    """,
    'author': 'genin IT, jeffery <jeffery9@gmail.com>',
    'website': 'http://www.geninit.cn',
    'depends': ['farm_core', 'farm_iot', 'farm_agri_science'],
    'data': [
        'security/ir.model.access.csv',
        'views/farm_greenhouse_views.xml',
        'views/government_reporting_views.xml',
        'views/ecommerce_integration_views.xml',  # batch 6: was never loaded upstream (needs ecommerce_integration import + government menu above)
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'application': True,
    'license': 'AGPL-3',
}