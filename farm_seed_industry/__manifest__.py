{
    'name': 'Seed Industry & R&D Management',
    'version': '18.0.1.0.1',
    'category': 'Industries/Agriculture',
    'summary': 'Specialized management for seed breeding, propagation, testing (Germination/Purity), and PVP compliance.',
    'depends': ['farm_core', 'farm_breeding', 'farm_agricultural_processing'],
    'data': [
        'security/ir.model.access.csv',
        'views/seed_views.xml',
        'views/menu.xml',
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'application': True,
    'license': 'AGPL-3',
}
