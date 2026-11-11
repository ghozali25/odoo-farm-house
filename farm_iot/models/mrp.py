# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    def _hook_post_start(self):
        """[US-IOT-05] Activate IoT Monitoring upon start"""
        # NOTE (porting 19.0 -> 18.0): Odoo 18 core mrp.production has NO
        # _hook_post_start/_hook_pre_done hooks at all (no definition, no
        # caller) — super() would raise AttributeError. Guard defensively
        # (pattern PORTING.md §5/§14: super() without a base).
        try:
            super()._hook_post_start()
        except AttributeError:
            pass
        # If devices are linked, put them in high-frequency monitoring mode
        if hasattr(self, 'iot_device_ids') and self.iot_device_ids:
            for device in self.iot_device_ids:
                if hasattr(device, 'action_activate_monitoring'):
                    device.action_activate_monitoring(context={'intervention_id': self.id})

            # Check connectivity
            # NOTE (porting): field is 'connection_status' in agri_iot
            # (values online/offline/error), not 'connection_state'.
            all_connected = all(d.connection_status == 'online' for d in self.iot_device_ids)
            # NOTE (porting): 'iot_status' on mrp.production comes from the
            # farm_operation mixin and only allows
            # normal/monitoring/warning/critical — the upstream values
            # 'connected'/'offline'/'none' are rejected by the selection
            # (ValueError). Map them to the closest valid values.
            self.write({'iot_status': 'monitoring' if all_connected else 'warning'})
            self.message_post(body=_("IOT SYNC: Monitoring activated for %s devices.") % len(self.iot_device_ids))
        else:
            self.write({'iot_status': 'normal'})

    def _hook_pre_done(self):
        """[US-IOT-06] Deactivate IoT Monitoring before completion"""
        # NOTE (porting 19.0 -> 18.0): see _hook_post_start — no such hook
        # in Odoo 18 core; guard super().
        try:
            super()._hook_pre_done()
        except AttributeError:
            pass
        if hasattr(self, 'iot_device_ids') and self.iot_device_ids:
            for device in self.iot_device_ids:
                if hasattr(device, 'action_deactivate_monitoring'):
                    device.action_deactivate_monitoring()
            self.message_post(body=_("IOT SYNC: Monitoring deactivated."))
            self.write({'iot_status': 'normal'})
