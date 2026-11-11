{
    "name": "Farm ESG Risk Management",
    "summary": "Manage ESG risk assessment, compliance and governance aspects of farming operations",
    "version": "18.0.1.0.0",
    "category": "Farming",
    "author": "genin IT, jeffery <jeffery9@gmail.com>",
    "maintainers": ["jeffery"],
    "depends": [
        "base",
        "mail",
        "farm_core",
        "farm_hr",
        "farm_esg",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/esg_risk_views.xml",
        "views/menu.xml",
        "views/esg_data_governance_views.xml",
        "views/esg_report_customization_views.xml",
        "views/esg_scenarios_analysis_views.xml",
    ],
    "demo": [
    ],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "auto_install": False,
    "license": "AGPL-3",
    "website": "http://www.geninit.cn"
}