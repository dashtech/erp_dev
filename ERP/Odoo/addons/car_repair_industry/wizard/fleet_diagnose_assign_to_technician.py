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

from openerp import fields, models, api, _


class fleet_diagnose_assignto_technician(models.TransientModel):
    _name = 'fleet.diagnose.assignto.technician'
    user_id = fields.Many2one('res.users', string='Technician', required=True)

    def do_assign_technician(self):
        if self.user_id and self._context.get('active_id'):
            self.env['fleet.diagnose'].browse(self._context.get('active_id')).write({'user_id': self.user_id.id, 'state': 'in_progress'})
        return {'type': 'ir.actions.act_window_close'}
