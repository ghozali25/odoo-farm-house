{
    "name": "Farm Financial Valuation",
    "summary": "Biological asset valuation and financial instruments",
    "version": "18.0.1.0.0",
    "category": "Farming",
    "author": "genin IT, jeffery <jeffery9@gmail.com>",
    "maintainers": ["jeffery"],
    "depends": [
        "base",
        "mail",
        "account",
        "stock",
        "mrp",
        "farm_core",
        "farm_financial",
        # Port 19.0 -> 18.0: 'farm_ecology' PRUNED (not installed, outside
        # batch 1-5). Its only link was farm.location.gep_score, used by
        # the GEP premium below; the gep_score field on this model is now
        # a computed field that reads the location's gep_score defensively
        # (0.0 when farm_ecology is absent) instead of a related field,
        # so no code path here requires farm_ecology. Reversible: restore
        # the depends and the related field if farm_ecology is ported.
        "farm_operation",
        "farm_biological_valuation",  # Using the consolidated module created earlier
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/financial_valuation_views.xml",
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
    Financial Valuation Module
    ====================

    This module provides specialized financial valuation capabilities for farm operations:
    - Biological asset valuation (fair value and cost model)
    - Market price integration for valuation
    - Revaluation accounting entries
    - Growth stage coefficient management

    Built on top of the farm_financial foundation module.
    NOTE: This module uses the consolidated farm_biological_valuation module for core valuation functionality.
    """,
}