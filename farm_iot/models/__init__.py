from . import iiot_device
# NOTE (porting 19.0 -> 18.0): agri_telemetry MUST be imported — it is the
# ONLY definition of model 'agri.telemetry' in the whole repo (upstream 19.0
# has it commented out too, yet farm_telemetry.py inherits 'agri.telemetry'
# and tests/test_epic_006.py uses it). Without this import the registry
# fails on 'farm.telemetry' ('Model agri.telemetry does not exist').
from . import agri_telemetry
# NOTE (porting 19.0 -> 18.0): farm_telemetry MUST be imported too — upstream
# models/__init__.py never imports it, yet the ACL CSV references model
# 'farm.telemetry' (model_farm_telemetry). Without this import install fails
# 'No matching record found for external id model_farm_telemetry'. Same class
# of upstream bug as agri_telemetry above.
from . import farm_telemetry
from . import farm_iot_telemetry
from . import farm_automation_rule
from . import farm_command_log
from . import farm_iot_mapping
from . import iot_telemetry_buffer
from . import agri_digital_twin
from . import digital_twin
from . import iiot_device_inherit
from . import mrp
from . import farm_event_correlation
from . import storage_env
from . import agri_iot_wal_log
from . import agri_telemetry_series
from . import water_valve
