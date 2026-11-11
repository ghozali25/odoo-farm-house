{
    "name": "Farm Financial Credit",
    "summary": "Credit scoring and risk assessment for agricultural lending",
    "version": "18.0.1.0.0",
    "category": "Farming",
    "author": "genin IT, jeffery <jeffery9@gmail.com>",
    "maintainers": ["jeffery"],
    "depends": [
        "base",
        "mail",
        "account",
        "sale",
        "farm_core",
        "farm_financial",
        # Port 19.0 -> 18.0: 'farm_multi_farm_financial' PRUNED (module
        # outside batch 5, multi-farm family, not installed). Verified by
        # grep: ZERO code references to it outside this manifest, so no
        # code guard was needed. Reversible: restore the depends if that
        # module is ever ported.
        # NOTE: 'sale' ADDED (was missing upstream): the
        # farm.supply.chain.finance model has a sale.order field, which
        # fails registry load when sale is not a dependency.
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "views/credit_scoring_views.xml",
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
    Financial Credit and Risk Assessment Module
    ====================

    This module provides credit scoring and risk assessment capabilities for agricultural lending:
    - Credit scoring models for farmers and agricultural businesses
    - Risk assessment tools for agricultural loans
    - Collateral evaluation for biological assets
    - Credit history tracking
    - Default probability calculations

    Built on top of the farm_financial foundation module.
    """,
}