{
    'name': 'Farm Subsidy Management',
    'version': '18.0.1.0.0',
    'category': 'Industries/Agriculture',
    'summary': 'Government Subsidies and Policy Compliance',
    'description': """
        Manage agricultural subsidies and policy compliance [US-040-02].
        - Subsidy Programs (e.g. Organic Conversion, Crop Rotation)
        - Application Tracking & Reporting
        - Linking Subsidies to Land Parcels
    """,
    'author': 'Jeffery',
    # NOTE (port 19.0->18.0, batch 6): 'farm_mobile' pruned — 0 code refs
    # to farm_mobile models in this module (same pattern as PORTING.md §3).
    'depends': ['farm_core', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',  # batch 6: sequence was missing upstream
        'views/subsidy_views.xml',
        'views/subsidy_report_views.xml',  # batch 6: was never loaded upstream
        'views/evidence_views.xml',  # batch 6: views for concrete agri.evidence
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}
