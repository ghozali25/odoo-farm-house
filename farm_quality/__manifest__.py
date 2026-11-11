{
    'name': 'Farm Quality Control',
    'version': '18.0.1.0.0',
    'category': 'Industries/Agriculture',
    'summary': 'Quality Control Points, Checks and Traceability',
    'description': """
        Quality module for Odoo 18 Farm Management System.
        - Quality Control Points (QCP) definition [US-038-04]
        - Quality Checks (Pass/Fail, Measurements) [US-038-02]
        - Quality Alerts & Traceability [US-002-01]
    """,
    'author': 'Jeffery',
    # 'purchase' is required: agri.quality.check.purchase_order_line_id
    # references purchase.order.line, which no other dependency provides.
    'depends': ['farm_operation', 'farm_core', 'purchase'],
    'data': [
        'security/farm_quality_groups.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        # 'data/quality_data.xml',
        'views/quality_point_views.xml',
        'views/quality_check_views.xml',
        'views/quality_alert_views.xml',
        'views/quality_record_book_views.xml',
        'views/quality_sample_views.xml',
        'views/stock_lot_views.xml',
    ],
    'images': ['static/description/main_screenshot.png'],
    'assets': {
        'web.assets_backend': [
            'farm_quality/static/src/components/**/*.js',
            'farm_quality/static/src/components/**/*.xml',
            'farm_quality/static/src/components/**/*.scss',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}
