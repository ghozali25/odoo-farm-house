# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions

class AgriInterventionMixin(models.AbstractModel):
    _inherit = 'agri.intervention.mixin'

    # Scenario 51: Strict JA Brand SOP Enforcement
    sop_compliance_status = fields.Selection([
        ('compliant', 'Fully Compliant (JA Premium)'),
        ('warning', 'Minor Deviation'),
        ('violation', 'SOP Violation (Downgraded)')
    ], string='SOP Compliance', default='compliant', tracking=True)
    
    def action_log_violation(self, reason):
        """Called automatically if a task is late or IoT detects banned chemical."""
        self.write({
            'sop_compliance_status': 'violation'
        })
        # Automatically downgrade linked crop/asset.
        # NOTE (18.0 port): 'commodity' is not a valid quality_grade value
        # on any batch-1 asset model (stock.lot uses grade_a/b/c/ungraded,
        # agri.biological.asset uses premium/standard/utility), so writing
        # it would raise a ValidationError. Downgrade only to a value the
        # linked asset actually accepts.
        if hasattr(self, 'asset_id') and self.asset_id:
            asset = self.asset_id
            if 'quality_grade' in asset._fields:
                valid_grades = dict(asset._fields['quality_grade'].selection)
                grade = next(
                    (g for g in ('commodity', 'ungraded') if g in valid_grades),
                    None,
                )
                if grade:
                    asset.write({'quality_grade': grade})
            if hasattr(asset, 'message_post'):
                asset.message_post(body=f"⚠️ Downgraded due to SOP Violation: {reason}")
