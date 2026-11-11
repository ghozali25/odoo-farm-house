# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import uuid
import json
import re
import requests
from datetime import datetime
# For logger - needed for error logging in process_telemetry_data
import logging
_logger = logging.getLogger(__name__)

class IiotDevice(models.Model):
    _name = 'iiot.device'
    _description = 'Industrial IoT Device'
    _order = 'serial_number'
    # NOTE (18.0 port, batch 4, fix B21): 'mail.thread' added —
    # farm_event_correlation._trigger_action() (farm_iot) creates a
    # mail.activity with res_model_id = iiot.device, and
    # mail.activity.create() calls message_subscribe() on the target
    # record; farm_iot_telemetry / agri_telemetry also call
    # device.message_post(). Without mail.thread this model had no
    # such methods (AttributeError on every triggered correlation,
    # rolling back the whole iiot.telemetry create). Same pattern as
    # fix B13 (agri.isl.aquaculture.task). mail.activity.mixin is NOT
    # added: no code schedules activities on the device itself
    # (activity_schedule / activity_ids are never used on iiot.device)
    # and no chatter is needed in the view — activities can be created
    # without it. All mail.thread fields are computed / relational, so
    # no new column on iiot_device is needed (verified against Odoo 18
    # mail_thread.py: no store=True field on mail.thread itself;
    # message_main_attachment_id lives on the separate mixin
    # mail.thread.main.attachment, which mail.thread does NOT inherit).
    _inherit = ['mail.thread']

    name = fields.Char('Name', compute='_compute_name', store=True, precompute=True)
    serial_number = fields.Char('Serial Number', required=True, copy=False, help='Physical serial number (unique, index=True)')
    # NOTE (18.0 port, batch 4, fix B15): required=True removed.
    # The web client blocks Save when a required field is empty, so
    # the auto-fill in create() below never ran and the form failed
    # silently (URL stayed /new, no record, no invalid message).
    # device_id is now auto-derived from serial_number in create()
    # (sanitised + made unique), which is the same value the UI
    # used to require typing by hand. A static default= was NOT used:
    # it cannot be unique per record, and a uuid default would break
    # the serial-derived naming the topics/tests rely on.
    device_id = fields.Char('Device ID', copy=False, help='Logical ID for Topics')
    profile_id = fields.Many2one(
        'iiot.device.profile',
        'Communication Profile',
        required=True,
        help='Associated communication profile'
    )
    business_ref = fields.Reference(
        selection='_get_business_models',
        string='Business Reference',
        help='Associated business entity (equipment/workcenter/location)'
    )
    config_token = fields.Char('Config Token', copy=False, help='One-time configuration download token')
    firmware_version = fields.Char('Firmware Version', help='Current firmware version')

    # Physical Topology [ISA-95 L2/L1]
    parent_id = fields.Many2one('iiot.device', string='Parent Device', help='Physical upstream gateway or controller', ondelete='restrict')
    child_ids = fields.One2many('iiot.device', 'parent_id', string='Sub-devices')
    physical_level = fields.Selection([
        ('gateway', 'Gateway/Edge Server'),
        ('controller', 'Controller/PLC'),
        ('node', 'Sensor Node'),
        ('sensor', 'Sub-sensor/Module')
    ], string='Physical Level', default='node')

    # Device shadow [US-TECH-04-01]
    shadow_state = fields.Text('Device Shadow', help='Last known state (JSON)')
    shadow_update = fields.Datetime('Shadow Last Update')

    # Video stream integration [US-039-01]
    is_camera = fields.Boolean("Is Camera", default=False)
    live_stream_url = fields.Char("Live Stream URL", help="HLS/HTTP/RTSP stream URL for the camera")

    # Status fields
    is_active = fields.Boolean('Active', default=True)
    last_telemetry = fields.Datetime('Last Telemetry')
    last_command = fields.Datetime('Last Command')
    connection_status = fields.Selection([
        ('offline', 'Offline'),
        ('online', 'Online'),
        ('error', 'Error')
    ], string='Connection Status', default='offline')

    # Tracking
    created_date = fields.Datetime('Created Date', default=fields.Datetime.now)
    last_update = fields.Datetime('Last Update', default=fields.Datetime.now)

    # Odoo 18: the Constraint() declarative API (Odoo 19) does not exist;
    # use the classic _sql_constraints list with the same SQL + message.
    _sql_constraints = [
        ('serial_number_uniq', 'UNIQUE(serial_number)',
         'Serial number must be unique!'),
        ('device_id_uniq', 'UNIQUE(device_id)',
         'Device ID must be unique!'),
    ]

    @api.model
    def _get_business_models(self):
        # Return a list of models that can be referenced
        # This should be extended by business modules (e.g., via _inherit)
        return []

    @api.depends('serial_number', 'device_id')
    def _compute_name(self):
        for device in self:
            device.name = f"{device.serial_number} ({device.device_id})"

    @api.constrains('device_id')
    def _check_device_id_format(self):
        for record in self:
            # Guard (fix B15): device_id is no longer required, so it
            # may be falsy on a transient write; only validate a value
            # that is actually present.
            if record.device_id and not re.match(r'^[a-zA-Z0-9_-]+$', record.device_id):
                raise ValidationError(_("Device ID can only contain letters, numbers, underscores and hyphens"))

    def action_generate_config_token(self):
        """Generate pairing token"""
        for device in self:
            device.config_token = str(uuid.uuid4())
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Configuration download token generated'),
                'type': 'success',
                'sticky': False,
            }
        }

    def get_topic_map(self):
        """Generate complete Topic list"""
        self.ensure_one()
        if not self.profile_id:
            return {}

        profile = self.profile_id
        device_id = self.device_id

        return {
            'telemetry': profile.telemetry_topic_template.format(device=device_id),
            'command': profile.command_topic_template.format(device=device_id),
            'ota_notify': profile.ota_notify_topic_template.format(device=device_id),
            'ota_status': profile.ota_status_topic_template.format(device=device_id),
        }

    def send_command(self, action=None, **params):
        """Send command via gateway.

        NOTE (Odoo 18 port): UI buttons (type="object") call the method
        without arguments, so the action may also arrive via the button
        context (``{'action': ..., 'params': {...}}``). The controller
        still calls this method with explicit arguments.

        NOTE (B26): ``context['params']`` is NOT taken raw — the Odoo
        18 web client itself puts its own action-manager params into
        the call context (``{'debug': 1, 'resId': 1, 'action': <id>,
        'actionStack': [...]}``) whenever a button carries no
        ``'params'`` of its own (e.g. the Reset buttons, context
        ``{'action': 'reset'}`` only). That client dict contains the
        key ``'action'``, so ``**params`` would collide with the
        ``action`` argument (``TypeError: got multiple values for
        argument 'action'``). Only a dict WITHOUT the client keys
        (``'action'``, ``'debug'``, ``'resId'``, ``'actionStack'``)
        is a genuine command-params dict and is used; otherwise the
        ``params`` argument (usually ``{}``) is kept.
        """
        self.ensure_one()
        if action is None:
            action = self.env.context.get('action')
            ctx_params = self.env.context.get('params')
            if isinstance(ctx_params, dict) and not any(
                k in ctx_params
                for k in ('action', 'debug', 'resId', 'actionStack')
            ):
                params = ctx_params or params
        if not action:
            raise UserError(_("No command action specified"))

        if not self.profile_id:
            raise UserError(_("Device not associated with communication profile"))

        # Find gateway managing this device
        gateway = self.env['iiot.gateway'].sudo().search([('device_ids', 'in', self.id)], limit=1)
        
        # Fallback to the first online gateway if not specifically assigned
        if not gateway:
            gateway = self.env['iiot.gateway'].sudo().search([('state', '=', 'online')], limit=1)

        if not gateway or not gateway.url:
            raise UserError(_("No online IoT Gateway found to handle this command"))

        try:
            # Use the unified webhook endpoint on the bridge
            webhook_url = f"{gateway.url.rstrip('/')}/api/v1/webhook"
            
            response = requests.post(
                webhook_url,
                json={
                    'event': 'command',
                    'payload': {
                        'device_id': self.device_id,
                        'action': action,
                        'params': params
                    }
                },
                timeout=10
            )
            
            if response.status_code == 200 and response.json().get('status') == 'success':
                self.last_command = fields.Datetime.now()
                return True
            else:
                error_detail = response.text
                try:
                    error_detail = response.json().get('error', response.text)
                except:
                    pass
                raise UserError(_("Gateway rejected command: %s") % error_detail)
                
        except Exception as e:
            raise UserError(_("Error occurred while sending command to gateway: %s") % str(e))

    def process_telemetry_data(self, telemetry_data):
        """Process incoming telemetry data and update Device Shadow"""
        self.ensure_one()

        # Update last telemetry time
        self.last_telemetry = fields.Datetime.now()
        self.connection_status = 'online'

        # Update Device Shadow [US-TECH-04-01]
        try:
            current_shadow = json.loads(self.shadow_state) if self.shadow_state else {}
            # Merge new telemetry into shadow
            if isinstance(telemetry_data, dict):
                current_shadow.update(telemetry_data)
                self.shadow_state = json.dumps(current_shadow)
                self.shadow_update = fields.Datetime.now()
        except Exception as e:
            _logger.error(f"Failed to update shadow for {self.device_id}: {str(e)}")

        # Process according to telemetry rules
        for rule in self.profile_id.iiot_telemetry_rule_ids:
            if not rule.active:
                continue

            try:
                # Extract value using JSONPath
                import jsonpath_ng
                jsonpath_expr = jsonpath_ng.parse(rule.json_path)
                matches = [match.value for match in jsonpath_expr.find(telemetry_data)]

                if not matches:
                    continue

                value = matches[0]  # Take the first match

                # Find target record
                domain = rule.evaluate_domain(self.id)
                target_model = self.env[rule.target_model]
                target_records = target_model.search(domain)

                if target_records:
                    # Update the field with the extracted value
                    for target_record in target_records:
                        target_record.write({rule.target_field: value})

            except Exception as e:
                # Log error but continue processing other rules
                _logger.error(f"Error processing telemetry rule {rule.name} for device {self.device_id}: {str(e)}")

    def write(self, vals):
        vals['last_update'] = fields.Datetime.now()
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        if isinstance(vals_list, dict):
            vals_list = [vals_list]
        # Candidates already handed out in this same batch, so two
        # serials that sanitise identically cannot collide with each
        # other before either row exists in the DB.
        seen_device_ids = set()
        for vals in vals_list:
            if isinstance(vals, list):
                vals = vals[0]  # Just in case Odoo passes a nested list
            # Fix B15: the web client sends an empty Char as False, so
            # 'device_id' not in vals is NOT enough — treat any falsy
            # value as missing and derive it from the serial number.
            # The old code only replaced ' ' and '-', which could still
            # produce a value rejected by _check_device_id_format
            # (e.g. serial "SN.001" -> "sn.001"); sanitise every
            # disallowed character instead. serial_number is UNIQUE,
            # but two different serials can sanitise to the same id
            # ("A-B" vs "A B"), so append -2, -3, ... until unique.
            if not vals.get('device_id'):
                serial = vals.get('serial_number') or 'device'
                base = re.sub(r'[^a-zA-Z0-9_-]', '_', serial).lower() or 'device'
                candidate = base
                suffix = 2
                while (candidate in seen_device_ids
                       or self.search_count([('device_id', '=', candidate)])):
                    candidate = f"{base}-{suffix}"
                    suffix += 1
                vals['device_id'] = candidate
            seen_device_ids.add(vals['device_id'])
            if not vals.get('config_token'):
                vals['config_token'] = str(uuid.uuid4())
        return super().create(vals_list)

