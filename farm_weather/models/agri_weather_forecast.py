from odoo import models, fields, api, _
import requests
import logging

_logger = logging.getLogger(__name__)

class AgriWeatherForecast(models.Model):
    _name = 'agri.weather.forecast'
    _description = 'Agricultural Weather Forecast'
    _order = 'date asc'

    date = fields.Date("Date", required=True)
    location_id = fields.Many2one('farm.location', string="Farm Location", domain=[('is_land_parcel', '=', True)])

    temp_max = fields.Float("Max Temp (°C)")
    temp_min = fields.Float("Min Temp (°C)")
    precipitation = fields.Float("Precipitation (mm)")
    condition = fields.Char("Condition") # e.g., Sunny, Cloudy, Rainy
    icon = fields.Char("Icon ID")

    humidity = fields.Float("Humidity (%)")
    wind_speed = fields.Float("Wind Speed (m/s)")

    is_warning = fields.Boolean("Weather Warning", compute='_compute_warning', store=True, precompute=True)
    # NOTE (B22, 10 Nov 2026): warning_type MUST be a computed field sharing
    # _compute_warning. As a plain Selection field, the assignment
    # `record.warning_type = w_type` inside the compute was silently dropped
    # on create (precompute only covered is_warning), so forecasts created
    # via ORM / cron fetch got warning_type=False until a second write --
    # and _trigger_disaster_alert never fired for fetched forecasts.
    # Thresholds (unchanged, upstream order frost > storm > heat > wind):
    # temp_min < 0 frost; precipitation > 50 storm; temp_max > 38 heat;
    # wind_speed > 15 wind. A record can only carry one type.
    warning_type = fields.Selection([
        ('frost', 'Frost Risk'),
        ('storm', 'Heavy Rain/Storm'),
        ('heat', 'Extreme Heat'),
        ('wind', 'Strong Wind')
    ], string="Warning Type", compute='_compute_warning', store=True, precompute=True)

    @api.depends('temp_min', 'precipitation', 'temp_max', 'wind_speed')
    def _compute_warning(self):
        for record in self:
            warning = False
            w_type = False
            if record.temp_min < 0:
                warning = True
                w_type = 'frost'
            elif record.precipitation > 50:
                warning = True
                w_type = 'storm'
            elif record.temp_max > 38:
                warning = True
                w_type = 'heat'
            elif record.wind_speed > 15:
                warning = True
                w_type = 'wind'

            record.is_warning = warning
            record.warning_type = w_type

    @api.model
    def action_fetch_weather_all_locations(self):
        """ Cron Job to fetch weather for all locations with GIS coordinates """
        locations = self.env['farm.location'].search([
            ('is_land_parcel', '=', True),
            ('gps_lat', '!=', 0),
            ('gps_lng', '!=', 0)
        ])
        for loc in locations:
            self._fetch_weather_for_location(loc)

    def _trigger_disaster_alert(self):
        """Trigger a disaster alert [US-040-10].

        Always creates a mail activity on the parcel when this forecast
        carries a warning. The disaster-incident draft is only created
        when farm_disaster_risk is installed: model farm.disaster.incident
        is NOT part of this module's dependencies, so an unguarded lookup
        would raise KeyError and break the whole weather fetch (and the
        cron) on a database without that module.
        """
        if self.is_warning and self.warning_type in ['storm', 'frost', 'heat']:
            # 1. Check whether an active alert already exists
            # NOTE: searching on res_model is VALID here -- mail.activity
            # res_model is a stored related field (related='res_model_id.model',
            # store=True, odoo/addons/mail/models/mail_activity.py:64-66) and
            # core itself searches ('res_model', '=', model) there (line 54).
            existing_activity = self.env['mail.activity'].search([
                ('res_model', '=', 'farm.location'),
                ('res_id', '=', self.location_id.id),
                ('summary', 'like', 'Weather Alert'),
                ('date_deadline', '>=', fields.Date.today())
            ], limit=1)

            if not existing_activity:
                # 2. Create the alert activity (Mail Activity)
                # NOTE (B23, 10 Nov 2026): mail.activity.res_model is a
                # READONLY related field (related='res_model_id.model') --
                # passing 'res_model' in create() is silently ignored and
                # leaves required res_model_id NULL -> NotNullViolation.
                # Must pass res_model_id (int) explicitly, same pattern as
                # farm_iot/models/farm_event_correlation.py:114 and
                # farm_core/models/agri_mixins.py:311. farm.location inherits
                # mail.thread via stock.location (farm_core land_location.py),
                # so message_subscribe() exists -- no B21-style crash.
                self.env['mail.activity'].create({
                    'res_model_id': self.env['ir.model']._get('farm.location').id,
                    'res_id': self.location_id.id,
                    'activity_type_id': self.env.ref('mail.mail_activity_data_warning').id,
                    'summary': _('Weather Alert: %s predicted on %s') % (self.warning_type, self.date),
                    'note': _('Please check the parcel and activate protection measures if necessary.'),
                    'user_id': self.env.user.id,
                })

            # 3. Auto-generate a disaster incident draft (Farm Disaster Incident)
            # Skipped silently when farm_disaster_risk is not installed.
            if 'farm.disaster.incident' in self.env:
                # Check whether a matching disaster incident draft already exists
                existing_incident = self.env['farm.disaster.incident'].search([
                    ('disaster_type', '=', self.warning_type),
                    ('date_start', '=', self.date),
                    ('affected_location_ids', 'in', self.location_id.id)
                ], limit=1)

                if not existing_incident:
                    disaster_type_map = {
                        'storm': 'gale',  # storm/gale
                        'frost': 'frost',
                        'heat': 'high_temp'
                    }
                    self.env['farm.disaster.incident'].create({
                        'name': _('Weather Disaster: %s on %s for %s') % (self.warning_type, self.date, self.location_id.name),
                        'disaster_type': disaster_type_map.get(self.warning_type, 'other'),
                        'date_start': self.date,
                        'affected_location_ids': [(4, self.location_id.id)],
                        'description': _('Auto-generated from weather forecast: %s predicted.') % self.warning_type,
                        'intensity': 'moderate',  # default moderate, adjust manually later
                    })

    def _fetch_weather_for_location(self, location):
        """
        Call external Weather API (Example: OpenWeatherMap OneCall API)
        Note: In real production, use the configured API Key.
        """
        api_key = self.env['ir.config_parameter'].sudo().get_param('farm_weather.api_key')
        if not api_key:
            _logger.warning("Weather API Key not configured.")
            return

        url = f"https://api.openweathermap.org/data/2.5/forecast?lat={location.gps_lat}&lon={location.gps_lng}&appid={api_key}&units=metric"

        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Process 5-day / 3-hour forecast (simplified to daily for the model)
                forecasts_by_date = {}
                for entry in data.get('list', []):
                    dt = fields.Date.to_date(entry['dt_txt'])
                    if dt not in forecasts_by_date:
                        forecasts_by_date[dt] = {
                            'temp_max': entry['main']['temp_max'],
                            'temp_min': entry['main']['temp_min'],
                            'precipitation': entry.get('rain', {}).get('3h', 0) + entry.get('snow', {}).get('3h', 0),
                            'condition': entry['weather'][0]['main'],
                            'icon': entry['weather'][0]['icon'],
                            'humidity': entry['main']['humidity'],
                            'wind_speed': entry['wind']['speed'],
                        }
                    else:
                        f = forecasts_by_date[dt]
                        f['temp_max'] = max(f['temp_max'], entry['main']['temp_max'])
                        f['temp_min'] = min(f['temp_min'], entry['main']['temp_min'])
                        f['precipitation'] += entry.get('rain', {}).get('3h', 0) + entry.get('snow', {}).get('3h', 0)

                # Update or create records
                for dt, vals in forecasts_by_date.items():
                    existing = self.search([('date', '=', dt), ('location_id', '=', location.id)], limit=1)
                    if existing:
                        existing.write(vals)
                        existing._trigger_disaster_alert()
                    else:
                        vals.update({'date': dt, 'location_id': location.id})
                        rec = self.create(vals)
                        rec._trigger_disaster_alert()
            else:
                _logger.error(f"Weather API Error: {response.status_code} - {response.text}")
        except Exception as e:
            _logger.error(f"Weather Fetch Exception: {str(e)}")

    @api.model
    def get_context_weather(self, res_model, res_id):
        """
        Get the weather information for the context of the current record.
        """
        if not res_model or not res_id:
            return None

        location = False
        if res_model == 'mrp.production':
            mo = self.env['mrp.production'].browse(res_id)
            location = mo.agri_task_id.land_parcel_id
        elif res_model == 'project.task':
            task = self.env['project.task'].browse(res_id)
            location = task.land_parcel_id
        elif res_model == 'farm.location':
            location = self.env['farm.location'].browse(res_id)

        if not location or not location.is_land_parcel:
            return None

        # Get today's forecast
        forecast = self.search([
            ('location_id', '=', location.id),
            ('date', '=', fields.Date.today())
        ], limit=1)

        if not forecast:
            return None

        return {
            'temp_max': forecast.temp_max,
            'temp_min': forecast.temp_min,
            'condition': forecast.condition,
            'icon': self._map_icon_to_fa(forecast.icon),
            'humidity': forecast.humidity,
            'wind_speed': forecast.wind_speed,
            'is_warning': forecast.is_warning,
            'warning_type': forecast.warning_type,
        }

    def _map_icon_to_fa(self, icon_id):
        """Map an OpenWeatherMap icon ID to FontAwesome."""
        mapping = {
            '01d': 'fa-sun-o',
            '01n': 'fa-moon-o',
            '02d': 'fa-cloud',
            '02n': 'fa-cloud',
            '03d': 'fa-cloud',
            '03n': 'fa-cloud',
            '04d': 'fa-cloud',
            '04n': 'fa-cloud',
            '09d': 'fa-tint',
            '10d': 'fa-umbrella',
            '11d': 'fa-bolt',
            '13d': 'fa-snowflake-o',
            '50d': 'fa-bars',
        }
        return mapping.get(icon_id, 'fa-sun-o')