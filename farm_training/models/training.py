from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class FarmCertificateType(models.Model):
    _name = 'farm.certificate.type'
    _description = 'Agricultural Certificate Type'

    name = fields.Char("Certificate Name", required=True, translate=True) # e.g. "Drone Operator License"
    code = fields.Char("Code", required=True)
    required_for_intervention_types = fields.Selection([
        ('protection', 'Crop Protection'),
        ('aerial_spraying', 'Aerial Spraying'),
        ('medical', 'Medical/Prevention'),
        ('harvesting', 'Mechanical Harvesting')
    ], string="Mandatory for Task Type", help="If set, system will check for this certificate during task confirmation.")

class FarmCertificate(models.Model):
    _name = 'farm.certificate'
    _description = 'Farmer Certificate'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Certificate No.", required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    certificate_type_id = fields.Many2one('farm.certificate.type', string="Type", required=True)
    issue_date = fields.Date("Issue Date")
    expiry_date = fields.Date("Expiry Date")
    is_valid = fields.Boolean("Is Valid", compute='_compute_is_valid', store=True, precompute=True)
    attachment_ids = fields.Many2many('ir.attachment', 'farm_certificate_attachment_rel', 'certificate_id', 'attachment_id', string="Certificate Photos")

    @api.depends('expiry_date')
    def _compute_is_valid(self):
        today = fields.Date.today()
        for rec in self:
            rec.is_valid = not rec.expiry_date or rec.expiry_date >= today

class FarmTrainingSession(models.Model):
    _name = 'farm.training.session'
    _description = 'Farmer Training Session'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Topic", required=True)
    date = fields.Date("Date", default=fields.Date.today)
    hours = fields.Float("Duration (Hours)")
    trainer_id = fields.Many2one('res.partner', string="Trainer/Expert")
    trainee_ids = fields.Many2many('hr.employee', 'farm_training_session_employee_rel', 'session_id', 'employee_id', string="Trainees")
    content = fields.Html("Training Content")
    state = fields.Selection([('draft', 'Draft'), ('done', 'Completed')], default='draft')

    def action_complete(self):
        self.write({'state': 'done'})

    def _cron_check_certificate_expiry(self):
        """ US-040-08: Automatically scan certificates expiring soon and remind the person in charge """
        today = fields.Date.today()
        warning_date = today + datetime.timedelta(days=30)
        
        # Find 30 valid certificates expiring within days
        expiring_certs = self.env['farm.certificate'].search([
            ('expiry_date', '<=', warning_date),
            ('expiry_date', '>=', today),
            ('is_valid', '=', True)
        ])
        
        for cert in expiring_certs:
            # Create the warning activity
            cert.activity_schedule(
                'mail.mail_activity_data_warning',
                user_id=cert.employee_id.parent_id.user_id.id or self.env.uid,
                summary=_("CERTIFICATE EXPIRING: %s for %s") % (cert.certificate_type_id.name, cert.employee_id.name),
                note=_("The certificate will expire on %s. Please arrange for recertification.") % cert.expiry_date
            )

    @api.model
    def get_qualified_worker_domain(self, intervention_type):
        """ Return the domain of employees qualified for a specific task """
        required_cert_type = self.env['farm.certificate.type'].search([
            ('required_for_intervention_types', '=', intervention_type)
        ], limit=1)
        
        if not required_cert_type:
            return [] # no special requirement
            
        # Find all employees holding a valid certificate of this type
        valid_certs = self.env['farm.certificate'].search([
            ('certificate_type_id', '=', required_cert_type.id),
            ('is_valid', '=', True)
        ])
        return [('id', 'in', valid_certs.mapped('employee_id').ids)]

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    training_certificate_ids = fields.One2many('farm.certificate', 'employee_id', string="Certificates")
    training_session_ids = fields.Many2many('farm.training.session', 'hr_employee_farm_training_session_rel', 'employee_id', 'session_id', string="Training History")
    total_training_hours = fields.Float("Total Training Hours", compute='_compute_training_hours')

    def _compute_training_hours(self):
        for emp in self:
            emp.total_training_hours = sum(emp.training_session_ids.filtered(lambda s: s.state == 'done').mapped('hours'))

class AgriIntervention(models.Model):
    _inherit = 'mrp.production'

    @api.onchange('intervention_type')
    def _onchange_intervention_type_filter_workers(self):
        """ US-040-08, US-052-02: US-040-08, US-052-02: Dynamically filter workers qualified by task type """
        if self.intervention_type:
            domain = self.env['farm.certificate.type'].get_qualified_worker_domain(self.intervention_type)
            return {'domain': {'doer_ids': domain}}

    def action_confirm(self):
        """ 
        US-040-08: Qualification admission check logic 
        If the intervention task type requires a special qualification, check that the executor holds a certificate
        """
        for mo in self:
            # 1. 1. Check whether this task type requires a certificate
            required_cert_type = self.env['farm.certificate.type'].search([
                ('required_for_intervention_types', '=', mo.intervention_type)
            ], limit=1)

            if required_cert_type:
                # 2. 2. Check all executors
                if not mo.doer_ids:
                    raise UserError(_("This task (%s) requires certified personnel, but no workers are assigned.") % mo.intervention_type)
                
                for employee in mo.doer_ids:
                    valid_cert = employee.training_certificate_ids.filtered(
                        lambda c: c.certificate_type_id == required_cert_type and c.is_valid
                    )
                    if not valid_cert:
                        raise UserError(_("ACCESS DENIED: Worker %s does not have a valid '%s' for this %s task.") % (
                            employee.name, required_cert_type.name, mo.intervention_type
                        ))
        
        return super(AgriIntervention, self).action_confirm()