from odoo import models, fields

class StockMove(models.Model):
    _inherit = 'stock.move'

    # Harvest grading fields [US-002-04]
    quality_grade = fields.Selection([
        ('grade_a', 'Grade A'),
        ('grade_b', 'Grade B'),
        ('grade_c', 'Grade C'),
    ], string="Quality Grade")

    # US-037-07: Agri Loss Management
    agri_loss_reason = fields.Selection([
        ('natural', 'Natural Dehydration'),
        ('decay', 'Decay/Rot'),
        ('pest_damage', 'Pest/Rodent Damage'),
        ('handling', 'Handling Damage'),
        ('processing', 'Processing Waste'),
    ], string="Agri Loss Reason")

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        """Override so grading info is carried to the move lines and the final lots."""
        vals = super()._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant)
        if self.quality_grade:
            vals['quality_grade'] = self.quality_grade
        return vals
