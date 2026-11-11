# -*- coding: utf-8 -*-
{
    'name': 'Agri-OS: Livestock Financial Valuation Bridge',
    'summary': 'Micro-industry bridge for livestock biomass valuation and dynamic credit lines',
    'version': '18.0.1.0.0',
    'category': 'Agri/Financial',
    'author': 'Agri-OS Team',
    'depends': [
        'farm_financial_valuation',  # Horizontal platform package (X-axis)
        'farm_livestock'             # Vertical industry package (Y-axis)
    ],
    'auto_install': True,            # Dual-factor auto-activation rule
    # Port 19.0 -> 18.0: upstream shipped no security file at all; the two
    # concrete models below had no access rule, so every UI action on them
    # raised Access Error (same gap class as PORTING.md §8.6).
    'data': ['security/ir.model.access.csv'],
    'installable': True,
    'license': 'LGPL-3',
}
