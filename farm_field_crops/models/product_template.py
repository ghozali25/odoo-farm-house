# -*- coding: utf-8 -*-
from odoo import models, fields


class ProductTemplate(models.Model):
    """Crop defaults on product.template (18.0 port).

    farm.field.crop.operation references these three fields, but no
    batch-1 module defines them anywhere in the repo:
    - crop_type_id domain: [('is_agricultural_product', '=', True)]
    - create(): crop.default_seeding_rate / crop.default_planting_density
    Without them the field-crop form fails to load (invalid domain field)
    and creating an operation with a crop type raises AttributeError.
    """
    _inherit = 'product.template'

    is_agricultural_product = fields.Boolean(
        "Is Agricultural Product",
        help="Mark products that are crops / agricultural products so they "
             "can be selected as crop types in field crop operations.")
    default_seeding_rate = fields.Float(
        "Default Seeding Rate",
        help="Default amount of seeds planted per unit area "
             "(e.g. kg/ha); copied to new field crop operations.")
    default_planting_density = fields.Float(
        "Default Planting Density",
        help="Default number of plants per unit area; copied to new "
             "field crop operations.")
