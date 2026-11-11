from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class FarmLot(models.Model):
    _inherit = 'stock.lot'

    # Livestock specific fields extending the base functionality - Converted to dynamic computed bridge properties
    animal_count = fields.Integer(
        string="Animal Count",
        compute='_compute_livestock_matter_properties',
        inverse='_inverse_animal_count',
        store=False
    )
    average_weight = fields.Float(
        string="Average Weight (kg)",
        compute='_compute_livestock_matter_properties',
        inverse='_inverse_average_weight',
        store=False,
        help="Compatibility Bridge: Computes weight from active matter tracking containers."
    )

    # Biological stage [US-005-04] - Converted to computed bridge
    biological_stage = fields.Selection([
        ('born', 'Born/Started'),
        ('growing', 'Growing'),
        ('breeding', 'Breeding'),
        ('lactating', 'Lactating'),
        ('finished', 'Finished'),
        ('harvested', 'Harvested')
    ], string="Biological Stage", compute='_compute_livestock_matter_properties', inverse='_inverse_biological_stage', store=False)

    def _get_matter_tracking_record(self):
        """ Return the active Matter Tracking container for this lot, if any.

        Single home of the lookup shared by the computed bridge
        (``_compute_livestock_matter_properties``) and the defensive
        inverses below: an inverse must compare the written value against
        exactly the value the compute would produce, so both sides must
        read the same record.
        """
        self.ensure_one()
        for quant in self.quant_ids.filtered(lambda q: q.package_id):
            tracking_record = self.env['stock.matter.tracking'].search(
                [('package_id', '=', quant.package_id.id)], limit=1)
            if tracking_record:
                return tracking_record
        return False

    @api.depends('quant_ids.package_id')
    def _compute_livestock_matter_properties(self):
        for lot in self:
            tracking_record = lot._get_matter_tracking_record()
            if tracking_record:
                lot.animal_count = tracking_record.animal_count or 1
                lot.average_weight = tracking_record.current_weight or 0.0
                lot.biological_stage = tracking_record.biological_stage or 'born'
            else:
                lot.animal_count = 1
                lot.average_weight = 0.0
                lot.biological_stage = 'born'

    def _inverse_animal_count(self):
        """ Defensive inverse (B10 fix, SIMULASI.md §3b).

        The field is computed, non-stored: nothing written here ever
        persists -- the compute overwrites it on the next read. A write
        can therefore only be a stray default (the web client sends
        ``animal_count=0`` for a new lot, which used to raise the Legacy
        Write Block and made creating ANY lot via UI impossible) or a
        genuine attempt to change the count. Tolerate the former, keep
        blocking the latter (the count must be changed on the Matter
        Tracking container). The written value is read FIRST: during an
        inverse the field is protected from recomputation, so the cache
        still holds the value just written.
        """
        from odoo.tools import config
        if self.env.context.get('bypass_legacy_write_block') or config.get('test_enable') or not self.env.registry.ready:
            return
        for lot in self:
            written = lot.animal_count
            tracking_record = lot._get_matter_tracking_record()
            if not tracking_record:
                # No Matter Tracking container owns this lot: there is
                # nothing to update on the tracking side, and the UI
                # default (0) must never block creating the lot.
                continue
            expected = tracking_record.animal_count or 1
            if written in (0, expected):
                continue
            raise UserError(_(
                "Legacy Write Block: Animal Count is now managed dynamically by Matter Tracking (LPN/Vessel). "
                "Please update count on the active Matter Tracking container directly."
            ))

    def _inverse_average_weight(self):
        """ Defensive inverse (B10 fix, same pattern as
        ``_inverse_animal_count``): the web client may send the displayed
        default (0.0) on create; tolerate it and any value equal to what
        the compute produces, and only block a genuine attempt to change
        the weight directly. """
        from odoo.tools import config
        if self.env.context.get('bypass_legacy_write_block') or config.get('test_enable') or not self.env.registry.ready:
            return
        for lot in self:
            written = lot.average_weight
            tracking_record = lot._get_matter_tracking_record()
            if not tracking_record:
                continue
            expected = tracking_record.current_weight or 0.0
            if written == 0.0 or abs(written - expected) < 0.000001:
                continue
            raise UserError(_(
                "Legacy Write Block: Weight is now managed dynamically by Matter Tracking (LPN/Vessel). "
                "Please update the weight on the active Matter Tracking container directly."
            ))

    def _inverse_biological_stage(self):
        """ Defensive inverse (B10 fix, same pattern as
        ``_inverse_animal_count``): tolerate an empty/default stage and
        any value equal to what the compute produces; only block a
        genuine attempt to change the stage directly. """
        from odoo.tools import config
        if self.env.context.get('bypass_legacy_write_block') or config.get('test_enable') or not self.env.registry.ready:
            return
        for lot in self:
            written = lot.biological_stage
            tracking_record = lot._get_matter_tracking_record()
            if not tracking_record:
                continue
            expected = tracking_record.biological_stage or 'born'
            if not written or written == expected:
                continue
            raise UserError(_(
                "Legacy Write Block: Biological Stage is now managed dynamically by Matter Tracking (LPN/Vessel). "
                "Please update the stage on the active Matter Tracking container directly."
            ))

    # US-003-01: Growth prediction and feeding write-off
    start_weight = fields.Float("Initial Weight (kg)")
    current_predicted_weight = fields.Float("Predicted Weight (kg)", compute='_compute_predicted_weight', store=True, precompute=True)
    average_daily_gain = fields.Float("Average Daily Gain (kg/day)", default=0.5)

    active_feeding_bom_id = fields.Many2one('mrp.bom', string="Active Feeding Recipe",
                                           domain="[('type', '=', 'normal'), ('intervention_type', '=', 'feeding')]")

    # Breeding and reproduction management
    breeding_status = fields.Selection([
        ('open', 'Open'),
        ('pregnant', 'Pregnant'),
        ('in_heat', 'In Heat'),
        ('dry', 'Dry Period'),
    ], string='Breeding Status')
    expected_farrowing_date = fields.Date('Expected Farrowing/Calving Date')
    breeding_record_ids = fields.One2many(
        'farm.breeding.record',
        'animal_id',
        string='Breeding Records'
    )
    pedigree_info = fields.Text('Pedigree Information')

    # Health management
    health_status = fields.Selection([
        ('healthy', 'Healthy'),
        ('sick', 'Sick'),
        ('quarantine', 'In Quarantine'),
        ('under_treatment', 'Under Treatment'),
    ], string='Health Status', default='healthy')
    last_vaccination_date = fields.Date('Last Vaccination Date')
    vaccination_schedule = fields.Text('Vaccination Schedule')
    medication_records = fields.Text('Medication Records')
    withdrawal_end_datetime = fields.Datetime('Withdrawal Period End')

    # Individual identification
    ear_tag_number = fields.Char('Ear Tag Number')
    animal_name = fields.Char('Animal Name')
    birth_date = fields.Date('Birth Date')
    sire_id = fields.Many2one('stock.lot', string='Sire')
    dam_id = fields.Many2one('stock.lot', string='Dam')
    breeding_record_id = fields.Many2one('farm.breeding.record', string='Breeding Record')

    # Production parameters (for dairy, egg, etc.)
    milk_yield_avg = fields.Float('Average Milk Yield (L/day)')
    lactation_number = fields.Integer('Lactation Number')
    days_in_milk = fields.Integer('Days in Milk')
    egg_production_rate = fields.Float('Egg Production Rate (%)')

    # US-065-02: High-density Precision Feeding Logic
    stocking_density = fields.Float("Stocking Density (heads/sqm)", compute='_compute_stocking_density')
    total_feed_consumed = fields.Float("Total Feed Consumed (kg)", compute='_compute_feed_stats')
    feed_conversion_ratio = fields.Float("Feed Conversion Ratio (FCR)", compute='_compute_feed_stats', help="Total Feed / Total Weight Gain")

    # US-065-03: Health Anomaly Early Warning
    health_index = fields.Float("Health Index (0-100)", default=100.0)
    is_health_anomaly = fields.Boolean("Anomaly Detected", default=False)
    last_anomaly_date = fields.Datetime("Last Anomaly Time")

    @api.depends('animal_count')
    def _compute_stocking_density(self):
        for lot in self:
            area = lot.location_id.land_area or 1.0
            lot.stocking_density = lot.animal_count / area

    def _compute_feed_stats(self):
        for lot in self:
            # Aggregate from interventions
            feeding_ops = self.env['mrp.production'].search([
                ('lot_producing_id', '=', lot.id),
                ('intervention_type', '=', 'feeding'),
                ('state', '=', 'done')
            ])
            total_feed = sum(feeding_ops.mapped('product_qty')) # Simplified
            lot.total_feed_consumed = total_feed
            
            weight_gain = (lot.current_predicted_weight - lot.start_weight) * lot.animal_count
            lot.feed_conversion_ratio = total_feed / weight_gain if weight_gain > 0 else 0.0

    def action_check_health_anomalies(self):
        """ US-065-03: Basic anomaly detection based on growth rate vs average """
        for lot in self:
            if lot.average_daily_gain < 0.1: # Threshold for anomaly
                lot.write({
                    'is_health_anomaly': True,
                    'last_anomaly_date': fields.Datetime.now()
                })
                lot.message_post(body=_("HEALTH ALERT: Growth rate for lot %s is critically low (%s kg/day)!") % (lot.name, lot.average_daily_gain))
                lot.activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary=_('Health Anomaly: %s') % lot.name,
                    note=_('Low growth rate detected. Please inspect for disease or environmental stress.'),
                    user_id=self.env.user.id
                )

    @api.depends('create_date', 'start_weight', 'average_daily_gain')
    def _compute_predicted_weight(self):
        today = fields.Date.today()
        for lot in self:
            if lot.create_date and lot.biological_stage in ['born', 'growing']:
                days_passed = (today - lot.create_date.date()).days
                lot.current_predicted_weight = lot.start_weight + (days_passed * lot.average_daily_gain)
            else:
                lot.current_predicted_weight = lot.average_weight

    def _cron_daily_feed_depletion(self):
        """ Scheduled job: auto-create a completed feeding intervention daily
        and consume stock [US-003-01].
        NOTE (18.0 port): the lot selection must NOT filter on
        ``biological_stage`` in the domain -- it is a computed, non-stored
        field and Odoo 18 raises ``ValueError: Cannot convert ... to SQL
        because it is not stored`` for such domains. The lots are fetched
        by their feeding BoM first and filtered on the stage in Python,
        which selects exactly the same records. """
        Intervention = self.env['mrp.production']
        active_lots = self.search([('active_feeding_bom_id', '!=', False)]).filtered(
            lambda lot: lot.biological_stage in ['born', 'growing'])

        for lot in active_lots:
            # Auto-create a "completed" feeding intervention
            intervention = Intervention.create({
                'product_id': lot.product_id.id,
                'bom_id': lot.active_feeding_bom_id.id,
                'product_qty': lot.animal_count, # Per-head quantity
                'intervention_type': 'feeding',
                'lot_producing_id': lot.id,
                'date_start': fields.Datetime.now(),
            })
            intervention.action_confirm()
            # Auto-confirm completion to trigger stock consumption
            intervention.button_mark_done()
            # B11 fix: mrp.bom has NO 'name' field -- the old attribute
            # access raised AttributeError and rolled the whole cron back.
            # display_name always resolves (via _rec_name / name_get).
            _logger.info("Daily feed depletion recorded for lot %s using BOM %s", lot.name, lot.active_feeding_bom_id.display_name)

    def action_record_mortality(self, qty, reason, notes=None):
        """ Record a head-count decrease and post an audit message """
        self.ensure_one()
        if qty <= 0:
            raise UserError(_("Quantity must be positive."))

        body = _("DEATH RECORDED: %s animals decreased. Reason: %s. Notes: %s") % (qty, reason, notes or "")
        self.message_post(body=body)

        # Future extension: auto-create a stock scrap (stock.scrap)
        return True

    def action_record_death(self, qty, reason, notes=None):
        """ Alias kept for the death-report wizard and the test suite, which
        both call ``action_record_death`` (upstream never defined it -- only
        ``action_record_mortality`` existed). Same behaviour, same message. """
        return self.action_record_mortality(qty, reason, notes=notes)

    def action_merge_from(self, source_group):
        """ Merge the source group into the current group """
        self.ensure_one()
        if source_group.product_id != self.product_id:
            raise UserError(_("Cannot merge groups of different products."))

        body = _("MERGE: Group %s has been merged into this group.") % source_group.name
        self.message_post(body=body)

        # Mark the source group as ended.
        # NOTE (18.0 port): upstream also wrote ``'active': False`` here,
        # but ``stock.lot`` has NO ``active`` field in Odoo 18 (verified
        # against the core source) -- the write raised ValueError on every
        # merge. The stage write runs with the module's own bypass context
        # because the ``biological_stage`` inverse blocks direct writes
        # ("Legacy Write Block"); the value itself does not persist -- the
        # computed bridge recomputes it from matter tracking -- so the
        # merge is recorded in the chatter message above, and the source
        # group keeps its computed stage. See PORTING.d/farm_livestock.md.
        source_group.with_context(bypass_legacy_write_block=True).write({'biological_stage': 'harvested'})
        return True

    def action_update_health_status(self):
        """Action to update health status"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'farm.animal.health.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': False,
            'target': 'new',
            'context': {
                'default_animal_id': self.id,
                'default_health_status': self.health_status,
            },
            'name': 'Update Health Status',
        }

    def action_record_breeding(self):
        """Action to record breeding event"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'farm.breeding.record',
            'view_mode': 'form',
            'res_id': False,
            'target': 'new',
            'context': {
                'default_animal_id': self.id,
                'default_breeding_date': fields.Date.today(),
            },
            'name': 'Record Breeding Event',
        }

    def action_calculate_expected_yield(self):
        """Calculate expected milk/egg yield based on animal characteristics"""
        for animal in self:
            if animal.biological_stage == 'lactating':
                # Calculate expected milk yield based on lactation number and days in milk
                base_yield = 20.0  # base yield in liters
                adjustment = min(animal.lactation_number * 0.5, 3.0)  # yield increases with lactation
                day_factor = max(1.0 - (animal.days_in_milk / 500), 0.7)  # yield decreases as days in milk increases
                animal.milk_yield_avg = base_yield + adjustment if animal.lactation_number > 0 else base_yield * day_factor


class FarmBreedingRecord(models.Model):
    """
    Breeding record model to track reproduction events in livestock
    """
    _name = 'farm.breeding.record'
    _description = 'Farm Breeding Record'
    _order = 'breeding_date desc'

    animal_id = fields.Many2one(
        'stock.lot',
        string='Animal',
        required=True,
        domain=[('is_animal', '=', True)]
    )
    breeding_date = fields.Date('Breeding Date', required=True, default=fields.Date.today)
    breeding_method = fields.Selection([
        ('natural', 'Natural Mating'),
        ('artificial', 'Artificial Insemination'),
        ('embryo_transfer', 'Embryo Transfer'),
    ], string='Breeding Method', default='natural')
    sire_id = fields.Many2one(
        'stock.lot',
        string='Sire Used',
        domain=[('is_animal', '=', True), ('breeding_status', '=', 'open')]
    )
    gestation_days = fields.Integer('Expected Gestation Days')
    expected_offspring_count = fields.Integer('Expected Offspring Count', default=1)
    breeding_notes = fields.Text('Breeding Notes')
    pregnancy_test_date = fields.Date('Pregnancy Test Date')
    pregnancy_test_result = fields.Boolean('Pregnancy Test Result')

    # Offspring tracking
    offspring_ids = fields.One2many(
        'stock.lot',
        'breeding_record_id',
        string='Offspring'
    )

    @api.onchange('sire_id')
    def _onchange_sire_id(self):
        """Set expected gestation days based on sire species"""
        if self.sire_id:
            # Set default gestation period based on species
            species = self.sire_id.product_id.name
            if 'pig' in species.lower():
                self.gestation_days = 114
            elif 'cow' in species.lower() or 'cattle' in species.lower():
                self.gestation_days = 283
            elif 'sheep' in species.lower():
                self.gestation_days = 150
            elif 'goat' in species.lower():
                self.gestation_days = 150
            elif 'horse' in species.lower():
                self.gestation_days = 340


class FarmAnimalHealthWizard(models.TransientModel):
    """
    Wizard model to update animal health status
    """
    _name = 'farm.animal.health.wizard'
    _description = 'Farm Animal Health Update Wizard'

    animal_id = fields.Many2one(
        'stock.lot',
        string='Animal',
        required=True
    )
    health_status = fields.Selection([
        ('healthy', 'Healthy'),
        ('sick', 'Sick'),
        ('quarantine', 'In Quarantine'),
        ('under_treatment', 'Under Treatment'),
    ], string='Health Status', required=True)
    treatment_notes = fields.Text('Treatment Notes')
    next_vaccination_date = fields.Date('Next Vaccination Date')

    def action_update_health_status(self):
        """Update the animal's health status"""
        self.ensure_one()
        self.animal_id.write({
            'health_status': self.health_status,
            'medication_records': self.treatment_notes,
            'last_vaccination_date': self.next_vaccination_date,
        })
        return {'type': 'ir.actions.act_window_close'}