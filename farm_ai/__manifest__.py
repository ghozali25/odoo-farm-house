{
    "name": "Farm AI Core",
    "summary": "Core AI infrastructure for agricultural applications",
    "version": "18.0.1.0.1",
    "category": "Farming",
    "author": "genin IT, jeffery <jeffery9@gmail.com>",
    "maintainers": ["jeffery"],
    "depends": [
        "base",
        "mail",
        "farm_core",
    ],
    "data": [
        # Port fix (batch 7): upstream had the ACL CSV commented out, so
        # NO access rules were ever loaded — even admin got "Access Denied
        # by ACLs" on agri.ai.* models. Uncommented.
        "security/ir.model.access.csv",
        "views/ai_config_views.xml",
        "views/ai_model_registry_views.xml",
        "views/menu.xml",
    ],
    "demo": [],
    "images": ["static/description/main_screenshot.png"],
    "installable": True,
    "auto_install": False,
    "license": "AGPL-3",
    "website": "http://www.geninit.cn",
    "description": """
    AI Core for Agricultural Applications
    ============

    This module provides the core AI infrastructure for agricultural applications,
    including base classes, utilities, and common functionality for all AI modules.

    Key Features:
    - Base AI model classes and mixins
    - Common AI utilities and helpers
    - Configuration management for AI services
    - Model registry and management
    """,
}