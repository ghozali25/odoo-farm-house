from odoo import models, fields, api, _
from odoo.exceptions import UserError
import json

class FarmDeviceCommand(models.TransientModel):
    _name = 'farm.device.command'
    _description = 'Send Command to Farm Device'

    device_id = fields.Many2one('iiot.device', string="Target Device", required=True)
    command_type = fields.Selection([
        ('switch', 'Switch On/Off'),
        ('set_threshold', 'Set Threshold'),
        ('reboot', 'Reboot Device'),
        ('custom', 'Custom JSON')
    ], string="Command Type", default='switch', required=True)
    
    action = fields.Selection([
        ('on', 'Turn ON'),
        ('off', 'Turn OFF')
    ], string="Action")
    
    custom_params = fields.Text("Custom Parameters (JSON)")

    def action_send(self):
        self.ensure_one()
        params = {}
        if self.command_type == 'switch':
            params = {'state': self.action}
            action_name = 'power_control'
        elif self.command_type == 'reboot':
            action_name = 'reboot'
        else:
            action_name = 'custom'
            # Handle custom parameters (plain JSON parsing)
            params = json.loads(self.custom_params or '{}')

        # Call the underlying industrial_iot send capability
        try:
            import time
            start_ts = time.time()
            self.device_id.send_command(action_name, **params)
            latency = int((time.time() - start_ts) * 1000)
            
            # Record the audit log [US-006-03]
            self.env['farm.command.log'].create({
                'device_id': self.device_id.id,
                'command': action_name,
                'payload': json.dumps(params),
                'status': 'success',
                'execution_latency': latency,
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Command Sent'),
                    'message': _('Command %s has been published to %s') % (action_name, self.device_id.name),
                    'type': 'success',
                    'sticky': False,
                }
            }
        except Exception as e:
            raise UserError(_("Failed to send command: %s") % str(e))
