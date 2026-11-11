from odoo import models, fields, api, _
from datetime import date

class FarmLocationCert(models.Model):
    _inherit = 'stock.location'

    certification_level = fields.Selection([
        ('conventional', 'Conventional'),
        ('organic_transition', 'Organic Transition'),
        ('organic', 'Organic'),
        ('green', 'Green Food'),
        ('gi', 'Geographical Indication')
    ], string="Certification Level", default='conventional', tracking=True)
    
    certificate_number = fields.Char("Certificate Number")
    certificate_expiry = fields.Date("Certificate Expiry")
    
    conversion_start_date = fields.Date("Conversion Start Date")
    last_prohibited_substance_date = fields.Date("Last Prohibited Substance Date", 
                                               help="Automatically updated when a non-organic input is used.")
    conversion_target_days = fields.Integer("Target Conversion Days", default=1095) # Default 3 years
    conversion_progress = fields.Float("Conversion Progress (%)", compute='_compute_conversion_progress', store=True, precompute=True)
    
    @api.depends('conversion_start_date', 'last_prohibited_substance_date', 'conversion_target_days')
    def _compute_conversion_progress(self):
        today = date.today()
        for loc in self:
            # Conversion start is the later of the declaration start date and the last prohibited-substance application date
            start_point = loc.conversion_start_date
            if loc.last_prohibited_substance_date:
                if not start_point or loc.last_prohibited_substance_date > start_point:
                    start_point = loc.last_prohibited_substance_date
            
            if start_point and loc.conversion_target_days > 0:
                delta = (today - start_point).days
                loc.conversion_progress = max(0.0, min(100.0, (delta / loc.conversion_target_days) * 100.0))
                
                # If progress reaches 100%, auto-upgrade status
                if loc.conversion_progress == 100.0 and loc.certification_level == 'organic_transition':
                    loc.certification_level = 'organic'
            else:
                loc.conversion_progress = 0.0

class FarmLotCert(models.Model):
    _inherit = 'stock.lot'

    certification_level = fields.Selection([
        ('conventional', 'Conventional'),
        ('organic_transition', 'Organic Transition'),
        ('organic', 'Organic'),
        ('green', 'Green Food'),
        ('gi', 'Geographical Indication')
    ], string="Certification Level", store=True)

    @api.onchange('location_id')
    def _onchange_location_id_certification(self):
        if self.location_id:
            self.certification_level = self.location_id.certification_level
