from odoo import models, fields, api, _

class FarmWorklog(models.Model):
    _name = 'farm.worklog'
    _description = 'Farm Field Worklog'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'

    employee_id = fields.Many2one('hr.employee', string="Worker", required=True)
    task_id = fields.Many2one('project.task', string="Farm Task", required=True)
    date = fields.Date("Date", default=fields.Date.today, required=True)
    
    work_type = fields.Selection([
        ('tillage', 'Tillage'),
        ('sowing', 'Sowing'),
        ('harvesting', 'Harvesting'),
        ('packaging', 'Packaging'),
        ('feeding', 'Feeding')
    ], string="Work Type", required=True)
    
    quantity = fields.Float("Done Quantity", default=1.0)
    uom_id = fields.Many2one('uom.uom', string="Unit")
    
    notes = fields.Text("Notes")

    def action_approve(self):
        """ Approve and allocate the labor cost [US-036-04].

        NOTE (port 19.0 -> 18.0): Odoo 18 ``project.task`` has no
        ``analytic_account_id`` (removed with the analytic rework);
        the analytic account lives on the task's project
        (``project.project.account_id``). ``account.analytic.line``
        in 18 also has no ``product_id``/``employee_id`` fields, so
        only ``account_id``/``amount``/``unit_amount`` are written
        (``analytic_distribution`` is auto-computed from the account).
        """
        for log in self:
            # Get the worker's hourly rate (from the employee record, or a fixed fallback)
            hourly_rate = getattr(log.employee_id, 'hourly_cost', 50.0)
            amount = log.quantity * hourly_rate

            # Find the analytic account of the task's project
            analytic_account = log.task_id.project_id.account_id
            if analytic_account:
                self.env['account.analytic.line'].create({
                    'name': _('Labor: %s on %s') % (log.employee_id.name, log.task_id.name),
                    'account_id': analytic_account.id,
                    'amount': -amount, # Expense is negative
                    'unit_amount': log.quantity,
                })
        return True

class ProjectTask(models.Model):
    _inherit = 'project.task'

    worklog_ids = fields.One2many('farm.worklog', 'task_id', string="Labor Worklogs")
    total_harvested_qty = fields.Float("Total Harvested (kg)", compute='_compute_total_worklog_qty', store=True, precompute=True)
    
    # Skill requirement [US-004-02]
    required_skill_id = fields.Many2one('farm.agri.skill', string="Required Skill")
    eligible_worker_ids = fields.Many2many('hr.employee', 'project_task_hr_employee_rel', 'task_id', 'employee_id', compute='_compute_eligible_workers', string="Eligible Workers")

    @api.depends('required_skill_id')
    def _compute_eligible_workers(self):
        for task in self:
            if task.required_skill_id:
                task.eligible_worker_ids = self.env['hr.employee'].search([
                    ('agri_skill_ids', 'in', task.required_skill_id.id)
                ])
            else:
                task.eligible_worker_ids = self.env['hr.employee'].search([])

    @api.depends('worklog_ids.quantity', 'worklog_ids.work_type')
    def _compute_total_worklog_qty(self):
        for task in self:
            harvesting_logs = task.worklog_ids.filtered(lambda l: l.work_type == 'harvesting')
            task.total_harvested_qty = sum(harvesting_logs.mapped('quantity'))

class AgriSkill(models.Model):
    _name = 'farm.agri.skill'
    _description = 'Agricultural Skill'

    name = fields.Char("Skill Name", required=True) # e.g., Harvester Operator, Veterinarian
    description = fields.Text("Description")
    # Color index for the many2many_tags widget (color_field='color' in the
    # employee form view); without this field the widget has nothing to read.
    color = fields.Integer("Color", default=0)

    # Certificate requirement [US-040-08]
    requires_certificate = fields.Boolean("Requires Certificate", default=False)

class FarmEmployeeCertificate(models.Model):
    _name = 'farm.employee.certificate'
    _description = 'Employee Skill Certificate'

    employee_id = fields.Many2one('hr.employee', required=True)
    skill_id = fields.Many2one('farm.agri.skill', string="Skill/Qualification", required=True)
    certificate_number = fields.Char("Cert No.")
    date_expiry = fields.Date("Expiry Date")
    
    state = fields.Selection([
        ('valid', 'Valid'),
        ('expired', 'Expired')
    ], compute='_compute_state', store=True, precompute=True)

    @api.depends('date_expiry')
    def _compute_state(self):
        today = fields.Date.today()
        for cert in self:
            if cert.date_expiry and cert.date_expiry < today:
                cert.state = 'expired'
            else:
                cert.state = 'valid'

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    is_seasonal = fields.Boolean("Seasonal Laborer", default=False, help="Identify external or seasonal workers.")
    hourly_cost = fields.Float("Hourly Cost", default=0.0)
    agri_skill_ids = fields.Many2many('farm.agri.skill', 'hr_employee_farm_agri_skill_rel', 'employee_id', 'skill_id', string="Agricultural Skills")
    piece_rate_total = fields.Float("Total Piece-rate Performance", compute='_compute_piece_rate')
    
    certificate_ids = fields.One2many('farm.employee.certificate', 'employee_id', string="Certificates")

    def _compute_piece_rate(self):
        for employee in self:
            logs = self.env['farm.worklog'].search([('employee_id', '=', employee.id)])
            employee.piece_rate_total = sum(logs.mapped('quantity'))
