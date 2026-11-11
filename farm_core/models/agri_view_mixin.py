from odoo import models, api

class AgriViewMixin(models.AbstractModel):
    """
    [Level 0: Foundation] - Base UI/UX adaptation mixin.
    Extension point for UI/UX adaptations (e.g. a future farm_ux module,
    which is not part of batch 1); the base implementation is a no-op.
    """
    _name = 'agri.view.mixin'
    _description = 'Agri UI/UX View Foundation Mixin'

    @api.model
    def _apply_agri_term_mapping(self, arch):
        """ Base implementation returns arch as is. """
        return arch
