# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo import http
import json
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    pre_order_html = fields.Html(readonly=True, compute='pre_order')

    @api.onchange('partner_id')
    def partner_change(self):
        if self.fleet_ids:
            return

        if not self.partner_id.fleet_vehicles:
            self.fleet_ids = [(6, False, [])]
            return

        self.fleet_ids = \
            [(6, False, [self.partner_id.fleet_vehicles[0].id])]

    def print_work_order(self):
        return self.env['report'].get_action(
            self.workorder_id,
            'car_repair_industry.fleet_workorder_template')

    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        self.action_create_work_order()
        return res

    @api.one
    def action_create_work_order(self):
        # if not self.order_line_service or self.workorder_id:
        if self.workorder_id:
            return False

        name = self.name
        priority = False
        client_phone = self.partner_id.phone
        client_mobile = self.partner_id.mobile
        service_type_ids = self.service_type_ids._ids
        license_plate = self.fleet_ids and self.fleet_ids[
            0].license_plate or '/'
        car_name = False
        vin_sn = False

        wo_vals = {
            'name': name,
            'client_id': self.partner_id.id,
            'sale_order_id': self.id,
            'fleet_repair_id': self.diagnose_id and self.diagnose_id.fleet_repair_id.id or False,
            'diagnose_id': self.diagnose_id and self.diagnose_id.id or False,
            'hour': 0.0,
            'priority': priority,
            'state': 'draft',
            'user_id': self.user_id.id,
            'confirm_sale_order': True,
            'client_phone': client_phone,
            'client_mobile': client_mobile,
            'fleet_repair_line': [
                (6, 0, self.fleet_ids.ids)],
            'service_type_ids': [
                (6, 0, service_type_ids)],
            'license_plate': license_plate,
            'car_name': car_name,
            'vin_sn': vin_sn,
            'date_finished': self.fleet_repair_id and self.fleet_repair_id.receipt_date or False,
            'company_id': self.company_id.id,
        }
        wo_id = self.env['fleet.workorder'].create(wo_vals)
        for line in self.order_line:
            line.write({'workorder_id': wo_id.id,
                        'user_id': wo_id.user_id.id})
        for line_service in self.order_line_service:
            line_service.write({'workorder_id': wo_id.id,
                                'user_id': wo_id.user_id.id})
        self.write({'workorder_id': wo_id.id,
                    'is_workorder_created': True})

        return True

    @api.multi
    def auto_confirm_invoice(self):
        for invoice in self.invoice_ids:
            if invoice.state != 'draft':
                continue
            invoice.action_invoice_open()
        return True

    @api.multi
    def auto_done_picking(self):
        def next_state(picking):
            if picking.state == 'done':
                return True
            if picking.state == 'confirmed':
                # picking.action_assign()
                picking.force_assign()
            if picking.state == 'assigned':
                act = picking.do_new_transfer()

                if not act:
                    return
                res_id = act['res_id']
                res_model = act['res_model']
                wizard = \
                    self.env[res_model].browse(res_id)
                wizard.process()

        for picking in self.picking_ids:
            next_state(picking)
        return True

    def ordered(self):
        self.make_invoice_automatic()
        self.auto_confirm_invoice()
        # self.auto_done_picking()

        return self.action_view_invoice()

    def basic_ordered(self):
        self.action_confirm()
        self.make_invoice_automatic()
        self.auto_confirm_invoice()
        self.env.cr.execute('select auto_picking_sale from sale_config_settings order by id DESC limit 1')
        result = self.env.cr.fetchone()
        if not result or 'auto' in result:
            self.auto_done_picking()
        return self.action_view_invoice()

    @api.depends('amount_total')
    def pre_order(self):
        for s in self:
            amount_total = s.format_money(s.amount_total, s.currency_id.name or '')
            if s.currency_id.currency_text:
                text = u' ' + unicode(s.currency_id.currency_text)
            else:
                text = u' đồng'
            amount_int = int(s.amount_total)
            amount_fl = int(str(s.amount_total - amount_int)[:1])
            amount_txt = s.env['read.number'].docso(amount_int) + text
            # s.env['read.number'].docso(amount_fl) + text
            s.pre_order_html = _(u'''
                        <span style="text-align: center; color: blue;">
                            <h1>Are you sure ordering this?</h1>
                        </span></br>
                        <span style="font-size: 13; text-align: center">
                            <h3> Amount total payment : {}</h3>
                        </span></br>
                        <span style="text-align: center"><h3>Equal text : <i>{}</i></h3></span>
                        ''').format(amount_total, amount_txt)

    def format_money(self, num, unit=''):
        num = round(num / 1, 2)
        num_text = '{:,}'.format(num).replace(
            '.', '/').replace(',', '.').replace('/', ',') + ' ' + unit
        return num_text

    def pre_confirm_sale(self):
        action = self.env.ref('bave_basic.action_pre_confirm_so').read()[0]
        action['res_id'] = self.id
        return action

    def pre_ordered(self):
        self.auto_done_picking_workorder_by_config()

        if self.workorder_id and self.workorder_id.state != 'done':
            return self.open_wizard_auto_done_confirm()
        if self.picking_ids:
            for picking in self.picking_ids:
                if picking.state != 'done':
                    return self.open_wizard_auto_done_confirm()
        action = self.env.ref('bave_basic.action_pre_confirm_cso').read()[0]
        action['res_id'] = self.id
        return action

    @api.model
    def create(self, vals):
        res = super(SaleOrder, self).create(vals)
        if res.create_form_fleet:
            res.action_confirm()
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        if not self.product_id:
            return res
        self.name = self.product_id.default_code or self.product_id.name
