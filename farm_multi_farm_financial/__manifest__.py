{
    'name': 'Multi-Entity Financial Management',
    'version': '18.0.1.0.0',
    'category': 'Industries/Agriculture',
    'summary': 'Multi-Entity Financial Management Module',
    'description': """
        Financial management module for Multi-Entity Collaboration System.
        - Member shares and dividend management [US-042-06]
        - Internal credit and lending management [US-042-07]
        - Dividend distribution and tracking [US-042-06]
        - Share transaction recording [US-042-06]
    """,
    'author': 'Jeffery',
    'depends': [
        'farm_multi_farm',
        'account',
        'base',
        'mail',
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/ir_rule.xml',
        'data/ir_sequence.xml',  # batch 6: sequences were missing upstream
        'views/menu.xml',
        # batch 6: the two view files below were never loaded upstream
        'views/member_share_views.xml',
        'views/finance_governance_views.xml',
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}