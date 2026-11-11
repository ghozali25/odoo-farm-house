# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError
import logging
from .agri_isl_abstract_models import INDUSTRY_SELECTION

_logger = logging.getLogger(__name__)

# Data Migration & Compatibility (US-084-14)

class AgriISLMigrationUtility(models.TransientModel):
    """
    Data migration utility for ISL architecture
    Implements US-084-14: Data migration & compatibility
    """
    _name = 'agri.isl.migration.utility'
    _description = 'Agri ISL Data Migration Utility'

    industry_type = fields.Selection(
        selection=INDUSTRY_SELECTION,
        string='Industry Type', 
        default='general', 
        required=True
    )

    model_to_migrate = fields.Selection([
        ('mrp.production', 'Intervention'),
        ('mrp.bom', 'Cultivation Recipe'),
        ('mrp.workcenter', 'Facility Unit'),
        ('stock.lot', 'Stock Lot'),
        ('sale.order', 'Sale Order'),
        ('purchase.order', 'Purchase Order'),
        ('product.template', 'Product Template'),
        ('stock.picking', 'Stock Picking'),
        ('mrp.workorder', 'Operation Phase'),
    ], string='Base Model', required=True)

    confirmation = fields.Boolean('Confirm Migration')

    def action_migrate_data(self):
        """
        Migrate existing data to ISL models
        """
        if not self.confirmation:
            raise UserError(_("Please confirm the migration before proceeding"))

        base_model_name = self.model_to_migrate
        
        # 1. Get all records of the base model
        base_records = self.env[base_model_name].search([])

        # 2. Use Redirector to create ISL records (which uses Convention and Metadata)
        migrated_count = 0
        redirector = self.env['agri.isl.model.redirector']

        for base_record in base_records:
            # B9: count ONLY ISL records that are actually newly created.
            # create_isl_record() is anti-duplicate: when a counterpart
            # already exists it returns that existing record instead of
            # creating one, so a bare "if isl_record" over-counts on
            # re-runs (run 2 claimed 25 while 0 were new). Check first
            # via the redirector and count only when nothing existed
            # before AND create returned a record.
            # NOTE: get_isl_record() filters by the base record's own
            # industry_type when the base model has one, while
            # create_isl_record() stores the wizard's industry_type.
            # The pre-check therefore agrees with create() exactly in
            # the normal case (same wizard industry on re-runs, one ISL
            # model per base model); if the wizard industry differs
            # between runs AND an ISL record already exists with another
            # stored industry, the count may over-claim — but no
            # duplicate is ever created (create() itself dedupes).
            existing_isl = redirector.get_isl_record(base_model_name, base_record.id)
            # create_isl_record internally checks for existence and uses dynamic discovery
            isl_record = redirector.create_isl_record(
                base_model_name,
                base_record.id,
                industry_type=self.industry_type
            )
            if isl_record and not existing_isl:
                migrated_count += 1

        message = _("Migration completed. %d records migrated to ISL architecture.") % migrated_count
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Migration Complete'),
                'message': message,
                'type': 'success',
                # B9b: close the wizard dialog after the notification
                # is shown. Supported by the Odoo 18 web client:
                # displayNotificationAction() returns params.next and
                # the action service executes it via doAction (see
                # web/static/src/webclient/actions/client_actions.js
                # and action_service.js _executeClientAction). Core
                # Odoo 18 wizards use the same pattern, e.g.
                # account_merge_wizard / account_move_send_batch_wizard
                # ('next': {'type': 'ir.actions.act_window_close'}).
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
