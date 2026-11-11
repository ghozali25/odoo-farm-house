{
    'name': 'Farm ESG Compliance',
    'version': '18.0.1.0.3',  # batch 6: farm_subsidy restored (see below)
    'category': 'Industries/Agriculture',
    'summary': 'ESG Compliance Management for Farm Operations (Epic 101)',
    'description': """
ESG Compliance module for Odoo 19 Farm Management System - Epic 101 Implementation.
- Carbon neutral certification and reporting
- Sustainable agriculture practice certification
- ESG data governance and quality control
- Triple bottom line metrics management (US-101-01)
- Multi-scale sustainable business model design (US-101-02)
- Sustainable supply chain management (US-101-04)
- Sustainable product lifecycle management (US-101-05)
    """,
    'author': 'genin IT, jeffery <jeffery9@gmail.com>',
    'website': 'http://www.geninit.cn',
    'depends': [
        'farm_esg',
        'farm_esg_environmental',
        'farm_agri_science',
        'farm_esg_circular',  # For circular economy integration
        # NOTE (port 19.0->18.0, batch 5): upstream depends
        # 'farm_supply_analytics', 'farm_supply_logistics',
        # 'farm_financial', 'farm_esg_risk' and 'account' trimmed — 0 code
        # references to any of their models in this module (verified by grep
        # over models/views/data). The only touchpoint was the Subsidies menu
        # (action_farm_subsidy -> farm.subsidy.application), removed from
        # views/esg_compliance_views.xml with this trim.
        # Batch 6: 'farm_subsidy' RESTORED (ported now) + action/menu
        # restored in views/esg_compliance_views.xml.
        'farm_subsidy',
        'mail',  # For mail.thread and activity mixins
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/esg_compliance_sequences.xml',
        'views/menu.xml',  # categories + record overrides only (early; see NOTE below)
        # NOTE (B5-FIX, 10 Nov 2026): 'views/menu.xml' (categories +
        # record overrides) loads EARLY; the action menuitems live in
        # 'views/menu_actions.xml' which MUST load LAST (see below).
        # Upstream had everything in one menu.xml listed twice (3rd
        # AND last): first load failed at menu.xml:58 (11 action IDs
        # not yet existing), and moving the whole file last broke
        # esg_compliance_views.xml:113 (menu_esg_operations not yet
        # existing) — a circular load order. Split resolves it.
        'views/esg_compliance_views.xml',
        'views/triple_bottom_line_metrics_views.xml',
        'views/sustainable_business_model_views.xml',
        'views/sustainable_supply_chain_views.xml',
        'views/sustainable_product_lifecycle_views.xml',
        'views/supply_chain_carbon_tracking_views.xml',
        'views/carbon_neutral_management_views.xml',
        'views/external_esg_marketplace_views.xml',
        'views/menu_actions.xml',
    ],
    'images': ['static/description/main_screenshot.png'],
    'installable': True,
    'application': True,
    'license': 'AGPL-3',
}