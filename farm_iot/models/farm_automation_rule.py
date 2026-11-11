import logging

from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class FarmAutomationRule(models.Model):
    _name = 'farm.automation.rule'
    _description = 'Farm IOT Automation Rule'

    name = fields.Char("Rule Name", required=True)
    active = fields.Boolean(default=True)

    sensor_type = fields.Selection([
        ('temperature', 'Temperature'),
        ('ph', 'pH Level'),
        ('dissolved_oxygen', 'Dissolved Oxygen'),
    ], string="Trigger Sensor", required=True)

    operator = fields.Selection([
        ('<', 'Less Than'),
        ('>', 'Greater Than')
    ], string="Operator", default='<', required=True)

    threshold = fields.Float("Threshold", required=True)

    target_device_id = fields.Many2one('iiot.device', string="Action Device", required=True)
    command_to_send = fields.Char("Command/Action", default='power_on', required=True)
    command_params = fields.Char("Params (JSON)", default='{"state": "on"}')

    def _gateway_label(self, device):
        """Best-effort label of the gateway that would handle a command
        for ``device`` (same lookup as ``iiot.device.send_command``:
        gateway managing the device, else first online gateway).

        Only used for log messages — never raises.
        """
        try:
            gateway = self.env['iiot.gateway'].sudo().search(
                [('device_ids', 'in', device.id)], limit=1)
            if not gateway:
                gateway = self.env['iiot.gateway'].sudo().search(
                    [('state', '=', 'online')], limit=1)
            if gateway:
                return _("gateway '%s' (%s, state %s)") % (
                    gateway.name, gateway.url or '-', gateway.state)
        except Exception:
            pass
        return _("no gateway found")

    def check_and_trigger(self, telemetry):
        """Check the reading and trigger the rule.

        Returns True when the rule triggered and the command was
        dispatched, False otherwise (sensor mismatch, rule not
        triggered, or command failed).

        NOTE (B20, 10 Nov 2026): sending the command MUST NOT raise.
        ``check_and_trigger`` is called from ``iiot.telemetry.create()``
        (``farm_iot_telemetry`` / ``agri_telemetry``) without a guard,
        so any exception here used to roll back the whole telemetry
        create and the reading was lost whenever the gateway was down.
        A failed command is now logged + noted in the production
        chatter, and the telemetry record is left intact.
        """
        self.ensure_one()
        if telemetry.sensor_type != self.sensor_type:
            return False

        triggered = False
        if self.operator == '<' and telemetry.value < self.threshold:
            triggered = True
        elif self.operator == '>' and telemetry.value > self.threshold:
            triggered = True

        if triggered:
            import json
            try:
                params = json.loads(self.command_params or '{}')
            except (ValueError, TypeError):
                # Bad params must not kill the telemetry either; fall
                # back to no params and record the problem.
                _logger.warning(
                    "AUTOMATION (B20): Rule '%s' has invalid command_params "
                    "%r — sending command '%s' to device '%s' without params.",
                    self.name, self.command_params,
                    self.command_to_send, self.target_device_id.name)
                params = {}
            try:
                self.target_device_id.send_command(self.command_to_send, **params)
            except Exception as exc:
                # B20: gateway down / unreachable / rejected — log the
                # failure (rule + device + gateway) and let the
                # telemetry flow continue. The reading itself was
                # already stored by the caller; do NOT re-raise.
                _logger.warning(
                    "AUTOMATION (B20): Rule '%s' triggered (%s %s %s) but "
                    "command '%s' FAILED for device '%s' via %s: %s. "
                    "Telemetry record kept; command NOT delivered.",
                    self.name, self.sensor_type, self.operator,
                    self.threshold, self.command_to_send,
                    self.target_device_id.name,
                    self._gateway_label(self.target_device_id), exc)
                # Visible trace in the production thread (best effort —
                # a chatter failure must not roll back telemetry either).
                if telemetry.production_id:
                    try:
                        telemetry.production_id.message_post(
                            body=_("AUTOMATION: Rule '%s' triggered but command "
                                   "'%s' FAILED for %s (%s %s %s): %s. "
                                   "Telemetry kept; command not delivered.") % (
                                self.name, self.command_to_send,
                                self.target_device_id.name, self.sensor_type,
                                self.operator, self.threshold, exc)
                        )
                    except Exception:
                        _logger.warning(
                            "AUTOMATION (B20): Rule '%s' — could not post "
                            "the failed-command note to production %s.",
                            self.name, telemetry.production_id.display_name)
                return False

            # Log the automatic trigger in the parcel message thread
            if telemetry.production_id:
                try:
                    telemetry.production_id.message_post(
                        body=_("AUTOMATION: Rule '%s' triggered. Command '%s' sent to %s because %s was %s %s.") % (
                            self.name, self.command_to_send, self.target_device_id.name,
                            self.sensor_type, self.operator, self.threshold
                        )
                    )
                except Exception:
                    # Same invariant as above: chatter must not roll
                    # back an already-triggered telemetry record.
                    _logger.warning(
                        "AUTOMATION (B20): Rule '%s' — command '%s' sent to "
                        "device '%s' but the chatter note could not be posted "
                        "to production %s.",
                        self.name, self.command_to_send,
                        self.target_device_id.name,
                        telemetry.production_id.display_name)
            return True
        return False
