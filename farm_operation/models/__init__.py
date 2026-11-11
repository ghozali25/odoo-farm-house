# Order of loading is critical for model dependencies
# 0. L0 intervention engine now comes from the `agri_intervention` module
#    (batch 2) — the vendored copy (agri_intervention_base.py) was deleted
#    10 Nov 2026; this module depends on agri_intervention (see manifest).
# 1. Base Mixins & Domain Mixins
from . import agri_agricultural_campaign_mixin
from . import agri_bom_mixin
from . import agri_operation_mixin
from . import agri_intervention_mixin
from . import farm_agricultural_campaign_mixin
from . import farm_agricultural_intervention_mixin
from . import farm_agricultural_bom_mixin

# 2. Domain Base Entities
from . import farm_agricultural_campaign_base

# 3. Core Extensions & Application Models
from . import agricultural_campaign
from . import agri_bom
from . import agri_intervention
from . import project_task
from . import stock_move
from . import farm_agricultural_campaign
from . import farm_agricultural_intervention
from . import farm_agricultural_bom

# 4. Auxiliary & Integrations
# NOTE: farm_isl_redirection.py was removed in the 19.0 -> 18.0 port: it only
# overrode get_formview_action() to call super() (no-op redirection stubs
# towards the `farm_isl` models, which are not in batch 1).
from . import sale_order
