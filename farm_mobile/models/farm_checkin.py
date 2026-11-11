from odoo import models, fields, api, _
from odoo.exceptions import UserError

class FarmCheckIn(models.Model):
    """
    US-007-04 & US-036-03: On-site check-in records and geo-location verification
    """
    _name = 'farm.checkin'
    _description = 'Agri Site Check-in'
    _inherit = ['mail.thread']
    _order = 'check_in_time desc'

    name = fields.Char("Check-in ID", required=True, copy=False, readonly=True, default=lambda self: _('New'))
    worker_id = fields.Many2one('hr.employee', string="Worker", default=lambda self: self.env.user.employee_id, required=True)
    intervention_id = fields.Many2one('mrp.production', string="Intervention/Task", required=True)
    
    check_in_time = fields.Datetime("Check-in Time", default=fields.Datetime.now)
    check_out_time = fields.Datetime("Check-out Time")
    
    # Geo-location capture
    gps_lat = fields.Float("Check-in Latitude", digits=(10, 7))
    gps_lng = fields.Float("Check-in Longitude", digits=(10, 7))
    
    # Site photo [US-054-04]
    checkin_photo = fields.Binary("Site Photo", attachment=True)
    
    # Verification result
    is_on_site = fields.Boolean("On-site Verified", compute='_compute_site_verification', store=True, precompute=True)
    site_distance = fields.Float("Distance to Site (m)", compute='_compute_site_verification', store=True, precompute=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('farm.checkin') or _('CI')
        return super().create(vals_list)

#    @api.depends('gps_lat', 'gps_lng', 'intervention_id.land_parcel_id')
    def _compute_site_verification(self):
        """ Check whether the check-in location is within the task parcel [US-053-01] """
        for rec in self:
            parcel = rec.intervention_id.agri_task_id.land_parcel_id
            if not parcel or not parcel.gps_coordinates or not rec.gps_lat:
                rec.is_on_site = False
                continue
            
            # Use the geofence logic implemented in Epic 23
            # Here simplified to checking whether the coordinates are inside the parcel.gps_coordinates fence
            temp_fence = self.env['agri.geospatial.geofence'].new({
                'coordinates': parcel.gps_coordinates
            })
            rec.is_on_site = temp_fence.is_point_inside(rec.gps_lng, rec.gps_lat)

class AgriIntervention(models.Model):
    _inherit = 'mrp.production'

    check_in_ids = fields.One2many('farm.checkin', 'intervention_id', string="Check-in History")
    evidence_ids = fields.One2many('agri.evidence', 'res_id', string="Site Evidence", domain=[('res_model', '=', 'mrp.production')])
    
    current_check_in_id = fields.Many2one('farm.checkin', string="Active Check-in", compute='_compute_active_checkin')

    def action_mobile_capture_evidence(self, lat, lng, photo_base64, note=""):
        """ Mobile-only：on-site evidence capture [US-007-05] """
        self.ensure_one()
        return self.env['agri.evidence'].create({
            'name': _('Evidence: %s') % self.name,
            'res_model': 'mrp.production',
            'res_id': self.id,
            'gps_lat': lat,
            'gps_lng': lng,
            'photo': photo_base64,
            'note': note
        })

    def _compute_active_checkin(self):
        for mo in self:
            mo.current_check_in_id = self.env['farm.checkin'].search([
                ('intervention_id', '=', mo.id),
                ('check_out_time', '=', False)
            ], limit=1)

    def action_mobile_check_in(self, lat, lng, photo_base64=False):
        """ Mobile check-in API: add a hard checklist gate """
        self.ensure_one()
        
        # 1. 1. Check whether the tools used require a checklist [US-056-03]
        for tool in self.tool_ids:
            if tool.checklist_id:
                # Find the most recent checklist submission
                submission = self.env['farm.checklist.submission'].search([
                    ('equipment_id', '=', tool.id),
                    ('task_id', '=', self.id),
                    ('state', '=', 'pass')
                ], limit=1)
                if not submission:
                    raise UserError(_("SAFETY BLOCK: Please complete the PRE-OP CHECKLIST for %s before starting!") % tool.name)

        # 2. Record the check-in
        checkin = self.env['farm.checkin'].create({
            'intervention_id': self.id,
            'gps_lat': lat,
            'gps_lng': lng,
            'checkin_photo': photo_base64
        })
        
        # 2. Record the check-in; trigger the native start-work logic
        self.action_start_work()
        
        if not checkin.is_on_site:
            self.message_post(body=_("WARNING: Worker checked in OUTSIDE the parcel boundary!"))
        
        return checkin.id

    def action_mobile_check_out(self):
        """ Mobile check-out API: auto-sync the timesheet """
        self.ensure_one()
        if self.current_check_in_id:
            now = fields.Datetime.now()
            checkin = self.current_check_in_id
            checkin.write({'check_out_time': now})
            
            # Auto-create Timesheet [US-054-03]
            # Compute the hours
            duration_hrs = (now - checkin.check_in_time).total_seconds() / 3600.0
            
            if duration_hrs > 0:
                self.env['account.analytic.line'].create({
                    'name': _("Check-in: %s") % self.name,
                    'project_id': self.agri_task_id.project_id.id,
                    'task_id': self.agri_task_id.id,
                    'employee_id': checkin.worker_id.id,
                    'unit_amount': duration_hrs,
                    'date': fields.Date.today(),
                })
            
            self.action_stop_work()
