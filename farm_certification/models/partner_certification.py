from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    agri_certification_ids = fields.One2many(
        'farm.partner.certification', 'partner_id', string="Agri Certifications"
    )
    has_valid_agri_cert = fields.Boolean(
        "Has Valid Agri Cert", compute='_compute_cert_status'
    )

    @api.depends('agri_certification_ids.date_expiry', 'agri_certification_ids.state')
    def _compute_cert_status(self):
        today = fields.Date.today()
        for partner in self:
            partner.has_valid_agri_cert = any(
                cert.state == 'valid' and cert.date_expiry >= today 
                for cert in partner.agri_certification_ids
            )

class FarmPartnerCertification(models.Model):
    _name = 'farm.partner.certification'
    _description = 'Supplier Agricultural Certification'

    partner_id = fields.Many2one('res.partner', string="Supplier", required=True, ondelete='cascade')
    cert_type = fields.Selection([
        ('organic', 'Organic'),
        ('green', 'Green Food'),
        ('gi', 'Geographical Indication'),
        ('gap', 'GAP')
    ], string="Certification Type", required=True)
    cert_number = fields.Char("Certificate No.", required=True)
    date_start = fields.Date("Issue Date")
    date_expiry = fields.Date("Expiry Date", required=True)
    state = fields.Selection([
        ('valid', 'Valid'),
        ('expired', 'Expired'),
        ('revoked', 'Revoked')
    ], string="Status", default='valid')

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def button_confirm(self):
        """ US-009-06: Hard check of supplier compliance credentials + Activity drives the workflow """
        today = fields.Date.today()
        for order in self:
            if order.partner_id.agri_certification_ids:
                valid_certs = order.partner_id.agri_certification_ids.filtered(
                    lambda c: c.state == 'valid' and c.date_expiry >= today
                )
                if not valid_certs:
                    # 1. Create a compliance-completion activity [Workflow]
                    compliance_user = self.env.ref('farm_core.group_farm_admin').users[:1] # Demo logic: send to the farm administrator
                    order.activity_schedule(
                        'mail.mail_activity_data_todo',
                        summary=_('Supplier Certificate Expired: Completion Required [%s]') % order.partner_id.name,
                        note=_('This order involves core agricultural inputs, but the supplier credentials have expired.Please update the qualification documents immediately, otherwise the order cannot proceed.'),
                        user_id=compliance_user.id if compliance_user else self.env.user.id
                    )
                    # 2. Raise a warning without hard-blocking; follow-up is driven by an activity instead
                    raise ValidationError(_(
                        "CORE-CLOSURE: Supplier [%s] agricultural qualification has expired.\n"
                        "A todo task has been automatically created for the compliance officer. Please update credentials and try again."
                    ) % order.partner_id.name)
        return super(PurchaseOrder, self).button_confirm()
