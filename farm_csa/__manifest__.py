{
    'name': 'Farm CSA Subscriptions',
    'version': '18.0.1.0.1',
    'category': 'Industries/Agriculture',
    'summary': 'Community Supported Agriculture (CSA) and Weekly Vegetable Bags',
    'description': """
        CSA module for Odoo 18 Farm Management System.
        - Subscription Plan management (Weekly, Monthly) [US-008-02]
        - Automated Delivery Task (Picking) Generation
        - Customer Subscription Lifecycle
    """,
    'author': 'Jeffery',
    'depends': ['farm_core',
        'mrp', 'stock', 'sale', 'farm_multi_farm', 'farm_operation'],
    'data': [
        # Port fix (batch 7): upstream had the ACL CSV commented out, so
        # NO access rules were ever loaded — even admin got "Access Denied
        # by ACLs" on farm.csa.plan / farm.csa.subscription. Uncommented.
        'security/ir.model.access.csv',
        'data/ir_cron_data.xml',
        'views/csa_subscription_views.xml',
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}
