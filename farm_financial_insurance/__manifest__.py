{
    "name": "Farm Financial Insurance",
    "summary": "Insurance products for agricultural operations",
    "version": "18.0.1.0.0",
    "category": "Farming",
    "author": "genin IT, jeffery <jeffery9@gmail.com>",
    "maintainers": ["jeffery"],
    "depends": [
        "base",
        "mail",
        "account",
        "farm_core",
        "farm_financial",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/insurance_views.xml",
        "views/menu.xml",
    ],
    "demo": [
    ],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "auto_install": False,
    "license": "AGPL-3",
    "website": "http://www.geninit.cn",
    "description": """
    Financial Insurance Module
    ====================

    This module provides insurance product management for agricultural operations:
    - Crop yield insurance
    - Weather index insurance
    - Livestock insurance
    - Property insurance for farm assets
    - Insurance claim management

    Built on top of the farm_financial foundation module.
    """,
}