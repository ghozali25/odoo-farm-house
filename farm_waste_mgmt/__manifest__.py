{
    'name': 'Farm Waste Management',
    'version': '18.0.1.0.3',  # batch 6: input_type reconciled (local def removed)
    'category': 'Industries/Agriculture',
    'summary': 'Livestock/Poultry Manure Management and Utilization Ledger',
    'description': """
        Manages livestock and poultry manure resource utilization ledgers.
        - Records disposal methods (composting, biogas, third-party transfer).
        - Tracks destination and recipient information.
        - Generates monthly utilization ledgers for manure resources.
        NOTE (port 19.0 -> 18.0, de-China-ize): upstream named this module
        after China and its MOARA ledger format; the ledger itself is a
        generic monthly utilization record, so the country/regulator
        references were generalized (method ``action_generate_ledger``,
        report "Manure Ledger").
    """,
    'author': 'Jeffery',
    'depends': ['farm_core', 'farm_livestock', 'farm_quality'],
    'data': [
        'security/ir.model.access.csv',
        'data/farm_waste_sequences.xml',
        'report/manure_ledger_report_templates.xml',
        'report/manure_ledger_reports.xml',
        'views/waste_mgmt_views.xml',
        'views/waste_management_views.xml',
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'application': False,
    'license': 'AGPL-3',
}
