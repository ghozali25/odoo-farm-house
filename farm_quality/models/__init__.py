# Core Agri Quality Models (Independent implementation, NO enterprise dependency)
from . import agri_quality
from . import agri_quality_sample
from . import agri_quality_record_book
# from . import quality  # Deprecated: proxies enterprise quality.point /
#   quality.check (Odoo Enterprise, not in CE 18) — HACCP stays out of batch 1.
from . import sample  # farm.quality.sample: thin deprecated alias over the
# farm's own agri.quality.sample (NO enterprise dependency). MUST stay
# imported: security/ir.model.access.csv + views/quality_sample_views.xml
# reference model_farm_quality_sample; leaving it out breaks install.
from . import product_extension
from . import stock_picking_extension
from . import qc_extension
