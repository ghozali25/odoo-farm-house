from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class FarmLocation(models.Model):
    _inherit = 'farm.location'

    isa95_level = fields.Selection([
        ('enterprise', 'Enterprise (Company)'),
        ('site', 'Site (Farm)'),
        ('area', 'Area (Sector/Barn)'),
        ('production_line', 'Production Line (Pond/Greenhouse)'),
        ('work_center', 'Work Center (Specific Bed/Rack)'),
        ('unit', 'Unit (Specific Pot/Cage)')
    ], string='ISA-95 Level', default='area', help="Industry standard functional hierarchy level")

    digital_twin_enabled = fields.Boolean("Digital Twin Enabled", default=False)
    digital_twin_scene_id = fields.Many2one('agri.digital.twin.scene', string="3D Scene")

class FarmDigitalTwinScene(models.Model):
    """
    Farm-specific extension of the agricultural digital twin scene model.
    This ensures backward compatibility while using the new agri.* namespace.
    """
    _name = 'farm.digital.twin.scene'
    _description = 'Digital Twin 3D Scene (Deprecated - Use agri.digital.twin.scene)'
    _inherit = 'agri.digital.twin.scene'

    def _register_hook(self):
        """Display deprecation warning when module is installed."""
        import logging
        _logger = logging.getLogger(__name__)
        _logger.warning(
            "farm.digital.twin.scene is deprecated. "
            "Please update your code to use agri.digital.twin.scene instead."
        )
        return super()._register_hook()

class FarmDigitalTwinMarker(models.Model):
    """
    Farm-specific extension of the agricultural digital twin marker model.
    This ensures backward compatibility while using the new agri.* namespace.
    """
    _name = 'farm.digital.twin.marker'
    _description = 'Digital Twin Device Marker (Deprecated - Use agri.digital.twin.marker)'
    _inherit = 'agri.digital.twin.marker'

    def _register_hook(self):
        """Display deprecation warning when module is installed."""
        import logging
        _logger = logging.getLogger(__name__)
        _logger.warning(
            "farm.digital.twin.marker is deprecated. "
            "Please update your code to use agri.digital.twin.marker instead."
        )
        return super()._register_hook()

# NOTE (porting 19.0 -> 18.0): the iiot.device extension
# (digital_twin_model_url / last_telemetry_json) was defined TWICE upstream
# (here and as AgriIiotDevice in agri_digital_twin.py, byte-identical
# behaviour). The duplicate is removed here; the single definition lives
# in agri_digital_twin.py.
