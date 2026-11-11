from odoo import models, fields, api

class FarmTraitValue(models.Model):
    _name = 'farm.trait.value'
    _description = 'Breeding Trait Value'

    name = fields.Char("Trait Name", required=True) # e.g., Yield, Disease Resistance
    value = fields.Char("Measured Value") # e.g., 500kg, High
    score = fields.Float("Score (0-10)", help="Numeric score for comparison")
    
    lot_id = fields.Many2one('stock.lot', string="Lot/Asset", ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

class FarmLotBreeding(models.Model):
    _inherit = 'stock.lot'

    trait_value_ids = fields.One2many('farm.trait.value', 'lot_id', string="Traits")
    trait_score_avg = fields.Float("Average Trait Score", compute='_compute_trait_score_avg', store=True, precompute=True)

    # Genetic marker (18.0 port): farm_nursery_batch_extension reads
    # stock.lot.dna_marker for the lethal-gene collision check, but no
    # batch-1 model defines it on stock.lot (farm_core only defines it on
    # agri.biological.asset). Defined here so the check does not raise
    # AttributeError when a nursery batch is created with both parents.
    dna_marker = fields.Char("Genetic Marker / DNA ID")
    
    # Pedigree [US-020-05]
    father_id = fields.Many2one('stock.lot', string="Sire", domain="[('gender', '=', 'male')]")
    mother_id = fields.Many2one('stock.lot', string="Dam", domain="[('gender', '=', 'female')]")
    gender = fields.Selection([('male', 'Male'), ('female', 'Female'), ('other', 'Mixed/Unknown')], default='other')

    def get_ancestors(self, depth=5):
        """ Recursively collect the set of ancestor IDs """
        ancestors = set()
        if depth <= 0:
            return ancestors
        
        parents = (self.father_id | self.mother_id).filtered(lambda x: x)
        for p in parents:
            ancestors.add(p.id)
            ancestors.update(p.get_ancestors(depth - 1))
        return ancestors

    def check_inbreeding_risk(self, partner_lot, max_depth=3):
        """ Check whether there is an inbreeding risk with the mate """
        self.ensure_one()
        my_ancestors = self.get_ancestors(max_depth)
        partner_ancestors = partner_lot.get_ancestors(max_depth)
        
        common = my_ancestors.intersection(partner_ancestors)
        if common:
            names = self.env['stock.lot'].browse(list(common)).mapped('name')
            return _("INBREEDING RISK: Common ancestors found within %s generations: %s") % (max_depth, ", ".join(names))
        return False

    @api.depends('trait_value_ids.score')
    def _compute_trait_score_avg(self):
        for lot in self:
            scores = lot.trait_value_ids.mapped('score')
            lot.trait_score_avg = sum(scores) / len(scores) if scores else 0.0

    def action_compare_traits(self):
        """ Open the trait comparison wizard [US-020-08] """
        return {
            'name': _('Trait Performance Comparison'),
            'type': 'ir.actions.act_window',
            'res_model': 'farm.trait.comparison.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_lot_ids': self.ids}
        }
