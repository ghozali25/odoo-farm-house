from odoo import models, fields, api
import json

class IiotDevice(models.Model):
    _inherit = 'iiot.device'

    # Geofence safety [US-053-01] - implemented at the business integration layer
    geofence_id = fields.Many2one(
        'agri.geospatial.geofence', 
        string="Safety Geofence", 
        help="Assigned virtual fence for boundary monitoring."
    )

    # Business integration fields: command log and alerts [US-053-01, US-037-06]
    command_log_ids = fields.One2many('farm.command.log', 'device_id', string="Command History")
    active_alert_ids = fields.One2many(
        'mail.activity', 
        'res_id', 
        domain=[('res_model', '=', 'iiot.device'), ('state', '!=', 'done')], 
        string="Active Alerts"
    )

    def send_command(self, action=None, **params):
        """ Overridden to add business logging in farm_iot layer.

        NOTE (B25): signature mirrors the base
        ``agri_iot.models.iiot_device.IiotDevice.send_command`` —
        ``action`` defaults to ``None`` so UI buttons (type="object")
        that call this method without arguments still work: the base
        resolves the action (and params) from the button context
        (``{'action': ..., 'params': {...}}``) and raises UserError
        "No command action specified" when none is given. The
        previous signature (``action`` required) shadowed the base
        and broke every device button with
        ``TypeError: send_command() missing 1 required positional
        argument: 'action'``. The final action is resolved from the
        context BEFORE logging so ``farm.command.log`` never records
        ``None``.

        NOTE (B26): ``context['params']`` is NOT taken raw. The Odoo
        18 web client itself puts its own action-manager params into
        the call context (``{'debug': 1, 'resId': 1, 'action': <id>,
        'actionStack': [...]}``) whenever a button carries no
        ``'params'`` of its own — which is exactly the Reset / Send
        Reset Command buttons (context ``{'action': 'reset'}`` only).
        That client dict contains the key ``'action'``, so passing it
        as ``**params`` to ``super().send_command(action, **params)``
        raised ``TypeError: got multiple values for argument
        'action'``. Only a dict WITHOUT the client keys
        (``'action'``, ``'debug'``, ``'resId'``, ``'actionStack'``)
        is a genuine command-params dict and is used; otherwise the
        ``params`` argument (usually ``{}``) is kept.
        """
        # Resolve the final action/params the same way the base does,
        # so the audit log records what was actually sent.
        if action is None:
            action = self.env.context.get('action')
            ctx_params = self.env.context.get('params')
            if isinstance(ctx_params, dict) and not any(
                k in ctx_params
                for k in ('action', 'debug', 'resId', 'actionStack')
            ):
                params = ctx_params or params
        # Trigger actual hardware command (base resolves from context
        # again if needed and raises UserError when no action at all)
        res = super(IiotDevice, self).send_command(action, **params)

        # Log command attempt
        log_vals = {
            'device_id': self.id,
            'command': action,
            'payload': json.dumps(params) if params else '{}',
            'status': 'dispatched' if res else 'failed',
            'res_model': self._context.get('active_model'),
            'res_id': self._context.get('active_id'),
        }
        return self.env['farm.command.log'].create(log_vals)
