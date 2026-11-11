# -*- coding: utf-8 -*-
from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # NOTE (port 19.0 -> 18.0, batch 6 RECONCILED): ``input_type`` was
    # defined locally here in batch 5 because ``farm_supply_procurement``
    # was not ported yet; that module (batch 6) now defines the field on
    # ``product.template`` with identical selection values, so the local
    # definition is REMOVED (the column is reused by the upstream
    # definition — Odoo does not drop it). ``agri.manure.batch.
    # fertilizer_product_id`` domain on ``input_type`` keeps working.
    # ``n_content``/``p_content``/``k_content`` already exist on
    # ``product.template`` via farm_core, so they are NOT redefined here.
