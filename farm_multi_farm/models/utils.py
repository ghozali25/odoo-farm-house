from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class BaseSequenceMixin(models.AbstractModel):
    """
    Mixin: provide standard sequence-number generation
    """
    _name = 'base.sequence.mixin'
    _description = 'Base Sequence Mixin'

    @api.model
    def create(self, vals):
        """Generic create method that generates the name field from a sequence"""
        if vals.get('name', _('New')) == _('New'):
            sequence_code = self._name.replace('.', '_')
            vals['name'] = self.env['ir.sequence'].next_by_code(sequence_code) or '/'
        return super().create(vals)


class BaseCodeMixin(models.AbstractModel):
    """
    Mixin: provide standard code-field generation
    """
    _name = 'base.code.mixin'
    _description = 'Base Code Mixin'

    @api.model
    def create(self, vals):
        """Generic create method that generates the code field from a sequence"""
        if 'code' not in vals or not vals['code']:
            sequence_code = self._name.replace('.', '_')
            vals['code'] = self.env['ir.sequence'].next_by_code(sequence_code) or '/'
        return super().create(vals)


class BaseTotalAmountMixin(models.AbstractModel):
    """
    Mixin: provide standard total-amount computation
    """
    _name = 'base.total.amount.mixin'
    _description = 'Base Total Amount Mixin'

    @api.depends('quantity', 'unit_price')
    def _compute_total_amount(self):
        """Generic total-amount computation method"""
        for record in self:
            record.total_amount = record.quantity * record.unit_price


class BaseInvestmentAmountMixin(models.AbstractModel):
    """
    Mixin: provide investment-amount computation
    """
    _name = 'base.investment.amount.mixin'
    _description = 'Base Investment Amount Mixin'

    @api.depends('shares_count', 'share_price')
    def _compute_total_amount(self):
        """Share-transaction total computation"""
        for record in self:
            record.total_amount = record.shares_count * record.share_price


class BaseServiceAmountMixin(models.AbstractModel):
    """
    Mixin: provide service-amount computation
    """
    _name = 'base.service.amount.mixin'
    _description = 'Base Service Amount Mixin'

    @api.depends('service_quantity', 'unit_rate')
    def _compute_total_amount(self):
        """Service order total computation"""
        for record in self:
            record.total_amount = record.service_quantity * record.unit_rate


class BaseActionConfirmMixin(models.AbstractModel):
    """
    Mixin: provide standard confirm action
    """
    _name = 'base.action.confirm.mixin'
    _description = 'Base Action Confirm Mixin'

    def action_confirm(self):
        """Generic confirm action method"""
        for record in self:
            if record.state == 'draft':
                record.state = 'confirmed'


class BaseActionApproveMixin(models.AbstractModel):
    """
    Mixin: provide standard approve action
    """
    _name = 'base.action.approve.mixin'
    _description = 'Base Action Approve Mixin'

    def action_approve(self):
        """Generic approve action method"""
        for record in self:
            record.state = 'approved'


class BaseActionRejectMixin(models.AbstractModel):
    """
    Mixin: provide standard reject action
    """
    _name = 'base.action.reject.mixin'
    _description = 'Base Action Reject Mixin'

    def action_reject(self):
        """Generic reject action method"""
        for record in self:
            record.state = 'rejected'


class BaseActionCancelMixin(models.AbstractModel):
    """
    Mixin: provide standard cancel action
    """
    _name = 'base.action.cancel.mixin'
    _description = 'Base Action Cancel Mixin'

    def action_cancel(self):
        """Generic cancel action method"""
        for record in self:
            if record.state in ['draft', 'confirmed']:
                record.state = 'cancelled'


class BaseCreditLimitMixin(models.AbstractModel):
    """
    Mixin: provide credit-limit validation
    """
    _name = 'base.credit.limit.mixin'
    _description = 'Base Credit Limit Mixin'

    @api.constrains('credit_limit', 'utilized_amount')
    def _check_credit_limit(self):
        """Validate the credit limit"""
        for record in self:
            if record.utilized_amount > record.credit_limit:
                raise ValidationError(_('Utilized amount cannot exceed credit limit.'))


class BaseLoanAmountMixin(models.AbstractModel):
    """
    Mixin: provide loan-amount validation
    """
    _name = 'base.loan.amount.mixin'
    _description = 'Base Loan Amount Mixin'

    @api.constrains('loan_amount')
    def _check_loan_amount(self):
        """Validate the loan amount"""
        for record in self:
            if record.loan_amount <= 0:
                raise ValidationError(_('Loan amount must be positive.'))


class BaseAvailableAmountMixin(models.AbstractModel):
    """
    Mixin: provide available-amount computation
    """
    _name = 'base.available.amount.mixin'
    _description = 'Base Available Amount Mixin'

    @api.depends('credit_limit', 'utilized_amount')
    def _compute_available_amount(self):
        """Compute the available amount"""
        for record in self:
            record.available_amount = record.credit_limit - record.utilized_amount


class BaseShareValueMixin(models.AbstractModel):
    """
    Mixin: provide share-value computation
    """
    _name = 'base.share.value.mixin'
    _description = 'Base Share Value Mixin'

    @api.depends('shares_held')
    def _compute_share_value(self):
        """Compute the share value"""
        for record in self:
            # Simple calculation - in real implementation this might be based on share price
            record.share_value = record.shares_held * 100.0  # Assuming 100 per share


class BaseTotalInvestmentMixin(models.AbstractModel):
    """
    Mixin: provide total-investment computation
    """
    _name = 'base.total.investment.mixin'
    _description = 'Base Total Investment Mixin'

    @api.depends('share_value')
    def _compute_total_investment(self):
        """Compute the total investment"""
        for record in self:
            # May include other investment types in the future
            record.total_investment = record.share_value


class BaseAvailableCreditMixin(models.AbstractModel):
    """
    Mixin: provide available-credit computation
    """
    _name = 'base.available.credit.mixin'
    _description = 'Base Available Credit Mixin'

    @api.depends('credit_limit', 'credit_used')
    def _compute_available_credit(self):
        """Compute the available credit"""
        for record in self:
            record.available_credit = record.credit_limit - record.credit_used


class BaseComplianceStatusMixin(models.AbstractModel):
    """
    Mixin: provide compliance-status computation
    """
    _name = 'base.compliance.status.mixin'
    _description = 'Base Compliance Status Mixin'

    @api.depends('audit_result')
    def _compute_compliance(self):
        """Compute the compliance status"""
        for record in self:
            record.compliance_status = (record.audit_result == 'authorized')


class BaseCertifiedStatusMixin(models.AbstractModel):
    """
    Mixin: provide certification-status computation
    """
    _name = 'base.certified.status.mixin'
    _description = 'Base Certified Status Mixin'

    @api.depends('quality_score', 'standard_id', 'expiry_date', 'state')
    def _compute_certified_status(self):
        """Compute the certification status"""
        for record in self:
            if (record.state == 'approved' and
                record.quality_score and
                record.standard_id and
                record.quality_score >= record.standard_id.quality_threshold and
                (not record.expiry_date or record.expiry_date >= fields.Date.context_today(self))):
                record.is_certified = True
            else:
                record.is_certified = False


class BaseNetAmountMixin(models.AbstractModel):
    """
    Mixin: provide net-amount computation
    """
    _name = 'base.net.amount.mixin'
    _description = 'Base Net Amount Mixin'

    @api.depends('receivable_amount', 'payable_amount')
    def _compute_net_amount(self):
        """Compute the net amount"""
        for record in self:
            record.net_amount = record.receivable_amount - record.payable_amount


class BaseSettlementDirectionMixin(models.AbstractModel):
    """
    Mixin: provide settlement-direction computation
    """
    _name = 'base.settlement.direction.mixin'
    _description = 'Base Settlement Direction Mixin'

    @api.depends('net_amount')
    def _compute_settlement_direction(self):
        """Compute the settlement direction"""
        for record in self:
            if record.net_amount > 0:
                record.settlement_direction = 'to_member'
            elif record.net_amount < 0:
                record.settlement_direction = 'from_member'
            else:
                record.settlement_direction = False


class BaseAmountCalculationMixin(models.AbstractModel):
    """
    Mixin: provide amount computation
    """
    _name = 'base.amount.calculation.mixin'
    _description = 'Base Amount Calculation Mixin'

    @api.depends('quantity', 'unit_price')
    def _compute_member_amount(self):
        """Compute the member amount"""
        for line in self:
            line.member_amount = line.quantity * line.unit_price

    @api.depends('member_amount')
    def _compute_markup_amount(self):
        """Compute the markup amount"""
        for line in self:
            if line.procurement_id:
                markup_rate = line.procurement_id.markup_rate / 100.0
                line.markup_amount = line.member_amount * markup_rate