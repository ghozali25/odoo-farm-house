from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class WorkspaceCustomization(models.Model):
    """
    Workspace Customization [US-039-04]
    """
    _name = 'workspace.customization'
    _description = 'Personalized Workspace Customization'

    name = fields.Char('Customization Name', required=True, translate=True)
    user_id = fields.Many2one('res.users', string='User', required=True, default=lambda self: self.env.user)
    dashboard_widgets = fields.Text('Dashboard Widgets', help='JSON configuration of dashboard widgets')
    theme_preference = fields.Selection([
        ('light', 'Light Theme'),
        ('dark', 'Dark Theme'),
        ('eye_care', 'Eye Care Mode'),
        ('high_contrast', 'High Contrast'),
    ], string='Theme Preference', default='light')
    quick_actions = fields.Text('Quick Actions', help='JSON configuration of quick action bar')
    language_preference = fields.Char('Language Preference', default='en_US')
    timezone_preference = fields.Char('Timezone Preference', default='UTC')
    font_size = fields.Selection([
        ('small', 'Small'),
        ('normal', 'Normal'),
        ('large', 'Large'),
        ('extra_large', 'Extra Large'),
    ], string='Font Size', default='normal')
    layout_preference = fields.Text('Layout Preferences', help='JSON configuration of UI layouts')
    is_active = fields.Boolean('Is Active', default=True)
    last_updated = fields.Datetime('Last Updated', default=fields.Datetime.now)

    def save_customization(self):
        """Save the user customization settings."""
        for customization in self:
            customization.last_updated = fields.Datetime.now()
            # TODO: implement saving the customization settings.
            pass

    @api.model
    def get_user_customization(self, user_id=None):
        """Fetch the user customization settings."""
        user_id = user_id or self.env.uid
        customization = self.search([('user_id', '=', user_id)], limit=1)
        if customization:
            return {
                'theme': customization.theme_preference,
                'font_size': customization.font_size,
                'dashboard_widgets': customization.dashboard_widgets,
                'quick_actions': customization.quick_actions,
                'language': customization.language_preference,
                'timezone': customization.timezone_preference,
            }
        return {
            'theme': 'light',
            'font_size': 'normal',
            'dashboard_widgets': '{}',
            'quick_actions': '[]',
            'language': 'en_US',
            'timezone': 'UTC',
        }