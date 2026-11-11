from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.addons.project.models.project_task import CLOSED_STATES
import logging

_logger = logging.getLogger(__name__)

class FarmAquacultureOperation(models.Model):
    """
    Aquaculture operation model for managing pond/tank operations, water quality, feeding, and growth tracking
    """
    _name = 'farm.aquaculture.operation'
    _description = 'Farm Aquaculture Operation'
    _inherit = 'project.task'  # Inherit from project.task to leverage existing task functionality

    # Many2many inheritance collision fix (also needed on Odoo 18):
    # project.task's user_ids / personal_stage_type_ids / depend_on_ids /
    # dependent_ids share relation tables with project.task itself; a model
    # _inheriting project.task under its own _name must use dedicated
    # relation tables, otherwise both models write into the same table.
    user_ids = fields.Many2many('res.users', relation='farm_aqua_op_user_rel', column1='op_id', column2='user_id', string='Assignees')
    personal_stage_type_ids = fields.Many2many('project.task.type', relation='farm_aqua_op_personal_stage_rel', column1='op_id', column2='stage_id')
    # B12 fix (2026-11-10): comodel MUST be this model itself, mirroring
    # core project.task (project_task.py:262-271). With comodel
    # 'project.task', the inherited constraint _check_no_cyclic_dependencies
    # (@api.constrains('depend_on_ids')) calls _has_cycle('depend_on_ids'),
    # which requires field.comodel_name == self._name (odoo/models.py:6036)
    # and raised "Field must be a many2one or many2many relation on itself:
    # 'depend_on_ids'" on every UI create (the web client always sends the
    # field, even empty). dependent_ids mirrors core as the LIVE inverse of
    # depend_on_ids on the SAME relation table with swapped columns — the
    # old separate table (farm_aqua_op_dependent_rel) was a dead field that
    # never reflected depend_on_ids. Both tables were empty (0 rows), so no
    # data migration is needed; the old table is left orphaned, harmless.
    depend_on_ids = fields.Many2many('farm.aquaculture.operation', relation='farm_aqua_op_depend_on_rel', column1='op_id',
                                     column2='task_id', string='Blocked By', tracking=True, copy=False,
                                     domain="[('project_id', '!=', False), ('id', '!=', id)]")
    dependent_ids = fields.Many2many('farm.aquaculture.operation', relation='farm_aqua_op_depend_on_rel', column1='task_id',
                                     column2='op_id', string='Block', copy=False,
                                     domain="[('project_id', '!=', False), ('id', '!=', id)]")
    # B12-residu fix (2026-11-10): parent_id MUST point at this model
    # itself, mirroring core project.task (project_task.py:229-230).
    # With comodel 'project.task', the inherited constraint
    # _check_parent_id (@api.constrains('parent_id'),
    # project_task.py:574-576) calls _has_cycle(), which requires
    # field.comodel_name == self._name (odoo/models.py:6012-6036) and
    # raised "Field must be a many2one or many2many relation on itself:
    # 'parent_id'" on every UI create (the web client always sends
    # parent_id, even False). The same comodel mismatch also broke the
    # field's own domain: ('id', 'child_of', id) raises "Invalid parent
    # field" in expression.py:child_of_domain when the parent field's
    # comodel is not the model itself. Definition mirrors core exactly
    # (string/index/domain/tracking); core parent_id has NO recursive
    # flag — recursive=True is for computed fields with a self-dependency
    # (odoo/fields.py:259-260), so none is added here. The DB foreign
    # key is re-pointed automatically on upgrade by
    # Registry.check_foreign_keys (drops the old FK to project_task).
    # child_ids is redefined as the LIVE inverse on the same model
    # (mirroring depend_on_ids/dependent_ids above): the inherited
    # One2many pointed at project.task records, which is meaningless
    # for operations and disagrees with _compute_subtask_count (which
    # searches this model on parent_id). Redefining parent_id alone
    # would NOT have broken child_ids resolution (it keeps resolving
    # against project.task.parent_id), but leaving it would keep the
    # Sub-tasks tab showing foreign project.task rows.
    parent_id = fields.Many2one('farm.aquaculture.operation', string='Parent Task', index=True,
                                domain="[('id', '!=', id), '!', ('id', 'child_of', id), ('project_id', '!=', False)]",
                                tracking=True)
    child_ids = fields.One2many('farm.aquaculture.operation', 'parent_id', string="Sub-tasks",
                                domain="[('recurring_task', '=', False)]", export_string_translation=False)

    # B12-residu, lanjutan: _compute_subtask_count core
    # (project_task.py:638-653) menghitung dari self.env['project.task']
    # secara HARDCODE — untuk operasi, itu menghitung sub-task dari
    # project.task yang KEBETULAN berbagi id (tabrakan id antar tabel),
    # bukan anak operasi. Akibat nyata di salinan: create operasi privat
    # (tanpa project) dengan id 13 gagal "This task has sub-tasks, so it
    # can't be private" karena project.task 13 punya 1 anak — padahal
    # operasi itu tidak punya anak sama sekali (REPRO-4; id 10/11/12
    # lolos hanya karena project.task 10/11/12 tidak punya anak).
    # Override ini cerminan persis core, dengan model _read_group
    # diganti ke model sendiri; cabang len(child_ids) sudah benar
    # sejak child_ids di-redefine di atas.
    @api.depends('child_ids')
    def _compute_subtask_count(self):
        if not any(self._ids):
            for task in self:
                task.subtask_count, task.closed_subtask_count = len(task.child_ids), len(task.child_ids.filtered(lambda r: r.state in CLOSED_STATES))
            return
        total_and_closed_subtask_count_per_parent_id = {
            parent.id: (count, sum(s in CLOSED_STATES for s in states))
            for parent, states, count in self.env[self._name]._read_group(
                [('parent_id', 'in', self.ids)],
                ['parent_id'],
                ['state:array_agg', '__count'],
            )
        }
        for task in self:
            task.subtask_count, task.closed_subtask_count = total_and_closed_subtask_count_per_parent_id.get(task.id, (0, 0))

    # B12-residu, lanjutan 2: pohon sub-task core dibaca dari tabel
    # project_task secara HARDCODE (SQL mentah di
    # _get_subtask_ids_per_task_id, project_task.py:1769-1802). Untuk
    # operasi, unlink() memanggil _get_all_subtasks() -> metode ini ->
    # SQL itu menemukan anak project.task yang KEBETULAN berbagi id,
    # lalu browse([id anak project.task]) pada model operasi
    # menghasilkan record hantu -> MissingError saat super().unlink()
    # menghapusnya (terbukti: REPRO-4 op 19, anak project.task 19 ada,
    # unlink gagal "Record does not exist or has been deleted").
    # Override ini cerminan persis core dengan nama tabel diganti ke
    # tabel model sendiri; _get_subtasks_recursively juga dicerminkan
    # (kasus kosong core mengembalikan recordset project.task kosong,
    # yang membuat concat() melempar TypeError bila digabung dengan
    # operasi — models.py:6957 menolak model berbeda walau kosong).
    def _get_subtask_ids_per_task_id(self):
        if not self:
            return {}

        res = dict.fromkeys(self._ids, [])
        if all(self._ids):
            self.env.cr.execute(
                """
         WITH RECURSIVE task_tree
                     AS (
                     SELECT id, id as supertask_id
                       FROM farm_aquaculture_operation
                      WHERE id IN %(ancestor_ids)s
                      UNION
                         SELECT t.id, tree.supertask_id
                           FROM farm_aquaculture_operation t
                           JOIN task_tree tree
                             ON tree.id = t.parent_id
                            AND t.active in (TRUE, %(active)s)
                          WHERE t.parent_id IS NOT NULL
               ) SELECT supertask_id, ARRAY_AGG(id)
                   FROM task_tree
                  WHERE id != supertask_id
               GROUP BY supertask_id
                """,
                {
                    "ancestor_ids": tuple(self.ids),
                    "active": self._context.get('active_test', True),
                }
            )
            res.update(dict(self.env.cr.fetchall()))
        else:
            res.update({
                task.id: task._get_subtasks_recursively().ids
                for task in self
            })
        return res

    def _get_subtasks_recursively(self):
        children = self.child_ids
        if not children:
            return self.env[self._name]
        return children + children._get_subtasks_recursively()


    # Pond/Tank Information
    pond_id = fields.Many2one('stock.lot', string='Pond/Tank',
                              domain=[('product_id.categ_id.name', 'ilike', 'pond')])
    pond_capacity = fields.Float('Pond Capacity (m³)', help='Capacity of the selected pond')
    aquatic_species = fields.Char('Aquatic Species', help='Species name for pond')
    initial_stocking = fields.Integer('Initial Stocking Count')
    current_count = fields.Integer('Current Count', compute='_compute_current_count', store=True, precompute=True)

    # Water Quality Management
    water_temperature = fields.Float('Water Temperature (°C)')
    ph_level = fields.Float('pH Level')
    dissolved_oxygen = fields.Float('Dissolved Oxygen (mg/L)')
    ammonia_level = fields.Float('Ammonia Level (mg/L)')
    nitrite_level = fields.Float('Nitrite Level (mg/L)')
    water_quality_status = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('critical', 'Critical'),
    ], string='Water Quality Status', compute='_compute_water_quality_status', store=True, precompute=True)

    # Feeding Management
    feeding_schedule = fields.Text('Feeding Schedule')
    last_feeding_date = fields.Datetime('Last Feeding Time')
    daily_feeding_rate = fields.Float('Daily Feeding Rate (%)', help='Percentage of body weight fed daily')

    # Growth Tracking
    avg_initial_weight = fields.Float('Avg Initial Weight (g)')
    avg_current_weight = fields.Float('Avg Current Weight (g)', compute='_compute_avg_current_weight', store=True, precompute=True)
    growth_rate = fields.Float('Growth Rate (g/day)', compute='_compute_growth_rate', store=True, precompute=True)
    target_weight = fields.Float('Target Weight (g)')

    # Harvest Management
    harvest_readiness = fields.Boolean('Harvest Readiness', compute='_compute_harvest_readiness', store=True, precompute=True)
    harvest_plan_date = fields.Date('Planned Harvest Date')

    # Aquaculture specific stages
    aquaculture_stage = fields.Selection([
        ('tank_preparation', 'Tank Preparation'),
        ('water_conditioning', 'Water Conditioning'),
        ('seed_stocking', 'Seed Stocking'),
        ('growing', 'Growing'),
        ('harvesting', 'Harvesting'),
        ('post_harvest', 'Post-Harvest'),
    ], string='Aquaculture Stage', default='tank_preparation')

    # Water treatment and circulation
    water_treatment_method = fields.Selection([
        ('mechanical', 'Mechanical'),
        ('biological', 'Biological'),
        ('chemical', 'Chemical'),
        ('uv', 'UV Sterilization'),
        ('ozone', 'Ozone Treatment'),
    ], string='Water Treatment Method')
    circulation_rate = fields.Float('Water Circulation Rate (m³/hour)')

    @api.depends('initial_stocking')
    def _compute_current_count(self):
        """Compute current stock count"""
        for record in self:
            # This would be calculated based on actual stock movements
            record.current_count = record.initial_stocking if record.initial_stocking else 0

    @api.depends('water_temperature', 'ph_level', 'dissolved_oxygen', 'ammonia_level', 'nitrite_level')
    def _compute_water_quality_status(self):
        """Compute water quality status based on parameters"""
        for record in self:
            # Critical if any parameter is out of normal range
            if (record.dissolved_oxygen < 3.0 or  # Critical low oxygen
                record.ammonia_level > 2.0 or     # Critical high ammonia
                record.ph_level < 6.0 or record.ph_level > 9.0):  # Extreme pH
                record.water_quality_status = 'critical'
            elif (record.dissolved_oxygen < 5.0 or  # Low oxygen
                  record.ammonia_level > 1.0 or    # High ammonia
                  record.ph_level < 6.5 or record.ph_level > 8.5):  # Outside optimal range
                record.water_quality_status = 'poor'
            elif (record.dissolved_oxygen < 6.0 or  # Slightly low oxygen
                  record.ammonia_level > 0.5 or    # Moderate ammonia
                  record.ph_level < 7.0 or record.ph_level > 8.0):  # Not ideal
                record.water_quality_status = 'fair'
            else:
                record.water_quality_status = 'good'

    @api.depends('avg_initial_weight', 'current_count')
    def _compute_avg_current_weight(self):
        """Compute current average weight"""
        for record in self:
            # Simplified calculation - in reality would track individual fish weights
            record.avg_current_weight = record.avg_initial_weight if record.avg_initial_weight else 0

    @api.depends('avg_initial_weight', 'avg_current_weight')
    def _compute_growth_rate(self):
        """Compute growth rate"""
        for record in self:
            # Would need time tracking to calculate actual growth rate
            if record.avg_initial_weight > 0:
                record.growth_rate = (record.avg_current_weight - record.avg_initial_weight) / 1.0  # Placeholder for time calculation
            else:
                record.growth_rate = 0.0

    @api.depends('avg_current_weight', 'target_weight', 'aquaculture_stage')
    def _compute_harvest_readiness(self):
        """Compute if the aquatic species is ready for harvest"""
        for record in self:
            record.harvest_readiness = (record.avg_current_weight >= record.target_weight and
                                      record.aquaculture_stage == 'growing')

    def action_add_stock(self, count, species_type=None):
        """Add stock to pond"""
        self.ensure_one()
        new_count = self.current_count + count
        self.write({'current_count': new_count})

        body = _("ADDITIONAL STOCK: %s new %s added. Total count now: %s") % (count, species_type or "species", new_count)
        self.message_post(body=body)
        return True

    def action_record_mortality(self, count, cause=None):
        """Record mortality"""
        self.ensure_one()
        new_count = max(0, self.current_count - count)
        self.write({'current_count': new_count})

        body = _("MORTALITY RECORDED: %s %s died. Total count now: %s. Cause: %s") % (
            count, self.aquatic_species or "species", new_count, cause or "Unknown")
        self.message_post(body=body)
        return True

    def action_record_water_quality(self, temperature=None, ph=None, dissolved_oxygen=None, ammonia=None, nitrite=None):
        """Record water quality parameters"""
        self.ensure_one()
        updates = {}
        if temperature is not None:
            updates['water_temperature'] = temperature
        if ph is not None:
            updates['ph_level'] = ph
        if dissolved_oxygen is not None:
            updates['dissolved_oxygen'] = dissolved_oxygen
        if ammonia is not None:
            updates['ammonia_level'] = ammonia
        if nitrite is not None:
            updates['nitrite_level'] = nitrite

        if updates:
            self.write(updates)

            body = _("WATER QUALITY UPDATE:\n")
            if temperature: body += f"Temperature: {temperature}°C\n"
            if ph: body += f"pH: {ph}\n"
            if dissolved_oxygen: body += f"Dissolved Oxygen: {dissolved_oxygen} mg/L\n"
            if ammonia: body += f"Ammonia: {ammonia} mg/L\n"
            if nitrite: body += f"Nitrite: {nitrite} mg/L\n"

            self.message_post(body=body)
        return True

    def action_schedule_harvest(self, harvest_date):
        """Schedule harvest"""
        self.ensure_one()
        self.write({'harvest_plan_date': harvest_date})
        self.message_post(body=_("Harvest scheduled for %s") % harvest_date)
        return True


class FarmWaterQualityLog(models.Model):
    """
    Water quality log model for tracking historical water parameters
    """
    _name = 'farm.water.quality.log'
    _description = 'Farm Water Quality Log'
    _order = 'log_date desc'

    operation_id = fields.Many2one('farm.aquaculture.operation', string='Aquaculture Operation', required=True)
    log_date = fields.Datetime('Log Date', default=fields.Datetime.now, required=True)
    temperature = fields.Float('Temperature (°C)')
    ph_level = fields.Float('pH Level')
    dissolved_oxygen = fields.Float('Dissolved Oxygen (mg/L)')
    ammonia_level = fields.Float('Ammonia Level (mg/L)')
    nitrite_level = fields.Float('Nitrite Level (mg/L)')
    water_turbidity = fields.Float('Turbidity (NTU)')
    water_salinity = fields.Float('Salinity (ppt)')
    weather_conditions = fields.Char('Weather Conditions')
    notes = fields.Text('Notes')

    @api.model
    def create(self, vals):
        """Override create to update operation with current values"""
        record = super().create(vals)
        if record.operation_id:
            # Update the current values in the operation
            record.operation_id.write({
                'water_temperature': record.temperature,
                'ph_level': record.ph_level,
                'dissolved_oxygen': record.dissolved_oxygen,
                'ammonia_level': record.ammonia_level,
                'nitrite_level': record.nitrite_level,
            })
        return record