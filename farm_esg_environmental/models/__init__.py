# ESG Environmental models for compliance, reporting and certification
from . import agri_esg_red_line_monitoring
from . import esg_environmental_report
from . import esg_environmental_tracker  # NOTE (B5-FIX, 10 Nov 2026): file ada di disk tapi tidak pernah di-import upstream -> model esg.environmental.tracker tidak ter-register dan ir.model.access.csv gagal diproses saat install
from . import farm_carbon_accounting
from . import esg_red_line_monitoring
from . import vra_carbon_footprint
from . import vra_water_protection
from . import vra_soil_health
# NOTE (port 19.0->18.0, batch 5): equipment_log_extension dropped
# with the farm_equipment trim (see __manifest__.py).
from . import esg_settings

