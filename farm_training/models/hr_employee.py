# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # Port fix (batch 7, Odoo 18): core hr_skills already defines
    # hr.employee.skill_ids as a COMPUTED Many2many to hr.skill; redefining
    # the same field name to farm.training.skill keeps the core compute,
    # which then writes hr.skill records into it -> "Wrong value for
    # hr.employee.skill_ids: hr.skill()" at registry load. Renamed to
    # farm_skill_ids (same relation table).
    farm_skill_ids = fields.Many2many('farm.training.skill', 'hr_employee_farm_training_skill_rel', 'employee_id', 'skill_id',
        string='Acquired Skills',
        help='Skills acquired by the employee.'
    )
    certification_ids = fields.Many2many('farm.training.certification', 'hr_employee_farm_training_certification_rel', 'employee_id', 'certification_id',
        string='Certifications Held',
        help='Certifications held by the employee.',
        compute='_compute_certification_ids',
        store=True,
    )
    training_record_ids = fields.One2many(
        'farm.training.training_record',
        'employee_id',
        string='Training Records'
    )

    @api.depends('training_record_ids.certification_id', 'training_record_ids.status')
    def _compute_certification_ids(self):
        for employee in self:
            valid_certs = employee.training_record_ids.filtered(lambda r: r.status in ('valid', 'upcoming_expire')).mapped('certification_id')
            employee.certification_ids = [(6, 0, valid_certs.ids)]

    def check_qualification_for_task(self, required_skills=None, required_certifications=None):
        self.ensure_one()
        if required_skills:
            # Check if employee has all required skills
            if not all(skill in self.farm_skill_ids for skill in required_skills):
                missing_skills = ", ".join((required_skills - self.farm_skill_ids).mapped('name'))
                raise ValidationError(_(f"Employee {self.name} is missing required skills: {missing_skills}"))
        if required_certifications:
            # Check if employee has all valid required certifications
            valid_cert_ids = self.training_record_ids.filtered(lambda r: r.status in ('valid', 'upcoming_expire')).mapped('certification_id').ids
            if not all(cert.id in valid_cert_ids for cert in required_certifications):
                missing_certs = ", ".join((required_certifications - self.certification_ids).mapped('name'))
                raise ValidationError(_(f"Employee {self.name} does not hold all valid required certifications: {missing_certs}"))
        return True
