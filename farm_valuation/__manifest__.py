{
    "name": "Farm Biological Asset Valuation",
    "version": "18.0.1.0.1",
    "category": "Industries/Agriculture",
    "summary": "Advanced biological asset valuation with market price integration and fair value accounting",
    "description": """
        Advanced valuation module that provides:
        - Real-time fair value calculation for biological assets
        - Market price integration for commodity pricing
        - Automatic revaluation journal entries
        - Compliance with IAS 41 Agriculture (fair value accounting for biological assets)
        NOTE: This module now uses the consolidated farm_biological_valuation module for core functionality.
    """,
    "author": "Odoo Farm Dev Team",
    "depends": [
        "farm_core",
        "account",
        "product",
        "farm_biological_valuation",  # Consolidated biological asset valuation
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/ir_sequence_data.xml",
        "views/biological_asset_valuation_views.xml",
        "views/market_price_views.xml",
        "views/menu.xml",
    ],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "application": False,
    "license": "AGPL-3",
}