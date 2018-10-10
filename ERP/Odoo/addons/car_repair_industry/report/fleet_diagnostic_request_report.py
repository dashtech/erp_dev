# -*- coding: utf-8 -*-
##############################################################################
#
#    This module uses OpenERP, Open Source Management Solution Framework.
#    Copyright (C) 2015-Today BrowseInfo (<http://www.browseinfo.in>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################


import time
from openerp.osv import osv
from openerp.report import report_sxw


class fleet_diagnostic_request(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        super(fleet_diagnostic_request, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
        })
    

class fleet_diagnostic_request_template_id(osv.AbstractModel):
    _name = 'report.fleet_repair_industry.machi_diagn_req_temp_id'
    _inherit = 'report.abstract_report'
    _template = 'car_repair_industry.machi_diagn_req_temp_id'
    _wrapped_report_class = fleet_diagnostic_request

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
