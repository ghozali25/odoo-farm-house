from odoo import models, fields, api, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_agri_material = fields.Boolean("Is Agri Material")
    is_processed_food = fields.Boolean("Is Processed Food")

    # US-004-05: Substitute products (Maintained at Base level for cross-industry visibility)
    substitute_product_ids = fields.Many2many(
        'product.template',
        'product_template_substitute_rel',
        'product_id',
        'substitute_id',
        string="Substitute Products",
        help="Products that can be used as substitutes for this product."
    )
