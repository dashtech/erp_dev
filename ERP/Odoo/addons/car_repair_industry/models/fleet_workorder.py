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
from datetime import date, time, datetime, timedelta
from odoo.exceptions import UserError, ValidationError


class fleet_workorder(models.Model):
    _name = 'fleet.workorder'
    _inherit = ['mail.thread']
    _order = 'id desc'
    
    name = fields.Char(string='Work Order', required=True)
    sequence = fields.Char(string='Sequence', readonly=True, copy =False)
    client_id = fields.Many2one('res.partner', string='Customer Name', required=True)
    client_phone = fields.Char(string='Phone')
    client_mobile = fields.Char(string='Mobile')
    client_email = fields.Char(string='Email')
    date_planned = fields.Datetime(string='Scheduled Date')
    date_planned_end = fields.Datetime(string='End Date')
    cycle = fields.Float(string='Number of Cycles')
    hour = fields.Float(string='Number of Hours')
    date_start = fields.Datetime(string='Start Date', readonly=True, default=fields.Datetime.now)
    date_finished = fields.Date(string='Delivery Date')
    delay = fields.Float(string='Working Hours', readonly=True)
    hours_worked = fields.Float(string='Hours Worked')
    state = fields.Selection([('draft','Draft'),('cancel','Cancelled'),('pause','Pending'),('startworking', 'In Progress'),('done','Finished')],'Status', readonly=True, copy=False,
                               help="* When a work order is created it is set in 'Draft' status.\n" \
                                       "* When user sets work order in start mode that time it will be set in 'In Progress' status.\n" \
                                       "* When work order is in running mode, during that time if user wants to stop or to make changes in order then can set in 'Pending' status.\n" \
                                       "* When the user cancels the work order it will be set in 'Canceled' status.\n" \
                                       "* When order is completely processed that time it is set in 'Finished' status.")
    fuel_type = fields.Selection([('gasoline', 'Gasoline'), ('diesel', 'Diesel'), ('electric', 'Electric'), ('hybrid', 'Hybrid')], 'Fuel Type', help='Fuel Used by the vehicle')
    service_type_ids = fields.Many2many('service.type', string='Nature of Service')
    user_id = fields.Many2one('res.users', string='Technician')
    priority = fields.Selection([('0','Low'), ('1','Normal'), ('2','High')], 'Priority')
    description = fields.Text(string='Description')
    est_ser_hour = fields.Float(string='Estimated Sevice Hours')
    service_product_price = fields.Integer('Service Product Price')
    fleet_repair_id = fields.Many2one('fleet.repair', string='Car Repair', copy=False, readonly=True)
    diagnose_id = fields.Many2one('fleet.diagnose', string='Car Diagnosis', copy=False, readonly=True)
    sale_order_id = fields.Many2one('sale.order', string='Sales Order', copy=False, readonly=True)
    count_fleet_repair = fields.Integer(string="Invoice", compute='_compute_fleet_repair_id')
    count_dig = fields.Integer(string="Invoice", compute='_compute_dig_id')
    confirm_sale_order = fields.Boolean('is confirm')
    saleorder_count = fields.Integer(string="Sale Order", compute='_compute_saleorder_id')
    fleet_repair_line = fields.Many2many('fleet.vehicle', string='Car Information')

    order_lines = fields.One2many('sale.order.line', 'workorder_id', 'Order Line')
    service_lines = fields.One2many('repair.order.line', 'workorder_id', 'Order Line')
    service_lines_state_pause = fields.Boolean(compute="_compute_service_lines_state_pause")
    service_lines_state_assignee = fields.Boolean(compute="_compute_service_lines_state_assignee")
    real_start_date = fields.Char('Real Date', compute='get_real_date')
    real_finish_date_date = fields.Char('Real Date', compute='get_real_date')

    license_plate = fields.Char('License Plate')
    car_name = fields.Char('Car Name')
    vin_sn = fields.Char('Chassis Number')
    company_id = fields.Many2one('res.company', string='Company')
    done_date = fields.Datetime(readonly=True)

    @api.multi
    def open_assignee_line(self):
        action_obj = \
            self.env.ref(
                'car_repair_industry.action_fleet_workorder_assignee_line_user')
        action = action_obj.read([])[0]

        action['res_id'] = self[0].id
        return action

    @api.multi
    def save(self):
        return True

    @api.one
    @api.depends('date_start', 'date_finished')
    def get_real_date(self):
        if self.date_start:
            real_date = datetime.strptime(self.date_start, '%Y-%m-%d %H:%M:%S') + timedelta(hours=7)
            self.real_start_date = str(datetime.strftime(real_date, '%d-%m-%Y %H:%M:%S'))
        if self.date_finished:
            real_date = datetime.strptime(self.date_finished, '%Y-%m-%d') + timedelta(hours=7)
            self.real_finish_date_date = str(datetime.strftime(real_date, '%d-%m-%Y'))

    @api.multi
    @api.depends('fleet_repair_id')
    def _compute_fleet_repair_id(self):
        for order in self:
            repair_order_ids = self.env['fleet.repair'].search([('workorder_id', '=', order.id)])            
            order.count_fleet_repair = len(repair_order_ids)

    @api.multi
    @api.depends('diagnose_id')
    def _compute_dig_id(self):
        for order in self:
            work_order_ids = self.env['fleet.diagnose'].search([('fleet_repair_id.workorder_id', '=', order.id)])            
            order.count_dig = len(work_order_ids)
  
    @api.multi
    @api.depends('confirm_sale_order')
    def _compute_saleorder_id(self):
        for order in self:
            so_order_ids = self.env['sale.order'].search([('state', '=', 'sale'),('workorder_id', '=', order.id)])            
            order.saleorder_count = len(so_order_ids)          
            
            
    @api.multi
    def button_view_repair(self):
        list = []
        context = dict(self._context or {})
        repair_order_ids = self.env['fleet.repair'].search([('workorder_id', '=', self.id)])         
        for order in repair_order_ids:
            list.append(order.id)
        return {
            'name': _('Phiếu yêu cầu'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'fleet.repair',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in',list )],
            'context': context,
        }


    @api.multi
    def button_view_diagnosis(self):
        list = []
        context = dict(self._context or {})
        dig_order_ids = self.env['fleet.diagnose'].search([('fleet_repair_id.workorder_id', '=', self.id)])           
        for order in dig_order_ids:
            list.append(order.id)
        return {
            'name': _('Phiếu khám xe'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'fleet.diagnose',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in',list )],
            'context': context,
        }

    @api.multi
    def button_view_saleorder(self):
        list = []
        context = dict(self._context or {})
        order_ids = self.env['sale.order'].search([('state', '=', 'sale'),('workorder_id', '=', self.id)])           
        for order in order_ids:
            list.append(order.id)
        return {
            'name': _('Đơn hàng'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in',list )],
            'context': context,
        }

    @api.multi
    def button_cancel(self):
        fleet_repair = self.env['fleet.repair'].search([('id', '=', self.fleet_repair_id.id)])
        wo_line = self.env['repair.order.line'].search([('workorder_id', '=', self.id)])
        if wo_line:
            for wo_id in wo_line:
                if wo_id.repair_state == 'done':
                    raise ValidationError(_('You can not cancel Work Order when completed Work Order detail!'))
        fleet_repair.write({'state': 'saleorder'})
        return self.write({'state': 'cancel'})

    @api.multi
    def button_resume(self):
        # wo_line = self.env['repair.order.line'].search([('workorder_id', '=', self.id)])
        # if wo_line:
        #     for wo_id in wo_line:
        #         wo_id.write({'repair_state': 'start'})
        return self.write({'state': 'startworking'})

    @api.multi
    def button_pause(self):
        return self.write({'state': 'pause'})

    @api.multi
    def button_draft(self):
        fleet_repair = self.env['fleet.repair'].search([('id', '=', self.fleet_repair_id.id)])
        fleet_repair.write({'state': 'workorder'})
        return self.write({'state': 'draft'})

    @api.multi
    def action_start_working(self):
        """ Sets state to start working and writes starting date.
        @return: True
        """
        wo_line = self.env['repair.order.line'].search([('workorder_id', '=', self.id)])
        if wo_line:
            for wo_id in wo_line:
                wo_id.write({'repair_state': 'start'})
        self.write({'state':'startworking', 'date_start': datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')})
        if self.fleet_repair_id:
            self.fleet_repair_id.sudo(1).write({'state': 'workorder'})
        return True

    @api.multi
    def action_done(self):
        """ Sets state to done, writes finish date and calculates delay.
        @return: True
        """

        delay = 0.0
        date_now = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M:%S')

        date_start = datetime.strptime(self.date_start,'%Y-%m-%d %H:%M:%S')
        date_finished = datetime.strptime(date_now,'%Y-%m-%d %H:%M:%S')
        delay += (date_finished-date_start).days * 24
        delay += (date_finished-date_start).seconds / float(60*60)

        self.write({
            'state': 'done',
            'done_date': date_now,
            'delay': delay
        })
        # if self.sale_order_id:
        #     self.sale_order_id.sudo(1).write({'state': 'sale'})
        if self.fleet_repair_id:
            self.fleet_repair_id.sudo(1).write({'state': 'work_completed'})

        for service_line in self.service_lines:
            if service_line.repair_state != 'done':
                service_line.sudo().write({'repair_state': 'done'})
        return True

    @api.multi
    def work_lines_layouted(self):
        """
        Returns this order lines classified by sale_layout_category and separated in
        pages according to the category pagebreaks. Used to render the report.
        """
        self.ensure_one()
        report_pages = [[]]
        work_order = []
        prod_order = []
        for wo_id in self.service_lines:
            work_order.append(wo_id)

        for prod_id in self.order_lines:
            prod_order.append(prod_id)

        report_pages[-1].append({
            'work_order': work_order,
            'prod_order': prod_order
        })

        return report_pages

    @api.multi
    @api.depends('service_lines.repair_state')
    def _compute_service_lines_state_pause(self):
        for s in self:
            s.service_lines_state_pause = True
            if s.state == 'startworking':
                if not s.service_lines:
                    s.service_lines_state_pause = False
                for service_line in s.service_lines:
                    if service_line.repair_state != 'done':
                        s.service_lines_state_pause = False
                        break

    @api.multi
    @api.depends('service_lines.repair_state')
    def _compute_service_lines_state_assignee(self):
        for s in self:
            s.service_lines_state_assignee = True
            if s.state in ('draft', 'pause', 'startworking'):
                if not s.service_lines:
                    s.service_lines_state_assignee = False
                for service_line in s.service_lines:
                    if service_line.repair_state != 'done':
                        s.service_lines_state_assignee = False
                        break

    def auto_done(self):
        self.ensure_one()
        if self.state == 'draft':
            self.action_start_working()
        if self.state == 'startworking':
            self.action_done()
        if self.state == 'pause':
            self.button_resume()
            self.action_done()
        return True