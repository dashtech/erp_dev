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
from datetime import date, time, datetime
from odoo.exceptions import UserError, ValidationError


class A(models.Model):
    _inherit = "survey.survey"

    # service_ids = fields.Many2many('survey.survey', 'service_type_survey_rel', 'survey_id',
    #                                'service_id',)

    @api.model
    def search_ok(self, data_id=0):
        data_ok = self.env['fleet.diagnose'].browse(data_id).survey_ids
        if not data_ok:
            group = 2
            res = self.search([])
            data = []
            for x in res:
                _d = {'id': 'survey_%s' % x.id, 'string': x.display_name, 'page': [], 'group': []}
                pages = []
                for a in x.page_ids:
                    _a = {'id': 'page_id_%s' % a.id, 'string': a.display_name, 'question': []}
                    for i in a.question_ids:
                        labels = []
                        for l in i.labels_ids:
                            labels.append({'id': 'label_id_%s' % l.id, 'string': l.value, 'color': l.color})
                        labels_2 = []
                        for k in i.labels_ids_2:
                            labels_2.append({'id': 'label2_id_%s' % k.id, 'string': k.value,
                                             'name': 'question_id_%s' % i.id, 'value_input': "", 'value_radio': ""})
                        _a['question'].append({'id': 'question_id_%s' % i.id, 'string': i.question,
                                               'type': i.type, 'labels_ids': labels, 'labels_2': labels_2})
                    pages.append(_a)
                if group:
                    len_pages = len(pages) / group
                    if len_pages >= 1:
                        start = 0
                        stop = 0
                        for i in range(group):
                            start = stop
                            stop += len_pages
                            _d['group'].append(pages[start:stop])
                        if stop < len(pages):
                            _d['group'][0].extend(pages[stop:len(pages)])
                    else:
                        _d['group'].append(pages)
                _d['page'] = pages
                data.append(_d)
            return data
        else:
            return data_ok


class fleet_diagnose(models.Model):
    _name = 'fleet.diagnose'
    _inherit = ['mail.thread']
    
    name = fields.Char(string='Name')
    service_rec_no = fields.Char(string='Receipt No', readonly=True, copy=False)
    client_id = fields.Many2one('res.partner', string='Client', required=True)
    client_phone = fields.Char(string='Phone')
    client_mobile = fields.Char(string='Mobile')
    client_email = fields.Char(string='Email')
    receipt_date = fields.Datetime(string='Date of Receipt')
    contact_name = fields.Char(string='Contact Name')
    license_plate = fields.Char('License Plate', help='License plate number of the vehicle (ie: plate number for a car)')
    vin_sn = fields.Char('Chassis Number', help='Unique number written on the vehicle motor (VIN/SN number)')
    model_id = fields.Many2one('fleet.vehicle.model', 'Model', help='Model of the vehicle')
    fuel_type = fields.Selection([('gasoline', 'Gasoline'), ('diesel', 'Diesel'), ('electric', 'Electric'), ('hybrid', 'Hybrid')], 'Fuel Type', help='Fuel Used by the vehicle')
    service_type_ids = fields.Many2many('service.type', string='Nature of Service')
    user_id = fields.Many2one('res.users', string='Technician')
    priority = fields.Selection([('0','Low'), ('1','Normal'), ('2','High')], 'Priority')
    description = fields.Text(string='Customer Requests')
    est_ser_hour = fields.Float(string='Estimated Sevice Hours')
    service_product_id = fields.Many2one('product.product', string='Service Product')
    service_product_price = fields.Integer('Service Product Price')
    fleet_repair_id = fields.Many2one('fleet.repair', string='Source', copy=False)
    sale_order_id = fields.Many2one('sale.order', string='Sales Order', copy=False)
    state = fields.Selection([
            ('draft', 'Draft'),
            ('in_progress', 'In Progress'),
            ('done', 'Complete'),
            ], 'Status', default="draft", readonly=True, copy=False, help="Gives the status of the fleet Diagnosis.", select=True)
    fleet_repair_count = fields.Integer(string='Repair Orders', compute='_compute_repair_id')
    workorder_count = fields.Integer(string='Work Orders', compute='_compute_workorder_id')
    is_workorder_created = fields.Boolean(string="Workorder Created")
    confirm_sale_order = fields.Boolean(string="confirm sale order")
    is_invoiced = fields.Boolean(string="invoice Created", default=False)
    quotation_count = fields.Integer(string="Quotations", compute='_compute_quotation_id')
    saleorder_count = fields.Integer(string="Sale Order", compute='_compute_saleorder_id')
    inv_count = fields.Integer(string="Invoice", compute='_compute_invoice_id')
    fleet_repair_line = fields.Many2many('fleet.vehicle', string='Car Information')
    survey_ids = fields.Char(string="Survey")
    car_name = fields.Char(string="Car Name")

    _order = 'id desc'

    # @api.multi
    # def write(self, values):
        # from ast import literal_eval
        # if values.get('survey_ids'):
        #     user_input_obj = self.env['diagnose.user.input']
        #     parse_data = literal_eval(values.get('survey_ids'))
        #     for x in range(len(parse_data)):
        #         parse_data_group = literal_eval(values.get('survey_ids'))[x]['group']
        #         for i in range(len(parse_data_group)):
        #             if parse_data_group[i]:
        #                 for j in range(len(parse_data_group[i][0]['question'])):
        #                     label_obj = False
        #                     question_id = self.env['survey.question'].search([('id', '=', int(parse_data_group[i][0]['question'][j]['id'].replace('question_id_', '')))])
        #                     if not parse_data_group[i][0]['question'][j]['labels_2']:
        #                         answer = parse_data_group[i][0]['question'][j]['value'].decode('utf-8')
        #                     elif parse_data_group[i][0]['question'][j]['labels_2'] and len(parse_data_group[i][0]['question'][j]['labels_2'][0]) == 5:
        #                         answer = parse_data_group[i][0]['question'][j]['labels_2'][0]['value_input'].decode('utf-8')
        #                         if parse_data_group[i][0]['question'][j]['labels_2'][0]['value_radio']:
        #                             label_obj = self.env['survey.label'].search([('id', '=', int(parse_data_group[i][0]['question'][j]['labels_2'][0]['value_radio'].replace('label_id_', '')))])
        #                         else:
        #                             label_obj = False
        #                     elif parse_data_group[i][0]['question'][j]['labels_2'] and len(parse_data_group[i][0]['question'][j]['labels_2'][0]) == 4:
        #                         answer = parse_data_group[i][0]['question'][j]['labels_2'][0]['value_input'].decode('utf-8')
        #                         label_obj = False
        #                     user_input_obj.search([('diagnose_id', '=', self.id), ('question_id', '=', question_id.id)])
        #                     anser_exit = user_input_obj.search([('diagnose_id', '=', self.id), ('question_id', '=', question_id.id)])
        #                     if anser_exit:
        #                         anser_exit.write({'value_aws': answer, 'label_id': label_obj.id if label_obj else False})
        #                     else:
        #                         vals = {
        #                             'diagnose_id': self.id,
        #                             'question_id': question_id.id,
        #                             'value_aws': answer,
        #                             'label_id': label_obj.id if label_obj else False,
        #                         }
        #                         user_input_obj.create(vals)
        #
        # res = super(fleet_diagnose, self).write(values)
        # return res

    # @api.model
    # def default_get(self, fields):
    #     settings = super(fleet_diagnose, self).default_get(fields)
    #     data = self.env['survey.survey'].search([])
    #     settings['survey_ids'] = str(data.ids)
    #     return settings

    @api.depends('fleet_repair_id')
    def _compute_repair_id(self):
        for diagnose in self:
            repair_order_ids = self.env['fleet.repair'].search([('diagnose_id', '=', diagnose.id)])
            diagnose.fleet_repair_count = len(repair_order_ids)

    @api.multi
    @api.depends('is_workorder_created')
    def _compute_workorder_id(self):
        for diagnose in self:
            work_order_ids = self.env['fleet.workorder'].search([('diagnose_id', '=', diagnose.id)])            
            diagnose.workorder_count = len(work_order_ids)

    @api.multi
    @api.depends('sale_order_id')
    def _compute_quotation_id(self):
        for diagnose in self:
                quo_order_ids = self.env['sale.order'].search([('state', '=', 'draft'), ('diagnose_id.id', '=', diagnose.id)])
                diagnose.quotation_count = len(quo_order_ids)
    
    @api.multi
    @api.depends('confirm_sale_order')
    def _compute_saleorder_id(self):
        for diagnose in self:
            diagnose.quotation_count = 0
            so_order_ids = self.env['sale.order'].search([('state', '=', 'sale'), ('diagnose_id.id', '=', diagnose.id)])            
            diagnose.saleorder_count = len(so_order_ids)

    @api.multi
    @api.depends('is_invoiced')
    def _compute_invoice_id(self):
        count = 0 
        for diagnose in self:
            so_order_ids = self.env['sale.order'].search([('state', '=', 'sale'), ('diagnose_id.id', '=', diagnose.id)])
            for order in so_order_ids:
                inv_order_ids = self.env['account.invoice'].search([('origin', '=', diagnose.name)])            
                if inv_order_ids:
                    self.inv_count = len(inv_order_ids)         
 
 
    @api.multi
    def button_view_repair(self):
        list = []
        context = dict(self._context or {})
        repair_order_ids = self.env['fleet.repair'].search([('diagnose_id', '=', self.id)])         
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
    def button_view_workorder(self):
        list = []
        context = dict(self._context or {})
        work_order_ids = self.env['fleet.workorder'].search([('diagnose_id', '=', self.id)])           
        for order in work_order_ids:
            list.append(order.id)
        return {
            'name': _('Lệnh khám xe'),
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
        quo_order_ids = self.env['sale.order'].search([('state', '=', 'draft'),('diagnose_id', '=', self.id)])           
        for order in quo_order_ids:
            list.append(order.id)
        return {
            'name': _('Báo giá'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in',list )],
            'context': context,
        }
  
    @api.multi
    def button_view_saleorder(self):
        list = []
        context = dict(self._context or {})
        quo_order_ids = self.env['sale.order'].search([('state', '=', 'sale'), ('diagnose_id', '=', self.id)])
        for order in quo_order_ids:
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
    def button_view_invoice(self):
        list = []
        inv_list  = []
        so_order_ids = self.env['sale.order'].search([('state', '=', 'sale'),('diagnose_id', '=', self.id)])
        for order in so_order_ids:
            inv_order_ids = self.env['account.invoice'].search([('origin', '=',order.name )])            
            if inv_order_ids:
                for order_id in inv_order_ids:
                    if order_id.id not in list:
                        list.append(order_id.id)
                            

        context = dict(self._context or {})
        return {
            'name': _('Hóa đơn'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'account.invoice',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in',list )],
            'context': context,
        }


    
    @api.multi
    def button_in_progress(self):
        self.write({'state': 'in_progress'})


    @api.multi
    def button_done(self):
        self.write({'state':'done'})

    @api.multi
    def button_cancel(self):
        self.write({'state':'cancel'})

    @api.multi
    def button_draft(self):
        self.write({'state':'draft'})

    @api.onchange('client_id')
    def onchange_partner_id(self):
        addr = {}
        if self.client_id:
            addr = self.pool.get('res.partner').address_get([self.client_id.id], ['contact'])
        return {'value': addr}

    @api.multi
    def action_create_quotation(self):
        mod_obj = self.env['ir.model.data']
        act_obj = self.env['ir.actions.act_window']
        quote_vals = {
            'diagnose_id': self.id,
            'fleet_ids': [(6, 0, self.fleet_repair_line.ids)],
            'partner_id': self.client_id.id or False,
            'state': 'draft',
            'client_order_ref': self.name,
            'fleet_repair_id': self.fleet_repair_id.id,
            'create_form_fleet': True,
            'license_plate': self.fleet_repair_id.license_plate,
            'car_name': self.fleet_repair_id.car_name,
            'vin_sn': self.fleet_repair_id.vin_sn,
            'order_line_service': self.fleet_repair_id.prepare_line_order()
        }

        order_id = self.env['sale.order'].create(quote_vals)

        result = mod_obj.get_object_reference('car_repair_industry', 'action_saleorder1')
        id = result and result[1] or False
        result = act_obj.browse(id).read()[0]
        res = mod_obj.get_object_reference('car_repair_industry', 'repair_view_order_form')
        result['views'] = [(res and res[1] or False, 'form')]
        result['res_id'] = order_id.id or False
        self.write({'sale_order_id': order_id.id, 'state': 'done'})
        self.fleet_repair_id.write({'sale_order_id': order_id.id, 'state': 'quote'})
        return result
        

    @api.multi
    def action_view_sale_order(self):
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
    def action_view_fleet_repair(self):
        mod_obj = self.env['ir.model.data']
        act_obj = self.env['ir.actions.act_window']
        repair_id = self.fleet_repair_id.id
        result = mod_obj.get_object_reference('car_repair_industry', 'action_fleet_repair_tree_view')
        id = result and result[1] or False
        result = act_obj.browse(id).read()[0]
        res = mod_obj.get_object_reference('car_repair_industry', 'view_fleet_repair_form')
        result['views'] = [(res and res[1] or False, 'form')]
        result['res_id'] = repair_id or False
        return result

    @api.multi
    def result_diagnosis_layouted(self):
        from ast import literal_eval
        self.ensure_one()
        report_pages = [[]]
        survey_data = self.env['diagnose.user.input'].search([('diagnose_id', '=', self.id)])
        report_pages[-1].append({
            'survey_data': survey_data
        })
        return report_pages


class SurveyAnswer(models.Model):
    _name = 'diagnose.user.input'

    diagnose_id = fields.Many2one('fleet.diagnose', 'Diagnosis ID')
    question_id = fields.Many2one('survey.question', 'Question ID')
    value_aws = fields.Text('Answer Input')
    label_id = fields.Many2one('survey.label', 'Label')
    page_id = fields.Many2one('survey.page', 'Page', compute='compute_survey')
    survey_id = fields.Many2one('survey.survey', 'Survey', compute='compute_survey')

    @api.one
    @api.depends('question_id')
    def compute_survey(self):
        if self.question_id:
            self.survey_id = self.question_id.survey_id
            self.page_id = self.question_id.page_id

