from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta

class AgriManureBatch(models.Model):
    _name = 'agri.manure.batch'
    _description = 'Agricultural Manure Batch Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'batch_no'

    batch_no = fields.Char("Batch No.", default=lambda self: _('New'))
    production_date = fields.Date("Production Date", default=fields.Date.today)
    quantity = fields.Float("Quantity (kg)")
    lot_source_ids = fields.Many2many('stock.lot', string="Source Animal Lots")
    location_source_id = fields.Many2one('farm.location', string="Source Location", domain=[('usage', '=', 'internal')]) # e.g., Barn

    # Disposal method
    disposal_method = fields.Selection([
        ('composting', 'Composting'),
        ('biogas', 'Biogas Digestion'),
        ('transfer_third_party', 'Transfer to Third Party'),
        ('direct_field_use', 'Direct Field Use')
    ], string="Disposal Method", required=True)

    # Destination and recipient
    destination_location_id = fields.Many2one('farm.location', string="Destination Location", domain=[('is_land_parcel', '=', True)], invisible="disposal_method != 'direct_field_use'")
    recipient_partner_id = fields.Many2one('res.partner', string="Recipient (Third Party)", invisible="disposal_method != 'transfer_third_party'")

    fertilizer_product_id = fields.Many2one('product.product', string="Converted Fertilizer Product", domain=[('input_type', '=', 'fertilizer')])

    # US-057-01: Quality Check Linkage
    quality_check_id = fields.Many2one('agri.quality.check', string="Quality Check (Maturity)", domain=[('quality_state', '=', 'pass')])

    # Nutrient Return [US-057-01, US-057-02]
    pure_n_qty = fields.Float("Pure Nitrogen (kg)", compute='_compute_nutrients', store=True, precompute=True)
    pure_p_qty = fields.Float("Pure Phosphorus (kg)", compute='_compute_nutrients', store=True, precompute=True)
    pure_k_qty = fields.Float("Pure Potassium (kg)", compute='_compute_nutrients', store=True, precompute=True)

    @api.depends('quantity', 'fertilizer_product_id.n_content', 'fertilizer_product_id.p_content', 'fertilizer_product_id.k_content')
    def _compute_nutrients(self):
        for batch in self:
            prod = batch.fertilizer_product_id
            if prod:
                batch.pure_n_qty = batch.quantity * (prod.n_content / 100.0)
                batch.pure_p_qty = batch.quantity * (prod.p_content / 100.0)
                batch.pure_k_qty = batch.quantity * (prod.k_content / 100.0)
            else:
                batch.pure_n_qty = batch.pure_p_qty = batch.pure_k_qty = 0.0

    notes = fields.Text("Notes")

    def _get_stock_location_for_farm_location(self, farm_location):
        """ Map a ``farm.location`` record to a real ``stock.location``.

        B28 (SIMULASI.md): ``farm.location`` is a separate model/table
        (``_name = 'farm.location'`` + ``_inherit = 'stock.location'``
        in farm_core ``land_location.py`` — prototype inheritance, own
        id sequence, NO link field to ``stock.location``). A
        farm.location id is therefore NOT a stock.location id: passing
        it raw as ``location_src_id`` / ``location_dest_id`` on
        ``mrp.production`` violates the FK to ``stock_location``
        (e.g. farm.location 48 "SIMULASI B5R1 Lahan A1" exists while
        stock.location 48 does not). Resolve in this order:
        1. a ``stock.location`` with the same name (same company);
        2. otherwise the default warehouse stock location (WH/Stock).
        """
        StockLocation = self.env['stock.location']
        if farm_location:
            match = StockLocation.search([
                ('name', '=', farm_location.name),
                ('company_id', '=', farm_location.company_id.id),
            ], limit=1)
            if match:
                return match
        warehouse = self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.company.id)], limit=1)
        if warehouse and warehouse.lot_stock_id:
            return warehouse.lot_stock_id
        return self.env.ref('stock.stock_location_stock', raise_if_not_found=False)

    def action_convert_to_fertilizer(self):
        """ US-057-02: Convert manure to fertilizer via Manufacturing Order """
        self.ensure_one()
        if not self.fertilizer_product_id:
            raise UserError(_("Please select a Converted Fertilizer Product first!"))

        if not self.quality_check_id or self.quality_check_id.quality_state != 'pass':
            raise UserError(_("SAFETY BLOCK: A passed quality check (Compost Maturity) is required before conversion!"))

        # B28: location_source_id is a farm.location — its id is NOT a
        # stock.location id. Map it first (name match, else WH/Stock);
        # leave the keys out entirely when no stock location resolves
        # so mrp.production's own defaults apply.
        stock_location = self._get_stock_location_for_farm_location(self.location_source_id)
        mo_vals = {
            'product_id': self.fertilizer_product_id.id,
            'product_qty': self.quantity,
            'product_uom_id': self.fertilizer_product_id.uom_id.id,
            'intervention_type': 'fertilizing', # Or a custom 'conversion' type if defined
            'origin': self.batch_no,
        }
        if stock_location:
            mo_vals['location_src_id'] = stock_location.id
            mo_vals['location_dest_id'] = stock_location.id

        # Create a Manufacturing Order (Intervention)
        mo = self.env['mrp.production'].create(mo_vals)

        # In a real scenario, we would also add the raw manure product to the MO
        # For this prototype, we'll mark it as confirmed
        mo.action_confirm()

        # TODO: [DE-INDUSTRIAL] Use 'Agricultural Intervention' instead of 'Manufacturing Order' in Python string for consistent audit logs
        self.message_post(body=_("Manufacturing Order %s created for manure conversion.") % mo.name)

        return {
            'name': _('Conversion MO'),
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production',
            'res_id': mo.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('batch_no', _('New')) == _('New'):
                vals['batch_no'] = self.env['ir.sequence'].next_by_code('agri.manure.batch') or _('MNR')
        return super().create(vals_list)


class AgriManureLedger(models.Model):
    _name = 'agri.manure.ledger'
    _description = 'Agricultural Monthly Manure Resource Utilization Ledger'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'ledger_no'

    ledger_no = fields.Char("Ledger No.", default=lambda self: _('New'))
    month = fields.Selection([
        ('01', 'January'), ('02', 'February'), ('03', 'March'), ('04', 'April'),
        ('05', 'May'), ('06', 'June'), ('07', 'July'), ('08', 'August'),
        ('09', 'September'), ('10', 'October'), ('11', 'November'), ('12', 'December')
    ], string="Month", default=lambda self: fields.Date.today().strftime('%m'), required=True)
    year = fields.Integer("Year", default=lambda self: fields.Date.today().year, required=True)

    batch_ids = fields.Many2many('agri.manure.batch', string="Manure Batches Included", compute='_compute_batch_ids', store=True, precompute=True)
    total_quantity_disposed = fields.Float("Total Disposed Quantity (kg)", compute='_compute_ledger_stats', store=True, precompute=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('reported', 'Reported')
    ], default='draft', tracking=True)

    @api.depends('month', 'year')
    def _compute_batch_ids(self):
        for ledger in self:
            date_start = fields.Date.from_string(f"{ledger.year}-{ledger.month}-01")
            date_end = date_start + relativedelta(months=1, days=-1)
            ledger.batch_ids = self.env['agri.manure.batch'].search([
                ('production_date', '>=', date_start),
                ('production_date', '<=', date_end)
            ])

    @api.depends('batch_ids.quantity')
    def _compute_ledger_stats(self):
        for ledger in self:
            ledger.total_quantity_disposed = sum(ledger.batch_ids.mapped('quantity'))

    def action_generate_ledger(self):
        """ Generate the monthly manure resource utilization ledger [US-041-05].

        NOTE (port 19.0 -> 18.0, de-China-ize): upstream named this after
        MOARA (China's Ministry of Agriculture and Rural Affairs); the
        ledger itself is a generic monthly utilization record, so the
        regulator-specific name was dropped (method renamed from
        ``action_generate_moara_ledger``).
        """
        self.ensure_one()
        self.message_post(body=_("Manure Utilization Ledger generated for %s/%s.") % (self.month, self.year))
        return True

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('ledger_no', _('New')) == _('New'):
                vals['ledger_no'] = self.env['ir.sequence'].next_by_code('agri.manure.ledger') or _('MNL')
        return super().create(vals_list)