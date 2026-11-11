{
    'name': 'Farm Planning & Scenarios',
    'version': '18.0.1.0.1',
    'category': 'Industries/Agriculture',
    'summary': 'Advanced Production Planning, Technical Routes and Scenarios (Inspired by Ekylibre)',
    'description': """
        Strategic and tactical planning for Odoo 18 Farm Management.
        - Technical Routes (Sequences of intervention templates)
        - Scenario Simulation (What-if analysis)
        - Intervention Proposals (Estimated future tasks)
        - Resource Load Forecasting (Labor, Equipment, Inputs)
    """,
    'author': 'Jeffery',
    'depends': ['farm_operation'],
    'data': [
        'security/ir.model.access.csv',
        'data/agri_templates_data.xml',
        'views/technical_route_views.xml',
        'views/intervention_template_views.xml',
        'views/scenario_views.xml',
    ],
    'demo': [
        'data/farm_planning_demo.xml',
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'application': True,
    'license': 'AGPL-3',
}