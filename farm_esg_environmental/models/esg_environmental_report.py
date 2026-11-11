from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ESGEnvironmentalReport(models.Model):
    """
    US-30-XX: ESG Environmental Report
    ESG Environmental reporting that extends base ESG functionality with environmental data
    """
    _name = 'esg.environmental.report'
    _description = 'ESG Environmental Report'
    _inherit = ['esg.performance.report']  # Inherit from base ESG performance report

    # Environmental-specific fields
    carbon_footprint_tco2e = fields.Float('Carbon Footprint (tCO2e)', help='Total carbon footprint in tons CO2 equivalent')
    water_stress_score = fields.Float('Water Stress Score (0-100)', help='Water stress score for the area')
    biodiversity_risk_score = fields.Float('Biodiversity Risk Score (0-100)', help='Risk score for biodiversity impact')

    # Environmental assessment references (extending the base assessment_ids field)
    # NOTE (B5-FIX, 10 Nov 2026): esg.performance.report defines
    # assessment_ids/target_ids with EXPLICIT relation tables
    # (esg_performance_report_esg_assessment_rel /
    # esg_performance_report_esg_target_rel). Prototype inheritance
    # (_name + _inherit) copies those fields verbatim onto this child
    # model, so the Odoo 18 registry rejects the install:
    # "Many2many fields esg.environmental.report.assessment_ids and
    # esg.performance.report.assessment_ids use the same table and
    # columns". Fix: redefine both fields here with DISTINCT relation
    # tables (same comodels, same columns, same labels).
    assessment_ids = fields.Many2many(
        'esg.assessment', 'esg_environmental_report_esg_assessment_rel',
        'report_id', 'assessment_id', string='Related Assessments')
    target_ids = fields.Many2many(
        'esg.target', 'esg_environmental_report_esg_target_rel',
        'report_id', 'target_id', string='Related Targets')
