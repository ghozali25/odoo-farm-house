# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class FarmAgriProduct(models.Model):
    """
    Agricultural Product extension of product.template with
    agricultural specific features (nutrients, allergens, license categories)
    """
    _inherit = 'product.template'

    # --- Specialized Metadata (Sunk from Base) ---
    industry_tag = fields.Selection(selection=[
        ('material', 'Input Material (Seeds/Fertilizer)'),
        ('food', 'Processed Food'),
        ('livestock', 'Live Animal'),
        ('raw_grain', 'Raw Grain / Harvest')
    ], string='Agricultural Industry Tag', default='material')

    # Nutrient Data
    n_content = fields.Float("Nitrogen (N) %")
    p_content = fields.Float("Phosphorus (P) %")
    k_content = fields.Float("Potassium (K) %")

    # Food Compliance
    license_category_ids = fields.Many2many('farm.production.license.category', 'product_template_farm_production_license_category_rel', 'template_id', 'category_id', string="Production License Categories")
    allergen_ids = fields.Many2many('farm.allergen', 'product_template_farm_allergen_rel', 'template_id', 'allergen_id', string="Allergens")
    nutrition_table = fields.Text("Nutrition Data (JSON/Text)")

    is_potency_standardized = fields.Boolean("Standardize by Potency")
    target_purity = fields.Float("Target Purity %", default=100.0)

