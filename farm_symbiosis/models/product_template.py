# -*- coding: utf-8 -*-
"""product.template extension (batch 7).

Upstream ``farm_symbiotic.order._compute_toxin_risk`` reads
``product_id.is_toxic_to_fish`` but NO module in the repo defines that
field — the compute would crash with AttributeError on first read.
Minimal addition: Boolean flag, default False (non-toxic).
"""
from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_toxic_to_fish = fields.Boolean(
        "Toxic to Fish/Shrimp", default=False,
        help="Mark products (e.g. pesticides) that are toxic to aquatic "
             "life. Symbiotic orders are hard-blocked when a toxic "
             "product is among the raw materials.")
