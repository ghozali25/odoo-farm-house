from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class CooperativeEntity(models.Model):
    """
    Cooperative entity [US-042-01]
    """
    _name = 'cooperative.entity'
    _description = 'Cooperative Entity'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True, copy=False)
    legal_representative = fields.Char('Legal Representative')
    registration_number = fields.Char('Registration Number')
    registration_date = fields.Date('Registration Date')
    address = fields.Text('Address')
    phone = fields.Char('Phone')
    email = fields.Char('Email')
    member_farm_ids = fields.One2many('farm.entity', 'cooperative_id', string='Member Farms')
    is_active = fields.Boolean('Is Active', default=True)
    description = fields.Text('Description')

    # B2G / Government & Commercial dual-purpose [US-042-25]
    purpose_type = fields.Selection([
        ('commercial', 'Commercial (Business oriented)'),
        ('government', 'Government (Regulatory/Policy oriented)'),
        ('both', 'Dual Purpose (Commercial & Government)')
    ], string="Cooperative Purpose", default='commercial', required=True, tracking=True)

    overseeing_agency_id = fields.Many2one('res.partner', string="Overseeing Government Agency",
                                          help="The government body this cooperative reports to.")

    is_subsidy_hub = fields.Boolean("Subsidy Distribution Hub", default=False,
                                   help="Check if this cooperative distributes government subsidies to members.")

    compliance_audit_authority = fields.Boolean("Has Audit Authority", default=False,
                                               help="Check if this cooperative has the power to perform regulatory audits on members.")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if 'code' not in vals or not vals['code']:
                vals['code'] = self.env['ir.sequence'].next_by_code('cooperative.entity') or '/'
        return super().create(vals_list)

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, f"{record.code} - {record.name}"))
        return result


class FarmEntity(models.Model):
    """
    Farm entity [US-042-01, US-042-02]
    """
    _name = 'farm.entity'
    _description = 'Farm Entity'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', required=True)
    code = fields.Char('Code', required=True, copy=False)
    entity_type = fields.Selection([
        ('farm', 'Farm'),
        ('cooperative', 'Cooperative'),
        ('franchise', 'Franchise Farm'),
        ('subsidiary', 'Subsidiary'),
    ], string='Entity Type', required=True, default='farm')
    parent_entity_id = fields.Many2one('farm.entity', string='Parent Entity')
    child_entity_ids = fields.One2many('farm.entity', 'parent_entity_id', string='Child Entities')
    cooperative_id = fields.Many2one('cooperative.entity', string='Cooperative')
    company_id = fields.Many2one('res.company', string='Company', required=True)
    contact_person = fields.Char('Contact Person')
    phone = fields.Char('Phone')
    email = fields.Char('Email')
    address = fields.Text('Address')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date', help='For franchise agreements or membership periods')
    is_active = fields.Boolean('Is Active', default=True)
    data_isolation_level = fields.Selection([
        ('full', 'Full Isolation'),
        ('partial', 'Partial Sharing'),
        ('open', 'Open Sharing'),
    ], string='Data Isolation Level', default='partial', required=True)
    shared_data_types = fields.Many2many(
        'ir.model',
        'farm_entity_shared_data_rel',
        'entity_id',
        'model_id',
        string='Shared Data Types',
        help='Types of data that can be shared with parent entity'
    )
    description = fields.Text('Description')

    @api.model
    def create(self, vals):
        if 'code' not in vals or not vals['code']:
            vals['code'] = self.env['ir.sequence'].next_by_code('farm.entity') or '/'
        return super().create(vals)

    @api.constrains('parent_entity_id')
    def _check_parent_entity_recursion(self):
        """Prevent circular entity references"""
        if not self._check_recursion('parent_entity_id'):
            raise ValidationError(_('You cannot create recursive entity relationships.'))

    def name_get(self):
        result = []
        for record in self:
            parent_str = f" ({record.parent_entity_id.name})" if record.parent_entity_id else ""
            result.append((record.id, f"{record.code} - {record.name}{parent_str}"))
        return result

    def get_accessible_data(self, model_name):
        """
        Get accessible data according to the data-isolation level [US-042-02]
        """
        if self.data_isolation_level == 'full':
            # Fully isolated: only this entity's data is accessible
            return self.env[model_name].search([('company_id', '=', self.company_id.id)])
        elif self.data_isolation_level == 'partial':
            # Partially shared: specific data types of this entity and its parent are accessible
            accessible_companies = self._get_accessible_companies()
            if model_name in [data_model.model for data_model in self.shared_data_types]:
                return self.env[model_name].search([('company_id', 'in', accessible_companies.ids)])
            else:
                return self.env[model_name].search([('company_id', '=', self.company_id.id)])
        else:  # open
            # Open sharing: all related entities' data is accessible
            accessible_companies = self._get_accessible_companies()
            return self.env[model_name].search([('company_id', 'in', accessible_companies.ids)])

    def _get_accessible_companies(self):
        """Get the list of accessible companies"""
        companies = self.company_id  # This entity's company
        # Add the parent entity company's data
        current = self
        while current.parent_entity_id:
            current = current.parent_entity_id
            companies |= current.company_id
        # Add child entities' companies' data
        children = self._get_all_child_entities()
        for child in children:
            companies |= child.company_id
        return companies

    def _get_all_child_entities(self):
        """Recursively get all child entities"""
        children = self.child_entity_ids
        for child in children:
            children |= child._get_all_child_entities()
        return children


class FranchiseFarm(models.Model):
    """
    Franchise farm management [US-042-05]
    """
    _name = 'franchise.farm'
    _description = 'Franchise Farm Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Franchise Farm Name', required=True)
    code = fields.Char('Code', required=True, copy=False)
    farm_entity_id = fields.Many2one('farm.entity', string='Farm Entity', required=True)
    franchise_agreement_date = fields.Date('Franchise Agreement Date')
    franchise_expiry_date = fields.Date('Franchise Expiry Date')
    franchise_fee = fields.Float('Franchise Fee')
    royalty_rate = fields.Float('Royalty Rate (%)', help='Percentage of sales as royalty')
    brand_usage_rights = fields.Text('Brand Usage Rights')
    operational_standards = fields.Text('Operational Standards')
    compliance_status = fields.Selection([
        ('compliant', 'Compliant'),
        ('warning', 'Warning'),
        ('non_compliant', 'Non-Compliant'),
    ], string='Compliance Status', default='compliant', tracking=True)
    last_audit_date = fields.Date('Last Audit Date')
    next_audit_date = fields.Date('Next Audit Date')
    audit_notes = fields.Text('Audit Notes')
    is_active = fields.Boolean('Is Active', default=True)
    description = fields.Text('Description')

    @api.model
    def create(self, vals):
        if 'code' not in vals or not vals['code']:
            vals['code'] = self.env['ir.sequence'].next_by_code('franchise.farm') or '/'
        return super().create(vals)

    @api.onchange('franchise_agreement_date')
    def _onchange_agreement_date(self):
        if self.franchise_agreement_date:
            # Set the first audit date to one year after the agreement is signed
            from datetime import timedelta
            self.next_audit_date = fields.Date.from_string(self.franchise_agreement_date) + timedelta(days=365)

    def action_perform_compliance_check(self):
        """Perform the compliance check [US-042-05]"""
        for farm in self:
            # Concrete compliance-check logic can be implemented here
            # Check brand standards, operating procedures, etc.
            # Update the compliance status
            farm.compliance_status = 'compliant'  # Simplified implementation; set according to the check result in practice
            farm.last_audit_date = fields.Date.today()
            farm.audit_notes = f"Compliance check performed on {fields.Date.today()}"

            # Compute the next audit date
            from datetime import timedelta
            farm.next_audit_date = fields.Date.add(fields.Date.today(), days=365)

    def action_push_operational_standards(self):
        """Push operating standards [US-042-05]"""
        for farm in self:
            # Logic for pushing standard operating procedures to franchise farms can be implemented here
            # E.g. send technical roadmaps, production standards, etc.
            pass


class ResourceSharing(models.Model):
    """
    Resource sharing management [US-042-03]
    """
    _name = 'resource.sharing'
    _description = 'Resource Sharing Between Entities'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name', required=True, compute='_compute_name', store=True, precompute=True)
    source_entity_id = fields.Many2one('farm.entity', string='Source Entity', required=True)
    target_entity_id = fields.Many2one('farm.entity', string='Target Entity', required=True)
    resource_type = fields.Selection([
        ('equipment', 'Equipment'),
        ('personnel', 'Personnel'),
        ('land', 'Land'),
        ('warehouse', 'Warehouse'),
        ('other', 'Other'),
    ], string='Resource Type', required=True)
    resource_id = fields.Integer('Resource ID', help='ID of the shared resource (e.g., equipment ID, employee ID)')
    resource_name = fields.Char('Resource Name', compute='_compute_resource_name', store=True, precompute=True)
    start_date = fields.Date('Start Date', required=True)
    end_date = fields.Date('End Date')
    is_active = fields.Boolean('Is Active', default=True)
    sharing_cost = fields.Float('Sharing Cost', help='Cost per unit time or usage')
    sharing_unit = fields.Selection([
        ('hour', 'Hour'),
        ('day', 'Day'),
        ('trip', 'Trip'),
        ('unit', 'Unit'),
    ], string='Sharing Unit', default='day')
    internal_settlement_id = fields.Many2one('internal.settlement', string='Internal Settlement')
    description = fields.Text('Description')

    @api.depends('source_entity_id', 'target_entity_id', 'resource_type', 'resource_id')
    def _compute_name(self):
        for record in self:
            record.name = f"{record.source_entity_id.code} -> {record.target_entity_id.code}: {record.resource_type}({record.resource_id})"

    @api.depends('resource_type', 'resource_id')
    def _compute_resource_name(self):
        for record in self:
            if record.resource_type == 'equipment' and record.resource_id:
                equipment = self.env['fleet.vehicle'].browse(record.resource_id)
                if equipment.exists():
                    record.resource_name = equipment.name
                else:
                    record.resource_name = f"Equipment ID {record.resource_id}"
            elif record.resource_type == 'personnel' and record.resource_id:
                employee = self.env['hr.employee'].browse(record.resource_id)
                if employee.exists():
                    record.resource_name = employee.name
                else:
                    record.resource_name = f"Employee ID {record.resource_id}"
            else:
                record.resource_name = f"{record.resource_type.title()} ID {record.resource_id}"

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.end_date and record.start_date > record.end_date:
                raise ValidationError(_('Start date must be earlier than end date.'))

    def action_create_internal_settlement(self):
        """Create an internal settlement [US-042-03]"""
        for record in self:
            if not record.internal_settlement_id:
                settlement = self.env['internal.settlement'].create({
                    'from_entity_id': record.target_entity_id.id,
                    'to_entity_id': record.source_entity_id.id,
                    'settlement_type': 'resource_rental',
                    'resource_sharing_id': record.id,
                    'amount': record.sharing_cost,
                    'description': f'Resource sharing fee for {record.resource_name}',
                })
                record.internal_settlement_id = settlement.id