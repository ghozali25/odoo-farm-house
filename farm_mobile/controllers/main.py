from odoo import http
from odoo.http import request

class FarmMobileController(http.Controller):

    @http.route('/agri/scan/<string:model>/<int:res_id>', type='http', auth='user')
    def agri_scan_redirect(self, model, res_id, **kwargs):
        """ Scan-code redirect logic [US-002-03] """
        if model == 'location':
            # Jump to the unfinished task linked to this parcel
            task = request.env['project.task'].sudo().search([
                ('land_parcel_id', '=', res_id),
                ('is_closed', '=', False)
            ], limit=1)
            if task:
                return request.redirect('/web#id=%s&model=project.task&view_type=form' % task.id)
            return request.redirect('/web#id=%s&model=stock.location&view_type=form' % res_id)
            
        elif model == 'lot':
            # Jump to the lot detail page
            return request.redirect('/web#id=%s&model=stock.lot&view_type=form' % res_id)
            
        return request.redirect('/web')