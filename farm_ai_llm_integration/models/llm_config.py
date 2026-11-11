# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class AgriAiLlmConfiguration(models.Model):
    """
    Configuration for LLM providers - implements the AI Configuration interface
    """
    _name = 'agri.ai.llm.configuration'
    _description = 'LLM Provider Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    # Use delegation inheritance to properly link to the base interface
    _inherits = {'agri.ai.configuration': 'ai_config_id'}

    # Foreign key to the base agri.ai.configuration
    ai_config_id = fields.Many2one('agri.ai.configuration', string='AI Configuration', required=True, ondelete='cascade')

    # Provider-specific fields (in addition to inherited ai.configuration fields)
    provider = fields.Selection([
        ('openai', 'OpenAI'),
        ('anthropic', 'Anthropic'),
        ('google', 'Google'),
        ('huggingface', 'Hugging Face'),
        ('custom', 'Custom API'),
        ('ollama', 'Ollama'),
    ], string='LLM Provider', required=True)

    # Batch 7 (king, 11 Nov 2026): the LLM API goes through 9Router
    # (Ali Connection) — https://9router-go.hiddenlab.me/v1 — which is
    # OpenAI-compatible. Upstream ``llm_service.py`` reads
    # ``config_id.api_base_url`` in EVERY provider call, but NO model
    # defined that field (the parent only has ``base_url``, shown in the
    # form but never read by the service) — every LLM call crashed with
    # AttributeError before any request was sent. This field is the one
    # the service actually uses; its default is the 9Router gateway, so
    # provider 'openai' works against the gateway out of the box. The API
    # KEY is never stored in code: it is entered by king in the config
    # record (``api_key`` field, password widget) only.
    api_base_url = fields.Char(
        'API Base URL', default='https://9router-go.hiddenlab.me/v1',
        help='OpenAI-compatible API base URL used for all LLM calls. '
             'Default: 9Router (Ali Connection) gateway '
             'https://9router-go.hiddenlab.me/v1 — override per provider '
             'when needed (e.g. api.anthropic.com for Anthropic).')

    @api.onchange('provider')
    def _onchange_provider_base_url(self):
        """Keep the base URL consistent with the provider: switching away
        from OpenAI clears the gateway default; switching back restores
        it when the field is empty."""
        gateway = 'https://9router-go.hiddenlab.me/v1'
        defaults = {
            'anthropic': 'https://api.anthropic.com/v1',
            'google': 'https://generativelanguage.googleapis.com/v1beta',
            'huggingface': 'https://api-inference.huggingface.co',
            'ollama': 'http://localhost:11434',
        }
        if self.provider == 'openai':
            if not self.api_base_url:
                self.api_base_url = gateway
        elif self.provider in defaults and self.api_base_url in (gateway, False, ''):
            self.api_base_url = defaults[self.provider]

    # Performance settings
    rate_limit_requests = fields.Integer('Rate Limit (requests/min)', default=60)
    rate_limit_period = fields.Integer('Rate Limit Period (seconds)', default=60)

    # Agricultural domain-specific settings
    use_agricultural_context = fields.Boolean('Use Agricultural Context', default=True,
        help="Apply agricultural domain knowledge to prompts")
    temperature = fields.Float("Temperature", default=0.7)
    max_tokens = fields.Integer("Max Tokens", default=2048)
    timeout = fields.Integer("Timeout (seconds)", default=60)
    application_type = fields.Selection([
        ('general', 'General Agricultural Queries'),
        ('pest_disease', 'Pest and Disease Diagnosis'),
        ('crop_recommendation', 'Crop Recommendation'),
        ('market_prediction', 'Market Prediction'),
        ('resource_optimization', 'Resource Optimization'),
        ('risk_assessment', 'Risk Assessment'),
    ], string='Application Type', default='general')

    @api.constrains('is_default')
    def _check_only_one_default(self):
        """Ensure only one configuration is set as default"""
        active_defaults = self.search([('is_default', '=', True), ('is_active', '=', True)])
        if len(active_defaults) > 1:
            raise UserError(_("Only one LLM configuration can be set as default."))

    def test_connection(self):
        """
        Test the LLM service connection - implementation of abstract method from ai.configuration
        """
        try:
            # Try a simple test using agri.ai.llm.service
            llm_service = self.env['agri.ai.llm.service'].sudo().search([('config_id', '=', self.id)], limit=1)
            if llm_service:
                # Test with a simple prompt
                result = llm_service.call_llm("Say 'connection test' in one word", {})
                if result.get('success'):
                    _logger.info(f"LLM configuration {self.name} connection test successful")
                    return True
                else:
                    _logger.error(f"LLM configuration {self.name} connection test failed: {result.get('error')}")
                    return False
            else:
                # If no service exists, create a temporary one for testing
                service = self.env['agri.ai.llm.service'].sudo().create({
                    'name': f'Test Service for {self.name}',
                    'config_id': self.id,
                })
                result = service.call_llm("Say 'connection test' in one word", {})
                if result.get('success'):
                    _logger.info(f"LLM configuration {self.name} connection test successful")
                    # Clean up the test service
                    service.unlink()
                    return True
                else:
                    _logger.error(f"LLM configuration {self.name} connection test failed: {result.get('error')}")
                    # Clean up the test service
                    service.unlink()
                    return False
        except Exception as e:
            _logger.error(f"LLM configuration {self.name} connection test failed with exception: {str(e)}")
            return False

    def increment_request_stats(self, success=True):
        """Increment request statistics - implementation of method from ai.configuration"""
        # Call the parent implementation to maintain the base functionality
        super(LLMConfiguration, self).increment_request_stats(success=success)

    @api.model
    def get_active_default(self):
        """Get the active default LLM configuration"""
        return self.search([('is_default', '=', True), ('is_active', '=', True)], limit=1)

    def get_ai_provider_type(self):
        """
        Return the AI provider type for reflection/discovery purposes
        """
        return self.ai_provider or 'llm'