# -*- coding: utf-8 -*-
from odoo import models, fields, api


class AgriOperationMixin(models.AbstractModel):
    """
    Abstract base model for agricultural process operations and ISA-88 routing phases.
    Provides standard GxP fields, technical manual SOPs, and critical control parameters (CCPs).
    """
    _name = 'agri.operation.mixin'
    _description = 'Agri Process Operation Shared Logic'

    # ISA-88 Agri Activity Type
    agri_activity_type = fields.Selection([
        ('feed', 'Feed'),
        ('fertilizer', 'Fertilizer'),
        ('planting', 'Planting'),
        ('protection', 'Protection'),
        ('processing', 'Processing'),
        ('cleaning', 'CIP/Cleaning')
    ], string="Agri Activity Type", help="Classify operation as a specific agricultural/processing phase.")

    # Technical instructions (SOP)
    technical_manual = fields.Html(
        string="Technical SOP",
        help="Detailed standard operating procedure for this specific process step."
    )

    # Critical Control Parameters (CCP)
    param_monitoring_required = fields.Boolean(
        string="Monitor Critical Parameters",
        default=False,
        help="Check this if the operation requires strict telemetry monitoring."
    )
    target_value = fields.Float(
        string="Target Parameter Value",
        help="Theoretical standard/target value for the critical control parameter."
    )
    tolerance_range = fields.Float(
        string="Tolerance (+/-)",
        help="Acceptable deviation above or below the target value."
    )

    # Standard GxP phases
    gxp_phase_type = fields.Selection([
        ('none', 'Standard Execution'),
        ('sterilization', 'Sterilization'),
        ('fermentation', 'Fermentation'),
        ('dehydration', 'Dehydration'),
        ('packaging', 'Packaging'),
        ('cip', 'CIP Cleaning')
    ], string="GxP Phase Type", default="none")
