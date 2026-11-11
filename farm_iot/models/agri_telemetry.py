from odoo import models, fields, api, _

class AgriTelemetry(models.Model):
    _name = 'agri.telemetry'
    _description = 'Agricultural Telemetry Data'
    _order = 'timestamp desc'

    name = fields.Char("Sensor Name", required=True)
    sensor_type = fields.Selection([
        ('temperature', 'Temperature'),
        ('ph', 'pH Level'),
        ('dissolved_oxygen', 'Dissolved Oxygen'),
        ('humidity', 'Humidity'),
        ('soil_moisture', 'Soil Moisture'),
        ('flight_altitude', 'Flight Altitude'),
        ('chemical_level', 'Chemical Level'),
        ('battery_voltage', 'Drone Battery'),
        ('micro_sensor', 'Urban Micro-sensor')
    ], string="Sensor Type", required=True)

    value = fields.Float("Value", required=True)
    timestamp = fields.Datetime("Timestamp", default=fields.Datetime.now, required=True)

    # Linked assets and tasks
    production_id = fields.Many2one('project.task', string="Production Task")
    drone_id = fields.Many2one('maintenance.equipment', string="Drone", domain="[('is_drone', '=', True)]")
    device_id = fields.Many2one('iiot.device', string="IIoT Device")

    # Linked land parcel
    land_parcel_id = fields.Many2one('farm.location', string="Land Parcel/Pond")

    # US-066-01: Adoption Linkage
    adopted_lot_id = fields.Many2one('stock.lot', string="Adopted Asset", help="If the sensor is attached to a specific adopted tree/animal")

    # GIS Snapshot [US-002-02]
    gps_lat = fields.Float("Latitude", digits=(10, 7))
    gps_lng = fields.Float("Longitude", digits=(10, 7))

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            # 1. Automation rule trigger
            rules = self.env['farm.automation.rule'].search([
                ('active', '=', True),
                ('sensor_type', '=', record.sensor_type)
            ])
            for rule in rules:
                rule.check_and_trigger(record)

            # 2. Geofence breach check [US-053-02, US-053-06]
            if record.device_id and record.device_id.geofence_id and record.gps_lat and record.gps_lng:
                fence = record.device_id.geofence_id
                is_inside = fence.is_point_inside(record.gps_lng, record.gps_lat)

                if not is_inside:
                    # Trigger breach alarm
                    self._trigger_geofence_alarm(record, fence)

            # 3. Adoption push logic [US-066-01]
            # NOTE (porting 19.0 -> 18.0): 'farm.csa.subscription' lives in
            # farm_csa, which is NOT a dependency of this module (later batch)
            # — guard with an env membership check instead of a hard env[]
            # lookup, so telemetry without an adopted lot never crashes.
            if record.adopted_lot_id and 'farm.csa.subscription' in self.env:
                # Find active subscriptions for this lot
                subs = self.env['farm.csa.subscription'].search([
                    ('adopted_lot_id', '=', record.adopted_lot_id.id),
                    ('state', '=', 'active')
                ])
                for sub in subs:
                    # Post message to customer
                    sub.message_post(body=_("STATUS UPDATE: Your adopted asset %s sent a new reading: %s %s at %s.") % (
                        record.adopted_lot_id.name, record.value, record.sensor_type, record.timestamp
                    ))
        return records

    def _trigger_geofence_alarm(self, telemetry, fence):
        """Create a breach alarm activity and push a message."""
        msg_body = _("GEOFENCE ALERT: Device %s has LEFT the assigned fence '%s' at [%s, %s]!") % (
            telemetry.device_id.name, fence.name, telemetry.gps_lat, telemetry.gps_lng
        )

        # Log the message on the device and the fence
        telemetry.device_id.message_post(body=msg_body, message_type='notification', subtype_xmlid='mail.mt_comment')
        fence.message_post(body=msg_body, message_type='notification', subtype_xmlid='mail.mt_comment')

        # Create a to-do activity
        self.env['mail.activity'].create({
            'res_id': telemetry.device_id.id,
            'res_model_id': self.env['ir.model']._get('iiot.device').id,
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'summary': _('BOUNDARY BREACH: %s') % telemetry.device_id.name,
            'note': msg_body,
            'user_id': telemetry.device_id.create_uid.id or self.env.user.id,
        })