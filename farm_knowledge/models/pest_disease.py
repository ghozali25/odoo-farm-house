from odoo import models, fields


class FarmPestDisease(models.Model):
    """
    Farm-specific extension of the agricultural pest and disease model.
    This ensures backward compatibility while using the new agri.* namespace.
    """
    _name = 'farm.pest.disease'
    _description = 'Pest & Disease Database (Deprecated - Use agri.pest.disease)'
    _inherit = 'agri.pest.disease'

    # Port fix (batch 7, Odoo 18): the parent defines three Many2many
    # fields with EXPLICIT relation tables; inheriting them verbatim into
    # this alias model makes two fields share one table+columns, which
    # Odoo 18 rejects at registry load. Same relations, own tables.
    conventional_products = fields.Many2many(
        'product.template', 'farm_pest_disease_conventional_rel',
        'disease_id', 'product_id', string="Conventional Products",
        domain=[('is_agri_input', '=', True)],
        help="Recommended conventional products for treatment")
    organic_products = fields.Many2many(
        'product.template', 'farm_pest_disease_organic_rel',
        'disease_id', 'product_id', string="Organic/Green Products",
        domain=[('is_agri_input', '=', True)],
        help="Recommended organic/green products for treatment")
    affected_crops = fields.Many2many(
        'product.template', 'farm_pest_disease_crop_rel',
        'pest_disease_id', 'crop_id', string="Affected Crops",
        domain=[('agricultural_type', 'in', ['input', 'output'])],
        help="Crops that are typically affected by this pest/disease")

    def _register_hook(self):
        """Display deprecation warning when module is installed."""
        import logging
        _logger = logging.getLogger(__name__)
        _logger.warning(
            "farm.pest.disease is deprecated. "
            "Please update your code to use agri.pest.disease instead."
        )
        return super()._register_hook()
