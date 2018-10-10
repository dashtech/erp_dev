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
from datetime import datetime, timedelta
from openerp import tools
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import re


# class SurveyLabel(models.Model):
#     _inherit = "survey.label"
#
#     color = fields.Selection(string="Color", selection=[('radio-primary', 'Primary'),
#                                                         ('radio-danger', 'Danger'),
#                                                         ('radio-info', 'Info'),
#                                                         ('radio-warning', 'Warning'),
#                                                         ('radio-success', 'Success')], default="radio-success")


class fleet_repair(models.Model):
    _name = 'fleet.repair'
    _inherit = ['mail.thread']
    _order = 'id desc'
    _rec_name = 'name'

    def _current_company(self):
        company_id = self.env.user.company_id.id
        return company_id

    name = fields.Char(string='Name', compute='get_name')
    sequence = fields.Char(string='Sequence', readonly=True, copy=False)
    client_id = fields.Many2one('res.partner', string='Customer Name', required=True)
    client_phone = fields.Char(string='Phone', related='client_id.phone')
    client_mobile = fields.Char(related='client_id.mobile',store=False, readonly=False, string='Mobile')
    client_email = fields.Char(string='Email', related='client_id.email')
    client_addr = fields.Char('Address')
    contact_name = fields.Char(string='Contact Name')
    fleet_id = fields.Many2one('fleet.vehicle', 'Car')
    model_id = fields.Many2one('fleet.vehicle.model', 'Model', help='Model of the vehicle')
    guarantee = fields.Selection(
              [('yes', 'Yes'), ('no', 'No')], string='Under Guarantee?')
    guarantee_type = fields.Selection(
            [('paid', 'paid'), ('free', 'Free')], string='Guarantee Type')
    service_type_ids = fields.Many2many('service.type', string='Service', required=True)
    service_type = fields.Many2one('service.type', string='Service')
    user_id = fields.Many2one('res.users', string='Assigned To')
    priority = fields.Selection([('0','Low'), ('1','Normal'), ('2','High')], 'Priority')
    description = fields.Text(string='Customer Requests')
    state = fields.Selection([
            ('draft', 'Received'),
            ('diagnosis', 'In Diagnosis'),
            ('diagnosis_complete', 'Diagnosis Complete'),
            ('quote', 'Quotation Sent'),
            ('saleorder', 'Quotation Approved'),
            ('workorder', 'Work in Progress'),
            ('work_completed', 'Work Completed'),
            ('invoiced', 'Invoiced'),
            ('done', 'Done'),
            ('cancel', 'Cancelled'),
            ], 'Status', default = "draft",readonly=True, copy=False, help="Gives the status of the fleet repairing.", select=True)
    diagnose_id = fields.Many2one('fleet.diagnose', string='Car Diagnose', copy=False)
    workorder_id = fields.Many2one('fleet.workorder', string='Car Work Order', copy=False)
    sale_order_id = fields.Many2one('sale.order', string='Sales Order', copy=False)
    workorder_count = fields.Integer(string='Work Orders', compute='_compute_workorder_id')
    dig_count  = fields.Integer(string='Diagnosis Orders', compute='_compute_dignosis_id')
    quotation_count = fields.Integer(string="Quotations", compute='_compute_quotation_id')
    saleorder_count = fields.Integer(string="Sale Order", compute='_compute_quotation_id')
    upsell_count = fields.Integer(string="Upsell", compute='_compute_upsell_count')
    inv_count = fields.Integer(string="Invoice", compute='_compute_invoice_id')
    confirm_sale_order = fields.Boolean('is confirm')
    car_image = fields.image_medium = fields.Binary('Car Image', compute='get_car_info')
    license_plate = fields.Char('License Plate', compute='get_car_info', store=True)
    car_name = fields.Char('Car Name', compute='get_car_info')
    car_color = fields.Char('Car Color', compute='get_car_info')
    vin_sn = fields.Char('Chassis Number', compute='get_car_info')
    date_receipt = fields.Char('Car Pick Up Date', compute='_get_pick_up')
    service_name = fields.Char('Service Name', compute='get_name')
    # date_delivery = fields.Char('Start Work', compute='_get_date_delivery')
    receipt_date = fields.Datetime(string='Car Delivery Time', default=fields.Datetime.now)

    check_signup = fields.Boolean('Registration CarGO')
    fleet_repair_line = fields.Many2many('fleet.vehicle', string='Car Information', required=True)

    kanban_state = fields.Selection([
        ('blocked', 'Not Work'),
        ('normal', 'Working'),
        ('done', 'Done'),
    ], string='Kanban State', compute='_compute_state',
        copy=False, store=True)
    company_id = fields.Many2one('res.company', default=_current_company , string='Company')



    @api.multi
    def _compute_upsell_count(self):
        querry = """
                    select f.id, count(o.id)
                    from fleet_repair as f
                    left join sale_order as o
                    on o.fleet_repair_id = f.id
                    and o.state = 'draft'
                    and o.upsell = true
                    where f.id in ({})
                    group by f.id
                """.format(','.join([str(id) for id in self._ids]))
        self.env.cr.execute(querry)
        result_dict = \
            dict((row[0], row[1] or 0) for row in self.env.cr.fetchall())

        for f in self:
            f.upsell_count = result_dict.get(f.id, 0)

    @api.one
    @api.depends('sequence', 'service_type_ids')
    def get_name(self):
        if self.service_type_ids:
            name = ''
            count = 0
            for service_id in self.service_type_ids:
                name += ' & ' if count >= 1 else ''
                count += 1
                name += service_id.name
            self.service_name = name
            self.name = self.sequence + '-' + name

    @api.one
    @api.depends('state')
    def _compute_state(self):
        if self.state in ['draft']:
            self.kanban_state = 'blocked'
        elif self.state in ['work_completed', 'invoiced', 'done']:
            self.kanban_state = 'done'
        elif self.state not in ['draft', 'cancel', 'work_completed', 'invoiced', 'done']:
            self.kanban_state = 'normal'

    @api.onchange('client_id')
    def onchange_partner_id(self):
        if self.client_id:
            self.client_addr = self.client_id.street if self.client_id.street else '' + \
                                self.client_id.street2 if self.client_id.street2 else '' + \
                                self.client_id.state_id.name if self.client_id.state_id else '' + \
                                self.client_id.country_id.name if self.client_id.country_id else ''
            if self.client_id.mobile:
                self.client_mobile = self.client_id.mobile


    @api.one
    @api.depends('fleet_repair_line')
    def get_car_info(self):
        if self.fleet_repair_line:
            license_plate = ''
            count = 0
            for record in self.fleet_repair_line:
                count += 1
                self.car_image = record.image_medium
                # name_brand = record.model_id.brand_id.name if record.model_id.brand_id else ''
                name_model = record.model_id.name_get()[0][1] if record.model_id else ''
                self.car_name = name_model
                if record.color_id:
                    self.car_color = record.color_id.name
                else:
                    self.car_color = ' '
                self.vin_sn = record.vin_sn
                license_plate += record.license_plate
                if count < len(self.fleet_repair_line) and len(self.fleet_repair_line) > 1:
                    license_plate += ', '
                if record.driver_id.id:
                    self.client_id = record.driver_id.id
                else:
                    old_repair = self.search([('fleet_repair_line', 'in', record.id)], limit=1)
                    self.client_id = old_repair.client_id.id
            self.license_plate = license_plate

    @api.one
    @api.depends('create_date')
    def _get_pick_up(self):
        if self.create_date:
            real_date = datetime.strptime(self.create_date, '%Y-%m-%d %H:%M:%S') + timedelta(hours=7)
            self.date_receipt = str(datetime.strftime(real_date, '%d-%m-%Y %H:%M:%S'))

    @api.model
    def create(self, vals):
        vals['sequence'] = self.env['ir.sequence'].sudo().next_by_code('fleet.repair')
        if vals.get('client_email'):
            if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", vals['client_email']) != None:
                pass
            else:
                raise ValidationError(_("Email format invalid. Please enter again!"))
        vals['company_id'] = self.env.user.company_id.id
        res = super(fleet_repair, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        res = super(fleet_repair, self).write(vals)
        if vals.get('client_email'):
            if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", vals['client_email']) != None:
                return True
            else:
                raise ValidationError(_('Email format invalid. Please enter again!'))
        return res

    @api.multi
    def button_view_diagnosis(self):
        list = []
        context = dict(self._context or {})
        dig_order_ids = self.env['fleet.diagnose'].search([('fleet_repair_id', '=', self.id)])           
        for order in dig_order_ids:
            list.append(order.id)
        return {
            'name': _('Phiếu khám'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'fleet.diagnose',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in',list )],
            'context': context,
        }

    @api.multi
    def button_view_workorder(self):
        list = []
        context = dict(self._context or {})
        work_order_ids = self.env['fleet.workorder'].search([('fleet_repair_id', '=', self.id)])           
        for order in work_order_ids:
            list.append(order.id)
        return {
            'name': _('Lệnh làm việc'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'fleet.workorder',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in',list )],
            'context': context,
        }

    @api.multi
    def button_view_quotation(self):
        list = []
        context = dict(self._context or {})
        quo_order_ids = self.env['sale.order'].search([('state', '=', 'draft'), ('fleet_repair_id', '=', self.id),('upsell', '=', False)])
        for order in quo_order_ids:
            list.append(order.id)
        return {
            'name': _('Báo giá'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', list)],
            'context': context,
        }

    @api.multi
    def button_view_upsell(self):
        context = dict(self._context or {})
        domain = [('state', '=', 'draft'),
                  ('fleet_repair_id', '=', self.id),
                  ('upsell', '=', True)]

        return {
            'name': _('Upsell'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': domain,
            'context': context,
        }
  
    @api.multi
    def button_view_saleorder(self):
        list = []
        context = dict(self._context or {})
        quo_order_ids = self.env['sale.order'].search(
            [('state', '=', ('sale', 'done')),('fleet_repair_id', '=', self.id)])
        for order in quo_order_ids:
            list.append(order.id)
        return {
            'name': _('Đơn hàng'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', list)],
            'context': context,
        }
 
    @api.multi
    def button_view_invoice(self):
        list = []
        inv_list  = []
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('account.action_invoice_tree1')
        list_view_id = imd.xmlid_to_res_id('account.invoice_tree')
        form_view_id = imd.xmlid_to_res_id('account.invoice_form')
        so_order_ids = self.env['sale.order'].search([('state', '=', ('sale', 'done')),('fleet_repair_id', '=', self.id)])
        for order in so_order_ids:
            inv_order_ids = self.env['account.invoice'].search([('origin', '=',order.name )])            
            if inv_order_ids:
                for order_id in inv_order_ids:
                    if order_id.id not in list:
                        list.append(order_id.id)
                            
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'], [False, 'calendar'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(list) > 1:
            result['domain'] = "[('id','in',%s)]" % list
        elif len(list) == 1:
            result['views'] = [(form_view_id, 'form')]
            result['res_id'] = list[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    @api.multi
    @api.depends('workorder_id')
    def _compute_workorder_id(self):
        for order in self:
            work_order_ids = self.env['fleet.workorder'].search([('fleet_repair_id', '=', order.id)])            
            order.workorder_count = len(work_order_ids)

    @api.multi
    @api.depends('diagnose_id')
    def _compute_dignosis_id(self):
        for order in self:
            dig_order_ids = self.env['fleet.diagnose'].search([('fleet_repair_id', '=', order.id)])            
            order.dig_count = len(dig_order_ids)

    @api.multi
    @api.depends('sale_order_id')
    def _compute_quotation_id(self):
        for order in self:
            quo_order_ids = self.env['sale.order'].search(
                [('state', '=', 'draft'),('fleet_repair_id', '=', order.id),
                 ('upsell', '=', False)])
            order.quotation_count = len(quo_order_ids)
            so_order_ids = self.env['sale.order'].search(
                [('state', '=', ('sale', 'done')),
                 ('fleet_repair_id', '=', order.id)])
            order.saleorder_count = len(so_order_ids)

    @api.multi
    @api.depends('state')
    def _compute_invoice_id(self):
        for record in self:
            if record.state in ('invoiced', 'done'):
                for order in record:
                    so_order_ids = self.env['sale.order'].search([('state', '=', ('sale', 'done')),
                                                                  ('fleet_repair_id', '=', order.id)])
                    count = 0
                    for so_id in so_order_ids:
                        inv_order_ids = self.env['account.invoice'].search([('origin', '=', so_id.name )])
                        if inv_order_ids:
                            count += len(inv_order_ids)
                    self.inv_count = count

    @api.multi
    def diagnosis_created(self):
        self.write({'state':'diagnosis'})

    @api.multi
    def quote_created(self):
        self.write({'state':'quote'})

    @api.multi
    def order_confirm(self):
        self.write({'state':'saleorder'})

    @api.multi
    def fleet_confirmed(self):
        self.write({'state':'confirm'})

    @api.multi
    def workorder_created(self):
        self.write({'state':'workorder'})

    @api.multi
    def action_create_fleet_diagnosis(self):
        Diagnosis_obj = self.env['fleet.diagnose']
        repair_obj = self.env['fleet.repair'].browse(self._ids[0])
        mod_obj = self.env['ir.model.data']
        act_obj = self.env['ir.actions.act_window']
        if not repair_obj.fleet_repair_line:
            raise Warning('You cannot create Car Diagnosis without Cars.')
        
        diagnose_vals = {
            'service_rec_no': repair_obj.sequence,
            'name': repair_obj.name,
            'priority': repair_obj.priority,
            'receipt_date': repair_obj.receipt_date,
            'client_id': repair_obj.client_id.id,
            'contact_name': repair_obj.contact_name,
            'client_phone': repair_obj.client_phone,
            'client_mobile': repair_obj.client_mobile,
            'client_email': repair_obj.client_email,
            'fleet_repair_id': repair_obj.id,
            'state': 'draft',
            'fleet_repair_line': [(6, 0, repair_obj.fleet_repair_line.ids)],
            'service_type_ids': [(6, 0, repair_obj.service_type_ids.ids)],
            'user_id': repair_obj.user_id.id,
            'description': repair_obj.description,
            'car_name': repair_obj.car_name,
            'license_plate': repair_obj.license_plate,
            'vin_sn': repair_obj.vin_sn,
        }
        diagnose_id = Diagnosis_obj.create(diagnose_vals)

        self.write({'state': 'diagnosis', 'diagnose_id': diagnose_id.id})
        result = mod_obj.get_object_reference('car_repair_industry', 'action_fleet_diagnose_tree_view')
        id = result and result[1] or False
        result = act_obj.browse(id).read()[0]
        res = mod_obj.get_object_reference('car_repair_industry', 'view_fleet_diagnose_form')
        result['views'] = [(res and res[1] or False, 'form')]
        result['res_id'] = diagnose_id.id or False
        return result

    @api.multi
    def prepare_line_order(self):
        # for service_id in self.service_type_ids:
        product_services = self.env['product.product'].search([['service_type_id', 'in', self.service_type_ids.ids]])

        order_line_service = []
        order_line = []
        for ps in product_services:
            if ps.type == 'service':
                order_line_service.append(
                    [0, False, {'product_id': ps.id, 'product_uom_qty': 1}])
            if ps.type in ('product', 'consu'):
                order_line.append(
                    [0, False, {'product_id': ps.id, 'product_uom_qty': 1}])
        return order_line_service, order_line

    @api.multi
    def action_create_quotation(self):
        mod_obj = self.env['ir.model.data']
        act_obj = self.env['ir.actions.act_window']
        order_line_service, order_line = self.prepare_line_order()
        quote_vals = {
            'partner_id': self.client_id.id or False,
            'state': 'draft',
            'client_order_ref': self.name,
            'diagnose_id': False,
            'fleet_repair_id': self.id,
            'fleet_ids': [(6, 0, self.fleet_repair_line.ids)],
            'service_type_ids': [(6, False, self.service_type_ids._ids)],
            'create_form_fleet': True,
            'license_plate': self.license_plate,
            'car_name': self.car_name,
            'vin_sn': self.vin_sn,
            'order_line_service': order_line_service,
            'order_line': order_line,
            'description': self.description,
        }

        order_id = self.env['sale.order'].create(quote_vals)
        order_id.service_type_ids_change()

        result = mod_obj.get_object_reference('car_repair_industry', 'action_saleorder1')
        id = result and result[1] or False
        result = act_obj.browse(id).read()[0]
        res = mod_obj.get_object_reference('car_repair_industry', 'repair_view_order_form')
        result['views'] = [(res and res[1] or False, 'form')]
        result['res_id'] = order_id.id or False
        self.write({'sale_order_id': order_id.id, 'state': 'quote'})
        return result

    @api.multi
    def action_print_receipt(self):
        assert len(self._ids) == 1, 'This option should only be used for a single id at a time'
        return self.env['report'].get_action(self._ids[0],'car_repair_industry.machi_repa_rece_temp_id')

    @api.multi
    def action_print_label(self):
        if not self.fleet_repair_line:
            raise UserError(_('You cannot print report without Car details'))

        assert len(self._ids) == 1, 'This option should only be used for a single id at a time'
        return self.env['report'].get_action(self._ids[0],'car_repair_industry.machi_rep_label_temp_id')

    @api.multi
    def action_create_view_quotation(self):
        mod_obj = self.env['ir.model.data']
        act_obj = self.env['ir.actions.act_window']
        order_line_service, order_line = self.prepare_line_order()
        if self.saleorder_count >= 1:
            list = []
            context = dict(self._context or {})
            quo_order_ids = self.env['sale.order'].search([('state', '=', ('sale', 'done')), ('fleet_repair_id', '=', self.id)])
            for order in quo_order_ids:
                list.append(order.id)
            return {
                'name': _('Báo giá'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'sale.order',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', list)],
                'context': context,
            }
        elif self.quotation_count >= 1:
            list = []
            context = dict(self._context or {})
            quo_order_ids = self.env['sale.order'].search([('state', '=', 'draft'), ('fleet_repair_id', '=', self.id)])
            for order in quo_order_ids:
                list.append(order.id)
            return {
                'name': _('Đơn hàng'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'sale.order',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', list)],
                'context': context,
            }
        else:
            quote_vals = {
                'fleet_ids': [(6, 0, self.fleet_repair_line.ids)],
                'partner_id': self.client_id.id or False,
                'client_order_ref': self.name,
                'fleet_repair_id': self.id,
                'create_form_fleet': True,
                'license_plate': self.license_plate,
                'car_name': self.car_name,
                'vin_sn': self.vin_sn,
                'order_line_service': order_line_service,
                'order_line': order_line,
                'description': self.description
            }
            order_id = self.env['sale.order'].create(quote_vals)

            result = mod_obj.get_object_reference('car_repair_industry', 'action_sale_order_tree_filtered')
            id = result and result[1] or False
            result = act_obj.browse(id).read()[0]
            res = mod_obj.get_object_reference('car_repair_industry', 'repair_view_order_form')
            result['views'] = [(res and res[1] or False, 'form')]
            result['res_id'] = order_id.id or False
            self.write({'sale_order_id': order_id.id, 'state': 'quote'})
            return result

    @api.multi
    def action_create_view_diagnose(self):
        if self.dig_count >= 1:
            list = []
            context = dict(self._context or {})
            quo_order_ids = self.env['fleet.diagnose'].search([('fleet_repair_id', '=', self.id)])
            for order in quo_order_ids:
                list.append(order.id)
            return {
                'name': _('Phiếu khám'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'res_model': 'fleet.diagnose',
                'view_id': False,
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', list)],
                'context': context,
            }
        else:
            Diagnosis_obj = self.env['fleet.diagnose']
            repair_obj = self.env['fleet.repair'].browse(self._ids[0])
            mod_obj = self.env['ir.model.data']
            act_obj = self.env['ir.actions.act_window']
            if not repair_obj.fleet_repair_line:
                raise Warning('You cannot create Car Diagnosis without Cars.')

            diagnose_vals = {
                'service_rec_no': repair_obj.sequence,
                'name': repair_obj.name,
                'priority': repair_obj.priority,
                'receipt_date': repair_obj.receipt_date,
                'client_id': repair_obj.client_id.id,
                'contact_name': repair_obj.contact_name,
                'client_phone': repair_obj.client_phone,
                'client_mobile': repair_obj.client_mobile,
                'client_email': repair_obj.client_email,
                'fleet_repair_id': repair_obj.id,
                'state': 'draft',
                'fleet_repair_line': [(6, 0, repair_obj.fleet_repair_line.ids)],
                'service_type_ids': [(6, 0, repair_obj.service_type_ids.ids)],
                'user_id': repair_obj.user_id.id,
                'description': repair_obj.description,
                'car_name': repair_obj.car_name,
                'license_plate': repair_obj.license_plate,
                'vin_sn': repair_obj.vin_sn,
            }
            diagnose_id = Diagnosis_obj.create(diagnose_vals)

            self.write({'state': 'diagnosis', 'diagnose_id': diagnose_id.id})
            result = mod_obj.get_object_reference('car_repair_industry', 'action_fleet_diagnose_tree_filtered')
            id = result and result[1] or False
            result = act_obj.browse(id).read()[0]
            res = mod_obj.get_object_reference('car_repair_industry', 'view_fleet_diagnose_form')
            result['views'] = [(res and res[1] or False, 'form')]
            result['res_id'] = diagnose_id.id or False
            return result

    @api.multi
    def action_view_quotation(self):
        mod_obj = self.env['ir.model.data']
        act_obj = self.env['ir.actions.act_window']
        order_id = self.sale_order_id.id
        result = mod_obj.get_object_reference('sale', 'action_orders')
        id = result and result[1] or False
        result = act_obj.browse(id).read()[0]
        res = mod_obj.get_object_reference('sale', 'view_order_form')
        result['views'] = [(res and res[1] or False, 'form')]
        result['res_id'] = order_id or False
        return result

    @api.multi
    def action_view_work_order(self):
        mod_obj = self.env['ir.model.data']
        act_obj = self.env['ir.actions.act_window']
        work_order_id = self.workorder_id.id
        result = mod_obj.get_object_reference('car_repair_industry', 'action_fleet_workorder_tree_view')
        id = result and result[1] or False
        result = act_obj.browse(id).read()[0]
        res = mod_obj.get_object_reference('car_repair_industry', 'view_fleet_workorder_form')
        result['views'] = [(res and res[1] or False, 'form')]
        result['res_id'] = work_order_id or False
        return result

    @api.multi
    def workorder_lines_layouted(self):
        """
        Returns this order lines classified by sale_layout_category and separated in
        pages according to the category pagebreaks. Used to render the report.
        """
        self.ensure_one()
        report_pages = [[]]
        sale_order = self.env['sale.order'].search([('fleet_repair_id', '=', self.id)])
        if sale_order:
            for sale_id in sale_order:
                so_line = self.env['sale.order.line'].search([('order_id', '=', sale_id.id)])
                repair_line = self.env['repair.order.line'].search([('order_id', '=', sale_id.id)])

                subtotal_service = 0
                subtotal_product = 0
                for sv in repair_line:
                    subtotal_service += sv.price_subtotal
                for prd in so_line:
                    subtotal_product += prd.price_subtotal

                report_pages[-1].append({
                    'so_lines': so_line,
                    'repair_line': repair_line,
                    'subtotal_product': int(subtotal_product),
                    'subtotal_service': int(subtotal_service)
                })
        return report_pages

    @api.multi
    def unlink(self):
        if self.state not in ('draft', 'diagnosis', 'diagnosis_complete', 'quote', 'saleorder', 'workorder'):
            raise UserError(_("You can not delete a car repair that is already in progress!"))
        else:
            diagnosis_id = self.env['fleet.diagnose'].search([('fleet_repair_id', '=', self.id)])
            wo_id = self.env['fleet.workorder'].search([('fleet_repair_id', '=', self.id)])
            so_id = self.env['sale.order'].search([('fleet_repair_id', '=', self.id)])
            if wo_id:
                for wo in wo_id:
                    if wo.state in 'done':
                        raise UserError(_("You can not delete a car repair that is already in progress!"))
            if so_id:
                for so in so_id:
                    so.write({'state': 'cancel'})
                    stock_id = self.env['stock.picking'].search([('origin', '=', so.name)])
                    stock_id.unlink() if stock_id else False
                    so.unlink()
            diagnosis_id.unlink() if diagnosis_id else False
            wo_id.unlink() if wo_id else False
        res = super(fleet_repair, self).unlink()
        self.clear_caches()
        return res


class ServiceType(models.Model):

    _name = 'service.type'

    name = fields.Char(string='Name')
    product_template_id = fields.Many2many("product.template", "service_type_id", string="Product")
    survey_ids = fields.Many2many('survey.survey', 'service_type_survey_rel', 'service_id',
                                  'survey_id', 'Surveys')

    @api.multi
    def write(self, value):
        old_product_ids = self.product_template_id
        res = super(ServiceType, self).write(value)
        if res and "product_template_id" in value and self.env.context.get('FROM_FLEET', True):
            for product in self.product_template_id:
                if product not in old_product_ids:
                    service_type_id = product.service_type_id.ids
                    service_type_id.extend(self.ids)
                    value_write = {'service_type_id': [[6, False, service_type_id]]}
                    product.with_context(FROM_FLEET=False).write(value_write)
            product_destroy = [x for x in old_product_ids if x not in self.product_template_id]
            for pro_des in product_destroy:
                service_type_id = pro_des.service_type_id.ids
                for _id in self.ids:
                    if _id in service_type_id:
                        service_type_id.remove(_id)
                value_write = {'service_type_id': [[6, False, service_type_id]]}
                pro_des.with_context(FROM_FLEET=False).write(value_write)
        return res

    @api.model
    def create(self, value):
        res = super(ServiceType, self).create(value)
        if res:
            for product in res.product_template_id:
                service_type_id = product.service_type_id.ids
                service_type_id.extend(res.ids)
                value_write = {'service_type_id': [[6, False, service_type_id]]}
                product.with_context(FROM_FLEET=False).write(value_write)
        return res

ServiceType()


