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

import base64
from StringIO import StringIO

import time
import math
from openerp import fields, models, api, _
from openerp.report import report_sxw


class fleet_receipt(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context=None):
        super(fleet_receipt, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
        })
    

class fleet_repair_receipt_template_id(models.AbstractModel):
    _name = 'report.fleet_repair_industry.machi_repa_rece_temp_id'
    _inherit = 'report.abstract_report'
    _template = 'car_repair_industry.machi_repa_rece_temp_id'
    _wrapped_report_class = fleet_receipt

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
