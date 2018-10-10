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

from odoo import fields, models, api, _
from datetime import date, time, datetime
import xmlrpclib
from datetime import timedelta
import re
from odoo.exceptions import UserError, ValidationError
from itertools import groupby
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
import pytz
from odoo.addons import decimal_precision as dp

class btek_partner_group(models.Model):
    _name = 'btek.partner.group'

    name = fields.Char(string="Name", required=True, copy=False, default=lambda self: _('New'))
    description = fields.Text(string='Description')
    code = fields.Char(string="Code")


class ResPartner(models.Model):
    _inherit = 'res.partner'

    copy_id = fields.Many2one(string="Copy", comodel_name="res.partner")
    is_copy = fields.Boolean(string="Copy", default=False)
    upsell_count = fields.Integer(compute='_compute_upsell_count')

    code = fields.Char()
    fleet_vehicles = fields.One2many('fleet.vehicle', 'driver_id')
    plates = fields.Char(compute='_compute_plate', store=True, string='License plate')
    group_user = fields.Many2one(
        'btek.partner.group', string='Partner group')

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'The code must be unique !'),
        ('mobile_uniq', 'unique(mobile)', 'The mobile must be unique !'),
    ]

    def check_vat(self):
        res = super(ResPartner, self).check_vat()
        return True

    @api.multi
    def _compute_upsell_count(self):
        querry = """
                    select o.partner_id, count(o.id)
                    from sale_order as o
                    where o.partner_id in ({})
                      and o.state = 'draft'
                      and o.upsell = true
                    group by o.partner_id
                """.format(','.join([str(id) for id in self._ids]))
        self.env.cr.execute(querry)
        result_dict = \
            dict((row[0], row[1] or 0) for row in self.env.cr.fetchall())

        for p in self:
            p.upsell_count = result_dict.get(p.id, 0)

    @api.multi
    def button_view_upsell(self):
        context = dict(self._context or {})
        domain = [('state', '=', 'draft'),
                  ('partner_id', '=', self[0].id),
                  ('upsell', '=', True)]

        action_obj = self.env.ref('car_repair_industry.action_upsell')
        action = action_obj.read([])[0]
        action['domain'] = domain

        return action

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        domain = domain or []
        domain.append(['is_copy', '!=', True])
        res = super(ResPartner, self).search_read(domain=domain, fields=fields, offset=offset,
                                                  limit=limit, order=order)
        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        args.append(['is_copy', '!=', True])
        res = super(ResPartner, self).name_search(
            name=name, args=args, operator=operator, limit=limit)
        limit = limit or 8
        addition = limit - len(res)
        if addition <= 0:
            return res

        exist_ids = [r[0] for r in res]
        args.append(['code', 'ilike', name])
        args.append(['id', 'not in', exist_ids])
        partner_s = self.search(args, limit=addition)
        partner_name_get = partner_s.name_get()
        res.extend(partner_name_get)

        return res

    @api.model
    def create(self, vals):
        if vals.get('email'):
            if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", vals['email']) != None:
                pass
            else:
                raise ValidationError(_('Email format invalid. Please enter again!'))
        res = super(ResPartner, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        if vals.get('email'):
            if re.match("^.+\\@(\\[?)[a-zA-Z0-9\\-\\.]+\\.([a-zA-Z]{2,3}|[0-9]{1,3})(\\]?)$", vals['email']) != None:
                pass
            else:
                raise ValidationError(_('Email format invalid. Please enter again!'))
        res = super(ResPartner, self).write(vals)
        return res

    @api.depends('fleet_vehicles.license_plate','fleet_vehicles.driver_id')
    def _compute_plate(self):
        for s in self:
            if not s.fleet_vehicles:
                s.plates = ''
            else:
                plates = [v.license_plate for v in s.fleet_vehicles]
                s.plates = ' / '.join(plates)


ResPartner()


class OrderBave(models.Model):
    _name = 'bave.order'

    @api.model
    def default_partner_id(self):
        partner_id = self.env.user.company_id.partner_id
        if not partner_id.copy_id:
            partner_id.write({'copy_id': partner_id.copy({'name': partner_id.name, 'is_copy': True}).id})
            partner_id.copy_id.write({'name': partner_id.name})
        partner_id.copy_id.write({'is_copy': True})
        return partner_id.copy_id

    quantity = fields.Integer(string="Quantity")
    partner_id = fields.Many2one(comodel_name="res.partner", string="Partner", default=default_partner_id)

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        partner_id = self.partner_id
        if not partner_id.copy_id:
            partner_id.write({'copy_id': partner_id.copy({'name': partner_id.name, 'is_copy': True}).id})
            partner_id.copy_id.write({'name': partner_id.name})
        partner_id.copy_id.write({'is_copy': True})
        self.partner_id = partner_id.copy_id

    @api.model
    def order_product(self, values):
        return self.env['sale.order'].order_product(values)


OrderBave()


class BaseConfigSettings(models.TransientModel):
    _inherit = 'base.config.settings'

    bave_ip = fields.Char(string="IP", default="localhost")
    bave_port = fields.Char(string="Port", default="8069")
    bave_db = fields.Char(string="Database Name", default="btek")
    bave_user = fields.Char(string="Username", default="admin")
    bave_password = fields.Char(string="Password")

    @api.multi
    def set_bave_ip(self):
        for record in self:
            self.env['ir.config_parameter'].set_param("bave_ip", record.bave_ip or '')

    @api.multi
    def set_bave_port(self):
        for record in self:
            self.env['ir.config_parameter'].set_param("bave_port", record.bave_port or '')

    @api.multi
    def set_bave_db(self):
        for record in self:
            self.env['ir.config_parameter'].set_param("bave_db", record.bave_db or '')

    @api.multi
    def set_bave_user(self):
        for record in self:
            self.env['ir.config_parameter'].set_param("bave_user", record.bave_user or '')

    @api.multi
    def set_bave_password(self):
        for record in self:
            self.env['ir.config_parameter'].set_param("bave_password", record.bave_password or '')

    @api.multi
    def get_default_bave_ip(self, fields):
        ICP = self.env['ir.config_parameter']
        # authorization_code = self.google_drive_authorization_code
        return {
            'bave_ip': ICP.get_param("bave_ip", ""),
            'bave_port': ICP.get_param("bave_port", ""),
            'bave_db': ICP.get_param("bave_db", ""),
            'bave_user': ICP.get_param("bave_user", ""),
            'bave_password': ICP.get_param("bave_password", "")
        }


class RepairSaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    workorder_id = fields.Many2one('fleet.workorder', 'Fleet WorkOrder')
    user_id = fields.Many2one('res.users', 'Assign To')
    product_id = fields.Many2one('product.product', string='Product',
                                 domain=[('sale_ok', '=', True), ('type', 'in', ('product', 'consu'))],
                                 change_default=True, ondelete='restrict',
                                 required=True)
    order_id = fields.Many2one('sale.order', string='Order Reference', required=False, ondelete='cascade', index=True, copy=False)
    suggest_id = fields.Many2one('product.template', string='Suggest Product',
                                 required=False, ondelete='cascade',
                                 index=True, copy=True)
    parent_state = fields.Selection(
        selection=lambda s:s.env['sale.order']._fields[
            'state'].selection, related='order_id.state',
        store=False)

    sub_price_after_tax_discount = fields.Monetary('Subtotal after tax and discount',
                                                   compute='_compute_sub_price_after_tax_discount',
                                                   readonly=True, store=True)
    discount_value = fields.Float(compute='_compute_amount', digits=dp.get_precision('Discount Value'))
    promotion_id = fields.Char('Promotion')

    @api.multi
    def unlink(self):
        for order in self:
            if order.state == 'sale' and order._name == 'sale.order.line':
                picking_id = self.env['stock.picking'].search([('order_id', '=', order.order_id.id)])
                if picking_id and len(picking_id) == 1:
                    for move in picking_id.move_lines:
                        if move.product_id.id == order.product_id.id:
                            move.write({'state': 'draft'})
                            move.unlink()
                    if picking_id.pack_operation_product_ids:
                        for pack in picking_id.pack_operation_product_ids:
                            if pack.product_id.id == order.product_id.id:
                                # pack.write({'state': 'draft'})
                                pack.unlink()
        res = models.Model.unlink(self)
        return res

    @api.model
    def create(self, vals):
        # vals['editable'] = False
        if vals.get('order_id'):
            so_id = self.env['sale.order'].search([('id', '=', vals['order_id'])])
            if so_id.workorder_id:
                vals['workorder_id'] = so_id.workorder_id.id
                vals['user_id'] = so_id.fleet_repair_id.user_id.id
            # for line in so_id.order_line:
            #     if line.product_id.id == vals['product_id']:
            #         return False
            # for sv_line in so_id.order_line_service:
            #     if sv_line.product_id.id == vals['product_id']:
            #         return False
            result = super(RepairSaleOrderLine, self).create(vals)
        return result

    # @api.multi
    # def write(self, vals):
    #     res = super(RepairSaleOrderLine, self).write(vals)
    #     for order_line in self:
    #         if order_line.state == 'sale' and order_line._name == 'sale.order.line':
    #             picking_id = self.env['stock.picking'].search([('order_id', '=', order_line.order_id.id)])
    #             for move in picking_id.move_lines:
    #                 if move.product_id.id == order_line.product_id.id:
    #                     move.sudo().write({'produt_uom_qty': order_line.product_uom_qty})
    #             if picking_id.pack_operation_product_ids:
    #                 for pack in picking_id.pack_operation_product_ids:
    #                     if pack.product_id.id == order_line.product_id.id:
    #                         pack.sudo().write({'product_qty': order_line.product_uom_qty})
    #     return res

    @api.multi
    def action_upsell(self):
        line_vals = self.copy_data()[0]

        if 'state' in line_vals:
            del line_vals['state']

        if 'order_id' in line_vals:
            del line_vals['order_id']

        upsell_id = self[0].order_id.upsell_id
        if upsell_id:
            upsell_id.write({
                'order_line': [(0, 0, line_vals)]
            })
            self[0].unlink()
            # return {'type': 'ir.actions.client', 'tag': 'reload'}
            return True

        vals = self[0].order_id.prepare_upsell_value()
        if isinstance(vals, list):
            vals = vals[0]

        vals['order_line'] = [(0, 0, line_vals)]
        self.env['sale.order'].create(vals)
        self[0].unlink()

        # return {'type': 'ir.actions.client', 'tag': 'reload'}
        return True

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        res = super(RepairSaleOrderLine, self)._compute_amount()
        for line in self:
            # price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            price = line.price_unit
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                            product=line.product_id, partner=line.order_id.partner_shipping_id)
            price_tax = 0
            dis_value = line.product_uom_qty * line.price_unit * (line.discount / 100)
            for tax_id in line.tax_id:
                price_tax += (line.product_uom_qty * line.price_unit - dis_value) * ((tax_id.amount or 0) / 100)
            line.update({
                'discount_value': dis_value,
                'price_tax': price_tax,
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    @api.depends('price_subtotal', 'tax_id', 'discount')
    def _compute_sub_price_after_tax_discount(self):
        for line in self:
            sub_price_after_tax_discount = line.price_subtotal * (
            1 - (line.discount or 0.0) / 100.0)
            for tax_id in line.tax_id:
                sub_price_after_tax_discount = sub_price_after_tax_discount * (1 + (tax_id.amount or 0.0) * 0.01)
            line.sub_price_after_tax_discount = sub_price_after_tax_discount

    @api.onchange('product_uom')
    def product_uom_change(self):
        if not self.product_uom or not self.product_id:
            self.price_unit = 0.0
            return
        if self.order_id.pricelist_id and self.order_id.partner_id:
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id.id,
                quantity=self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            self.price_unit = self.env['account.tax']._fix_tax_included_price_company(self._get_display_price(product),
                                                                                      product.taxes_id, self.tax_id,
                                                                                      self.company_id)

    @api.onchange('product_id')
    def _bave_onchange_discount(self):
        self.discount = 0.0
        if not (self.product_id and self.product_uom and
                    self.order_id.partner_id and self.order_id.pricelist_id and
                        self.order_id.pricelist_id.discount_policy == 'without_discount' and
                    self.env.user.has_group('sale.group_discount_per_so_line')):
            return
        if self.product_id:
            context_partner = dict(self.env.context, partner_id=self.order_id.partner_id.id, date=self.order_id.date_order)
            pricelist_context = dict(context_partner, uom=self.product_uom.id)

            price, rule_id = self.order_id.pricelist_id.with_context(pricelist_context).get_product_price_rule(
                self.product_id, self.product_uom_qty or 1.0, self.order_id.partner_id)
            new_list_price, currency_id = self.with_context(context_partner)._get_real_price_currency(self.product_id,
                                                                                                      rule_id,
                                                                                                      self.product_uom_qty,
                                                                                                      self.product_uom,
                                                                                                      self.order_id.pricelist_id.id)

            if new_list_price != 0:
                if self.order_id.pricelist_id.currency_id.id != currency_id:
                    # we need new_list_price in the same currency as price, which is in the SO's pricelist's currency
                    new_list_price = self.env['res.currency'].browse(currency_id).with_context(context_partner).compute(
                        new_list_price, self.order_id.pricelist_id.currency_id)
                discount = (new_list_price - price) / new_list_price * 100
                if discount > 0:
                    self.discount = discount

    @api.onchange('product_id', 'price_unit', 'product_uom', 'product_uom_qty')
    def _onchange_discount(self):
        return


class SaleOrderLine(models.Model):
    _name = 'repair.order.line'
    _inherit = 'sale.order.line'

    product_id = fields.Many2one('product.product', string='Product',
                                 domain=[('sale_ok', '=', True), ('type', '=', 'service')],
                                 change_default=True, ondelete='restrict', required=True)

    invoice_lines = fields.Many2many('account.invoice.line', 'repair_order_line_invoice_rel', 'order_line_id',
                                     'invoice_line_id', string='Invoice Lines', copy=False)
    repair_state = fields.Selection(
        [('draft', 'Draft'), ('start', 'Working'), ('done', 'Done')],
        'Repair state',
        required=True, default='draft')
    current_user = fields.Boolean(compute='_compute_current_user')

    @api.multi
    def unlink(self):
        return super(SaleOrderLine, self).unlink()

    @api.multi
    def action_upsell(self):
        line_vals = self.copy_data()[0]

        if 'state' in line_vals:
            del line_vals['state']

        if 'order_id' in line_vals:
            del line_vals['order_id']

        upsell_id = self[0].order_id.upsell_id
        if upsell_id:
            upsell_id.write({
                'order_line_service': [(0, 0, line_vals)]
            })
            self[0].unlink()
            # return {'type': 'ir.actions.client', 'tag': 'reload'}
            return True

        vals = self[0].order_id.prepare_upsell_value()
        if isinstance(vals, list):
            vals = vals[0]

        vals['order_line_service'] = [(0, 0, line_vals)]
        self.env['sale.order'].create(vals)
        self[0].unlink()

        # return {'type': 'ir.actions.client', 'tag': 'reload'}
        return True

    @api.multi
    def action_done(self):
        for line in self:
            if line.repair_state != 'start':
                continue
            line.write({'repair_state': 'done'})
        return True

    @api.multi
    def invoice_line_create(self, invoice_id, qty):
        """
        Create an invoice line. The quantity to invoice can be positive (invoice) or negative
        (refund).

        :param invoice_id: integer
        :param qty: float quantity to invoice
        """
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for line in self:
            if not float_is_zero(qty, precision_digits=precision):
                vals = line._prepare_invoice_line(qty=qty)
                vals.update({'invoice_id': invoice_id, 'repair_line_ids': [(6, 0, [line.id])]})
                self.env['account.invoice.line'].create(vals)

    @api.multi
    def _compute_current_user(self):
        for s in self:
            if s.env.user.id == s.user_id.id:
                s.current_user = True
            else:
                s.current_user = False


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    diagnose_id = fields.Many2one('fleet.diagnose', string='Car Diagnosis', readonly=True)
    fleet_repair_id = fields.Many2one('fleet.repair', string='Car Repair')
    workorder_id = fields.Many2one('fleet.workorder', string='Repair Work Order', readonly=True)
    is_workorder_created = fields.Boolean(string="Workorder Created")
    count_fleet_repair = fields.Integer(string='Repair Orders', compute='_compute_repair_id')
    workorder_count = fields.Integer(string='Work Orders', compute='_compute_workorder_id')
    fleet_ids = fields.Many2many(
        'fleet.vehicle', string='Car Information')
    model_ids = fields.Many2many(
        'fleet.vehicle.model', string='Models',
        compute='compute_model_ids')
    brand_ids = fields.Many2many(
        'fleet.vehicle.model.brand', string='Brands',
        compute='compute_brand_ids')

    create_form_fleet = fields.Boolean(string='Fleet')
    product_outside = fields.Char(string="Product")
    license_plate = fields.Char('License Plate', compute='_compute_plate', store=True)
    car_name = fields.Char('Car Name')
    vin_sn = fields.Char('Chassis Number')
    product_ids = fields.Many2one('product.product', string="Product", context={'no': True})
    listen_search = fields.Char(string="Listen", default="{}")

    order_line_service = fields.One2many('repair.order.line', 'order_id', string='Order Lines Service', copy=True,
                                         states={'cancel': [('readonly', True)], 'done': [('readonly', True)]})
    product_id = fields.Many2one('product.product', string='Product',
                                 domain=[('sale_ok', '=', True), ('type', '=', 'product')],
                                 change_default=True, ondelete='restrict', required=True)

    amount_untaxed_repair = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all',
                                     track_visibility='always')
    amount_tax_repair = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all',
                                 track_visibility='always')
    amount_total_repair = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all',
                                   track_visibility='always')
    amount_total_discount = fields.Monetary(string='Total Discount', store=True, readonly=True, compute='_amount_all',
                                   track_visibility='always')
    amount_total_discount_repair = fields.Monetary(string='Total Discount', store=True, readonly=True, compute='_amount_all',
                                   track_visibility='always')
    code_used = fields.Char('Voucher Code',
        help=u'Mã giảm giá được sử dụng trong đơn bán hàng')

    description = fields.Text('Customer Request')

    reason_cancel = fields.Text('Reason')

    # To use on wizard add service line
    order_line_service_add = fields.One2many(
        'repair.order.line', 'order_id',
        string='Order Lines Service',
        domain=[('id', '<', 0)])
    # to use in wizard add order line
    order_line_add = fields.One2many(
        'sale.order.line', 'order_id',
        string='Order Lines',
        domain=[('id', '<', 0)])
    upsell = fields.Boolean(default=False,
                            string='Is upsell')

    # To reference origin order in upsell order
    origin_id = fields.Many2one(
        'sale.order', 'Origin order', readonly=True)
    # To reference upsell order in normal order
    upsell_ids = fields.One2many(
        'sale.order', 'origin_id', string='Upsell',
        readonly=True)
    upsell_id = fields.Many2one(
        'sale.order', string='Upsell',
        compute='_compute_upsell')
    mobile = fields.Char(related='partner_id.mobile',
                         store=False, readonly=False,
                         string='Mobile')

    total_price_before_tax_discount = fields.Monetary(
        'Total product before tax and discount',
        compute='_compute_total_price_before_tax_discount',
        readonly=True, store=True)

    total_product_discount = fields.Monetary(
        'Total product discount',
        compute='_compute_total_product_discount',
        readonly=True, store=True)

    total_product_tax = fields.Monetary(
        'Total product tax',
        compute='_compute_total_product_tax',
        readonly=True, store=True)

    total_price_after_tax_discount = fields.Monetary(
        'Total product after tax and discount',
        compute='_compute_total_price_after_tax_discount',
        readonly=True, store=True)
    done_date = fields.Datetime(readonly=True)
    cancel_date = fields.Datetime(readonly=True)
    service_type_ids = fields.Many2many(
        'service.type', 'sale_order_service_type_rel',
        'order_id', 'service_type_id',
        'Service Package')

    invoice_confirmed = fields.Boolean(
        compute='_compute_invoice_confirmed',
        store=True)
    invoice_state = fields.Selection(
        [('open', 'Confirmed'),
         ('paid', 'Paid')],
        compute='_compute_invoice_state',
        store=True
    )
    total_service = fields.Monetary(compute='_get_total_service')
    total_product = fields.Monetary(compute='_get_total_product')
    amount_total_repair_in_word = fields.Text(compute='_compute_amount_total_repair_in_word', readonly=True)
    day_order = fields.Char(compute='_compute_day_order', readonly=True)
    day_validity = fields.Char(compute='_compute_day_validity', readonly=True)
    property_quotes_note = fields.Text(company_dependent=True, string="Quotes note print")
    message_error_picking_workorder = fields.Html(
        compute='_compute_message_error_picking_workorder')

    @api.multi
    def _compute_message_error_picking_workorder(self):
        for order in self:
            picking_done = True
            workorder_done = True
            for picking in order.picking_ids:
                if picking.state != 'done':
                    picking_done = False
                    continue
            workorder_s = self.env['fleet.workorder'].search(
                [('sale_order_id', '=', order.id)])
            for workorder in workorder_s:
                if workorder.state != 'done':
                    workorder_done = False
                    continue
            message = _('delivery and workorder')
            if picking_done and not workorder_done:
                message = _('workorder')
            if not picking_done and workorder_done:
                message = _('delivery')

            message_error_picking_workorder = \
                '<p><b><font style="color: rgb(41, 82, 24);">' +\
            _('You need done {} before ordered.').format(message) + \
            '</font> </b></p><ul><li><p>' +\
            _('Please click "continue" to automatic process done {}').format(message) +\
            '</p></li><li><p>' +\
            _('Click exit to come back!') +\
            '</p></li></ul>'
        self.message_error_picking_workorder = \
            message_error_picking_workorder

    @api.multi
    @api.depends('order_line_service')
    def _get_total_service(self):
        for s in self:
            if s.order_line_service:
                s.total_service = sum(line.price_subtotal for line in s.order_line_service)

    @api.multi
    @api.depends('order_line')
    def _get_total_product(self):
        for s in self:
            if s.order_line:
                s.total_product = sum(line.price_subtotal for line in s.order_line)

    @api.depends('order_line.invoice_lines.invoice_id.state',
                 'order_line_service.invoice_lines.invoice_id.state')
    @api.multi
    def _compute_invoice_state(self):
        for o in self:
            o.invoice_state = 'paid'
            state_list = []
            for l in o.order_line:
                for il in l.invoice_lines:
                    if not il.invoice_id:
                        continue
                    state_list.append(il.invoice_id.state)
            for l in o.order_line_service:
                for il in l.invoice_lines:
                    if not il.invoice_id:
                        continue
                    state_list.append(il.invoice_id.state)

            if not state_list:
                o.invoice_state = 'open'
                continue

            if any(state != 'paid' for state in state_list):
                o.invoice_state = 'open'

    @api.depends('order_line.invoice_lines.invoice_id.state',
                 'order_line_service.invoice_lines.invoice_id.state')
    @api.multi
    def _compute_invoice_confirmed(self):
        for o in self:
            o.invoice_confirmed = True
            state_list = []
            for l in o.order_line:
                for il in l.invoice_lines:
                    if not il.invoice_id:
                        continue
                    state_list.append(il.invoice_id.state)
            for l in o.order_line_service:
                for il in l.invoice_lines:
                    if not il.invoice_id:
                        continue
                    state_list.append(il.invoice_id.state)

            if not state_list:
                o.invoice_confirmed = False
                continue

            for state in state_list:
                if state not in ('open', 'paid'):
                    o.invoice_confirmed = False
                    break

    @api.multi
    def _compute_upsell(self):
        for o in self:
            o.upsell_id = o.upsell_ids and o.upsell_ids[0].id or False

    @api.onchange('service_type_ids')
    def service_type_ids_change(self):
        if self.state not in ('draft', 'sale'):
            return
        order_line_service = [(4, line.id) for line in self.order_line_service]
        order_line = [(4, line.id) for line in self.order_line]

        for service in self.service_type_ids:
            for template_id in service.product_template_id:
                if not template_id.product_variant_ids:
                    continue
                if template_id.product_variant_ids[0].id in self.order_line_service.mapped('product_id.id'):
                    continue

                if template_id.product_variant_ids[0].id in self.order_line.mapped('product_id.id'):
                    continue

                if template_id.type != 'service':
                    order_line.append(
                        (0, 0, {
                            'product_id': template_id.product_variant_ids[0].id,
                        })
                    )
                    continue

                order_line_service.append(
                    (0, 0, {
                        'product_id': template_id.product_variant_ids[0].id,
                    })
                )
        self.order_line_service = order_line_service
        self.order_line = order_line
        for line_service in self.order_line_service:
            line_service.product_id_change()
        for line in self.order_line:
            line.product_id_change()


    @api.multi
    def compute_model_ids(self):
        for o in self:
            model_ids = [f.model_id.id for f in o.fleet_ids]
            o.model_ids = model_ids

    @api.multi
    def compute_brand_ids(self):
        for o in self:
            brand_ids = [f.model_id.brand_id.id for f in o.fleet_ids]
            o.brand_ids = brand_ids

    @api.onchange('fleet_ids')
    def fleet_ids_change(self):
        model_ids = [f.model_id.id for f in self.fleet_ids]
        brand_ids = [f.model_id.brand_id.id for f in self.fleet_ids]
        partner_id = False
        if self.fleet_ids:
            if self.fleet_ids[0].driver_id:
                partner_id = self.fleet_ids[0].driver_id.id
            else:
                old_so = self.search([('fleet_ids', 'in', self.fleet_ids[0].id)], limit=1)
                partner_id = old_so.partner_id.id if old_so else False
        value = {
            'model_ids': [(6, False, model_ids)],
            'brand_ids': [(6, False, brand_ids)]
        }
        if not self.partner_id:
            value['partner_id'] = partner_id
        return {
            'value': value,
        }

    @api.depends('fleet_ids.license_plate', 'partner_id')
    def _compute_plate(self):
        for s in self:
            if not s.fleet_ids and s.partner_id.fleet_vehicles:
                license_plates = ' / '.join([fleet.license_plate for fleet in s.partner_id.fleet_vehicles])
                s.license_plate = license_plates
                continue
            plates = s.fleet_ids.mapped('license_plate')
            s.license_plate = u' / '.join(plates)


    @api.model
    def create(self, vals):
        if self._context.get('active_id'):
            fleet_repair_obj = self.env['fleet.repair'].search([('id', '=', self._context.get('active_id'))])
            vals.update({
                'fleet_repair_id': fleet_repair_obj.id,
                'partner_id': fleet_repair_obj.client_id.id or False,
                'client_order_ref': fleet_repair_obj.name,
                'fleet_ids': [(6, 0, fleet_repair_obj.fleet_repair_line.ids)],
                # 'license_plate': fleet_repair_obj.license_plate,
                'car_name': fleet_repair_obj.car_name,
                'vin_sn': fleet_repair_obj.vin_sn,
            })
        if vals.has_key('create_form_fleet') and vals['create_form_fleet'] is True:
            if vals.get('name', _('New')) == _('New'):
                if 'company_id' in vals:
                    vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('car.repair.ord') or _('New')
                else:
                    vals['name'] = self.env['ir.sequence'].next_by_code('car.repair.ord') or _('New')
            res = super(SaleOrder, self).create(vals)
        else:
            res = super(SaleOrder, self).create(vals)
        return res

    @api.multi
    def write(self, vals):
        res = super(SaleOrder, self).write(vals)
        self.update_picking_workorder_repair_if_change_partner_vehicle()
        return res

    def update_picking_workorder_repair_if_change_partner_vehicle(self):
        if self.picking_ids:
            if self.partner_id:
                for picking in self.picking_ids:
                    picking.write({'partner_id': self.partner_id.id})
        if self.workorder_id:
            if self.partner_id:
                self.workorder_id.write({'client_id': self.partner_id.id})
            if self.fleet_ids.ids:
                self.workorder_id.write({'fleet_repair_line': [[6, False, self.fleet_ids.ids]]})
                self.workorder_id.write({'license_plate': self.fleet_ids[0].license_plate})
                self.workorder_id.write({'car_name': self.fleet_ids[0].model_id.name_get()[0][1]})
        if self.fleet_repair_id:
            if self.partner_id:
                self.fleet_repair_id.write({'client_id': self.partner_id.id})
            if self.fleet_ids.ids:
                self.fleet_repair_id.write(
                    {'fleet_repair_line': [[6, False, self.fleet_ids.ids]]})

    @api.model
    @api.one
    def prepare_upsell_value(self):
        vals = self.copy_data()[0]

        vals['upsell'] = True
        vals['origin_id'] = self.id
        vals['date_order'] = datetime.now()

        if 'order_line_service' in vals:
            del vals['order_line_service']

        if 'order_line' in vals:
            del vals['order_line']

        return vals

    @api.multi
    def open_upsell(self):
        action_obj = self.env.ref('car_repair_industry.action_upsell')
        action = action_obj.read([])[0]
        action['res_id'] = self[0].id
        return action

    @api.multi
    def action_cancel(self):
        context = dict(self._context or {})
        if self.workorder_id:
            if self.workorder_id.state in 'done':
                raise ValidationError(_('You can not cancel repair request when Work Order state in done'))
            elif self.workorder_id.state != 'done':
                self.workorder_id.write({'state': 'cancel'})
        if self.invoice_ids:
            for inv_id in self.invoice_ids:
                if inv_id.state in 'paid':
                    raise ValidationError(_('You can not cancel repair request when Invoice state in done'))
        if self.fleet_repair_id:
            self.fleet_repair_id.write({'state': 'cancel'})
        picking_id = self.env['stock.picking'].search([('order_id', '=', self.id)])
        if picking_id:
            picking_id.write({'state': 'cancel'})
        self.write({'cancel_date': datetime.now()})
        return {
            'name': _('Reason Cancel'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'fleet.repair.reason',
            'view_id': False,
            'type': 'ir.actions.act_window',
            # 'domain': [('id', 'in', list)],
            'context': context,
            'target': 'new'
        }

    @api.depends('state', 'order_line_service.invoice_status', 'order_line.invoice_status')
    def _get_invoiced(self):
        """
        Compute the invoice status of a SO. Possible statuses:
        - no: if the SO is not in status 'sale' or 'done', we consider that there is nothing to
          invoice. This is also hte default value if the conditions of no other status is met.
        - to invoice: if any SO line is 'to invoice', the whole SO is 'to invoice'
        - invoiced: if all SO lines are invoiced, the SO is invoiced.
        - upselling: if all SO lines are invoiced or upselling, the status is upselling.

        The invoice_ids are obtained thanks to the invoice lines of the SO lines, and we also search
        for possible refunds created directly from existing invoices. This is necessary since such a
        refund is not directly linked to the SO.
        """
        for order in self:
            if order.order_line:
                invoice_ids = order.order_line.mapped('invoice_lines').mapped('invoice_id').filtered(
                    lambda r: r.type in ['out_invoice', 'out_refund'])
                # Search for invoices which have been 'cancelled' (filter_refund = 'modify' in
                # 'account.invoice.refund')
                # use like as origin may contains multiple references (e.g. 'SO01, SO02')
                refunds = invoice_ids.search([('origin', 'like', order.name)]).filtered(
                    lambda r: r.type in ['out_invoice', 'out_refund'])
                invoice_ids |= refunds.filtered(lambda r: order.name in [origin.strip() for origin in r.origin.split(',')])
                # Search for refunds as well
                refund_ids = self.env['account.invoice'].browse()
                if invoice_ids:
                    for inv in invoice_ids:
                        refund_ids += refund_ids.search(
                            [('type', '=', 'out_refund'), ('origin', '=', inv.number), ('origin', '!=', False),
                             ('journal_id', '=', inv.journal_id.id)])

                # Ignore the status of the deposit product
                deposit_product_id = self.env['sale.advance.payment.inv']._default_product_id()
                line_invoice_status = [line.invoice_status for line in order.order_line if
                                       line.product_id != deposit_product_id]

                if order.state not in ('sale', 'done'):
                    invoice_status = 'no'
                elif any(invoice_status == 'to invoice' for invoice_status in line_invoice_status):
                    invoice_status = 'to invoice'
                elif all(invoice_status == 'invoiced' for invoice_status in line_invoice_status):
                    invoice_status = 'invoiced'
                elif all(invoice_status in ['invoiced', 'upselling'] for invoice_status in line_invoice_status):
                    invoice_status = 'upselling'
                else:
                    invoice_status = 'no'
                order.update({
                    'invoice_count': len(set(invoice_ids.ids + refund_ids.ids)),
                    'invoice_ids': invoice_ids.ids + refund_ids.ids,
                    'invoice_status': invoice_status
                })
            if order.order_line_service:
                invoice_ids = order.order_line_service.mapped('invoice_lines').mapped('invoice_id').filtered(
                    lambda r: r.type in ['out_invoice', 'out_refund'])
                # Search for invoices which have been 'cancelled' (filter_refund = 'modify' in
                # 'account.invoice.refund')
                # use like as origin may contains multiple references (e.g. 'SO01, SO02')
                refunds = invoice_ids.search([('origin', 'like', order.name)]).filtered(
                    lambda r: r.type in ['out_invoice', 'out_refund'])
                invoice_ids |= refunds.filtered(
                    lambda r: order.name in [origin.strip() for origin in r.origin.split(',')])
                # Search for refunds as well
                refund_ids = self.env['account.invoice'].browse()
                if invoice_ids:
                    for inv in invoice_ids:
                        refund_ids += refund_ids.search(
                            [('type', '=', 'out_refund'), ('origin', '=', inv.number), ('origin', '!=', False),
                             ('journal_id', '=', inv.journal_id.id)])

                # Ignore the status of the deposit product
                deposit_product_id = self.env['sale.advance.payment.inv']._default_product_id()
                line_invoice_status = [line.invoice_status for line in order.order_line_service if
                                       line.product_id != deposit_product_id]

                if order.state not in ('sale', 'done'):
                    invoice_status = 'no'
                elif any(invoice_status == 'to invoice' for invoice_status in line_invoice_status):
                    invoice_status = 'to invoice'
                elif all(invoice_status == 'invoiced' for invoice_status in line_invoice_status):
                    invoice_status = 'invoiced'
                elif all(invoice_status in ['invoiced', 'upselling'] for invoice_status in line_invoice_status):
                    invoice_status = 'upselling'
                else:
                    invoice_status = 'no'
                order.update({
                    'invoice_count': len(set(invoice_ids.ids + refund_ids.ids)),
                    'invoice_ids': invoice_ids.ids + refund_ids.ids,
                    'invoice_status': invoice_status
                })

    @api.multi
    def action_invoice_create(self, grouped=False, final=False):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        inv_obj = self.env['account.invoice']
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoices = {}
        references = {}
        for order in self:
            if order.order_line:
                group_key = order.id if grouped else (order.partner_invoice_id.id, order.currency_id.id)
                for line in order.order_line.sorted(key=lambda l: l.qty_to_invoice < 0):
                    if float_is_zero(line.qty_to_invoice, precision_digits=precision):
                        continue
                    if group_key not in invoices:
                        inv_data = order._prepare_invoice()
                        invoice = inv_obj.create(inv_data)
                        references[invoice] = order
                        invoices[group_key] = invoice
                    elif group_key in invoices:
                        vals = {}
                        if order.name not in invoices[group_key].origin.split(', '):
                            vals['origin'] = invoices[group_key].origin + ', ' + order.name
                        if order.client_order_ref and order.client_order_ref not in invoices[group_key].name.split(
                                ', ') and order.client_order_ref != invoices[group_key].name:
                            vals['name'] = invoices[group_key].name + ', ' + order.client_order_ref
                        invoices[group_key].write(vals)
                    if line.qty_to_invoice > 0:
                        line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)
                    elif line.qty_to_invoice < 0 and final:
                        line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)
            if order.order_line_service:
                group_key = order.id if grouped else (order.partner_invoice_id.id, order.currency_id.id)
                for line in order.order_line_service.sorted(key=lambda l: l.qty_to_invoice < 0):
                    if float_is_zero(line.qty_to_invoice, precision_digits=precision):
                        continue
                    if group_key not in invoices:
                        inv_data = order._prepare_invoice()
                        invoice = inv_obj.create(inv_data)
                        references[invoice] = order
                        invoices[group_key] = invoice
                    elif group_key in invoices:
                        vals = {}
                        if order.name not in invoices[group_key].origin.split(', '):
                            vals['origin'] = invoices[group_key].origin + ', ' + order.name
                        if order.client_order_ref and order.client_order_ref not in invoices[group_key].name.split(
                                ', ') and order.client_order_ref != invoices[group_key].name:
                            vals['name'] = invoices[group_key].name + ', ' + order.client_order_ref
                        invoices[group_key].write(vals)
                    if line.qty_to_invoice > 0:
                        line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)
                    elif line.qty_to_invoice < 0 and final:
                        line.invoice_line_create(invoices[group_key].id, line.qty_to_invoice)

            if references.get(invoices.get(group_key)):
                if order not in references[invoices[group_key]]:
                    references[invoice] = references[invoice] | order
            order.write({'state': 'done'})
        if not invoices:
            raise UserError(_('There is no invoicable line.'))

        for invoice in invoices.values():
            if not invoice.invoice_line_ids:
                raise UserError(_('There is no invoicable line.'))
            # If invoice is negative, do a refund invoice instead
            if invoice.amount_untaxed < 0:
                invoice.type = 'out_refund'
                for line in invoice.invoice_line_ids:
                    line.quantity = -line.quantity
            # Use additional field helper function (for account extensions)
            for line in invoice.invoice_line_ids:
                line._set_additional_fields(invoice)
            # Necessary to force computation of taxes. In account_invoice, they are triggered
            # by onchanges, which are not triggered when doing a create.
            invoice.compute_taxes()
            invoice.message_post_with_view('mail.message_origin_link',
                                           values={'self': invoice, 'origin': references[invoice]},
                                           subtype_id=self.env.ref('mail.mt_note').id)
        return [inv.id for inv in invoices.values()]

    @api.depends('order_line_service.price_total', 'order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = amount_total_discount = 0.0
            for line in order.order_line:
                amount_untaxed += line.price_subtotal
                # FORWARDPORT UP TO 10.0
                if order.company_id.tax_calculation_rounding_method == 'round_globally':
                    price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                    taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                                    product=line.product_id, partner=order.partner_shipping_id)
                    amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                    amount_total_discount += line.price_unit * (line.discount / 100.0) * line.product_uom_qty
                else:
                    if line.discount:
                        amount_total_discount += line.price_unit * (line.discount / 100.0) * line.product_uom_qty
                    # amount_tax += line.price_tax
                    price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                    taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                                    product=line.product_id, partner=line.order_id.partner_shipping_id)
                    amount_tax += taxes['total_included'] - taxes['total_excluded']

            for line in order.order_line_service:
                amount_untaxed += line.price_subtotal
                # FORWARDPORT UP TO 10.0
                if order.company_id.tax_calculation_rounding_method == 'round_globally':
                    price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                    taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                                    product=line.product_id, partner=order.partner_shipping_id)
                    amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                    amount_total_discount += line.price_unit * (line.discount / 100.0) * line.product_uom_qty
                else:
                    if line.discount:
                        amount_total_discount += line.price_unit * (line.discount / 100.0) * line.product_uom_qty
                    price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                    taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty,
                                                    product=line.product_id, partner=line.order_id.partner_shipping_id)
                    amount_tax += taxes['total_included'] - taxes['total_excluded']
            order.update({
                'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
                'amount_untaxed_repair': order.pricelist_id.currency_id.round(amount_untaxed),
                'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
                'amount_tax_repair': order.pricelist_id.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax - amount_total_discount,
                'amount_total_repair': amount_untaxed + amount_tax - amount_total_discount,
                'amount_total_discount': amount_total_discount,
                'amount_total_discount_repair': amount_total_discount
            })

    # def __init__(self, *args, **kwargs):
    #     res = super(SaleOrder, self).__init__(*args, **kwargs)
    #     self.check_rpc()

    # @api.onchange("listen_search")
    # def onchange_listen_search(self):
    #     data = eval(self.listen_search)
    #     if data:
    #         order_lines = []
    #         for product in self.env['product.product'].browse(data.get("data")):
    #             order_lines.append({'product_id': product.id, 'product_uom_qty': 1,
    #                                 'name': product.name_get()[0][1]})
    #         self.order_line = order_lines

    @api.model
    def check_rpc(self):
        # global url, db, username, password, uid, mymodels
        get_param = self.env['ir.config_parameter'].get_param
        # info = {"host": "http://localhost:8888", "database": "btek1", "user": "admin", "password": "admin"}
        url = "http://%s:%s" % (get_param('bave_ip'), get_param('bave_port'))
        db = get_param('bave_db')
        username = get_param('bave_user')
        password = get_param('bave_password')
        common = xmlrpclib.ServerProxy('{}/xmlrpc/2/common'.format(url))
        mymodels = None
        uid = 0
        try:
            common.version()
            uid = common.authenticate(db, username, password, {})
            mymodels = xmlrpclib.ServerProxy('{}/xmlrpc/2/object'.format(url))
            sc = mymodels.execute_kw(db, uid, password, 'res.partner', 'check_access_rights', ['read'],
                                     {'raise_exception': False})
        except Exception:
            pass
        return mymodels, url, db, username, password, uid

    def get_origin_order(self, order):
        if order.upsell:
            return self.get_origin_order(order.origin_id)
        return order

    @api.multi
    @api.depends('fleet_repair_id')
    def _compute_repair_id(self):
        for order in self:
            if order.upsell:
                origin = self.get_origin_order(order)

                repair_order_ids = self.env['fleet.repair'].search(
                    [('sale_order_id', '=', origin.id)])
                order.count_fleet_repair = len(repair_order_ids)
                continue

            repair_order_ids = self.env['fleet.repair'].search(
                [('sale_order_id', '=', order.id)])
            order.count_fleet_repair = len(repair_order_ids)

    @api.multi
    @api.depends('is_workorder_created')
    def _compute_workorder_id(self):
        for order in self:
            work_order_ids = self.env['fleet.workorder'].search([('sale_order_id', '=', order.id)])            
            order.workorder_count = len(work_order_ids)

    @api.model
    def call(self, model="", method="", args=[]):
        mymodels, url, db, username, password, uid = self.check_rpc()
        if mymodels is not None:
            return mymodels.execute_kw(db, uid, password, model, method, args)
        return None

    @api.multi
    def get_product(self, domain=[], category_id=0, offset=0, limit=80):
        res = []
        length = 0
        domain_pt = [['vehicle_model_id', 'in', [x.model_id.id for x in self.fleet_ids or self.diagnose_id.fleet_repair_line]]]
        if category_id:
            domain_pt.append(["categ_id", '=', category_id])
            # product_template = self.call("product.template", "search", [[["categ_id", '=', category_id]]]) or []
            # domain.append(['product_tmpl_id', 'in', product_template])
        product_template = self.call("product.template", "search", [domain_pt])
        domain.append(['product_tmpl_id', 'in', product_template])
        length = self.call('product.product', 'search_count', [domain])
        res = self.call('product.product', 'search_read',
                        [domain, ['id', 'name', 'list_price', 'image_medium', 'default_code'], offset, limit])
        res = res or []
        return {'length': length or 0, 'data': res, 'data_store': dict([(x['id'], x) for x in res])}

    @api.model
    def get_product_category(self):
        return self.call(model='product.category', method="search_read", args=[[], ['id', 'name']]) or []

    @api.model
    def order_product(self, values):
        partner = self.env['res.partner'].browse(values.get('partner_id'))
        partner_val = {'active': True, 'name': partner.name, 'street': partner.street, 'street2': partner.street2,
                       'zip': partner.zip, 'state_id': partner.state_id.id, 'city': partner.city,
                       'country_id': partner.country_id.id, 'website': partner.website, 'function': partner.function,
                       'phone': partner.phone, 'mobile': partner.mobile, 'fax': partner.fax, 'email': partner.email,
                       'lang': partner.lang, 'comment': partner.comment, 'company_type': partner.company_type,
                       'image': partner.image, 'type': 'contact'}
        res = self.call(model="res.partner", method="create", args=[partner_val])
        order_line_val = [[0, False,
                           {'product_id': values['product_id'], 'product_uom_qty': values['quantity']}
                           ]]
        sale_val = {'partner_id': res, 'order_line': order_line_val}
        res = self.call(model='sale.order', method="create", args=[sale_val])
        return res

    @api.multi
    def workorder_created(self):
        self.write({'state': 'workorder'})

    @api.multi
    def action_confirm(self):
        order = self
        if order.create_form_fleet is False:
            res = super(SaleOrder, order).action_confirm()
            return res

        wo_vals = {
            'name': order.name or '',
            'client_id': order.partner_id.id,
            'sale_order_id': order.id,
            'fleet_repair_id': order.fleet_repair_id and order.fleet_repair_id.id or False,
            'diagnose_id': False,
            # 'hour': sum((line.est_ser_hour for line in order.diagnose_id.fleet_repair_line), 0.0),
            'hour': 0.0,
            'priority': order.fleet_repair_id and order.fleet_repair_id.priority or False,
            'state': 'draft',
            'user_id': order.user_id.id,
            'confirm_sale_order': True,
            'client_phone': order.partner_id.phone,
            'client_mobile': order.mobile,
            'fleet_repair_line': [(6, 0, order.fleet_ids._ids)],
            'service_type_ids': [(6, 0, order.service_type_ids._ids)],
            'license_plate': order.fleet_ids and order.fleet_ids[0].license_plate or False,
            'car_name': order.fleet_repair_id and order.fleet_repair_id.car_name or False,
            'vin_sn': order.fleet_repair_id and order.fleet_repair_id.vin_sn or False,
            'date_finished': order.validity_date,
            'company_id': order.company_id.id,
        }
        wo_id = self.env['fleet.workorder'].create(wo_vals)

        order.order_line.write({'workorder_id': wo_id.id, 'user_id': order.user_id.id})
        order.order_line_service.write({'workorder_id': wo_id.id, 'user_id': order.user_id.id})
        self.write({'workorder_id': wo_id.id,
                    'is_workorder_created': True
                    })

        today = datetime.utcnow()
        loyalty_obj = self.env['loyalty.management'].search([('config_active', '=', True),
                                                          ('start_date', '<', today.strftime('%Y-%m-%d %H:%M:%S')),
                                                          ('end_date', '>', today.strftime('%Y-%m-%d %H:%M:%S'))])
        if loyalty_obj:
            point = round((self.amount_total * loyalty_obj.points) / loyalty_obj.purchase, 0)
            if point > 1:
                real_point = self.env['res.partner'].search([('id', '=', self.partner_id.id)]).wk_loyalty_points
                real_point += point
                self.partner_id.write({'wk_loyalty_points': real_point})
                self.env['pos.loyalty.history'].create({
                    'source': 'sale',
                    'amount_pay': self.amount_total,
                    'order_id': self.id,
                    'customer_id': self.partner_id.id,
                    'tx_type': 'credit',
                    'tx_date': datetime.utcnow(),
                    'tx_points': point,
                    'remain_points': real_point,
                })
        res = super(SaleOrder, self).action_confirm()
        order.fleet_repair_id.write({'state': 'saleorder'})
        return res

    @api.multi
    def button_view_repair(self):
        list = []
        context = dict(self._context or {})
        domain = [('sale_order_id', '=', self.id)]

        if self[0].upsell:
            origin = self.get_origin_order(self[0])
            domain = [('sale_order_id', '=', origin.id)]

        return {
            'name': _('Phiếu yêu cầu'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'fleet.repair',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': domain,
        }

    @api.multi
    def button_view_workorder(self):
        work_order_ids = self.env['fleet.workorder'].search([('sale_order_id', '=', self.id)])
        res = {
            'name': _('Lệnh làm việc'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'fleet.workorder',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', work_order_ids._ids)],
        }
        if len(work_order_ids) == 1:
            res['view_mode'] = 'form'
            res['res_id'] = work_order_ids[0].id
        return res

## TO CREATE WORKORDER ON SHIP CREATE ###            e

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

    # @api.multi
    # def order_lines_layouted(self):
    #     """
    #     Returns this order lines classified by sale_layout_category and separated in
    #     pages according to the category pagebreaks. Used to render the report.
    #     """
    #     self.ensure_one()
    #     report_pages = [[]]
    #     for category, lines in groupby(self.order_line, lambda l: l.layout_category_id):
    #         # If last added category induced a pagebreak, this one will be on a new page
    #         if report_pages[-1] and report_pages[-1][-1]['pagebreak']:
    #             report_pages.append([])
    #         # Append category to current report page
    #         report_pages[-1].append({
    #             'name': category and category.name or 'Uncategorized',
    #             'subtotal': category and category.subtotal,
    #             'pagebreak': category and category.pagebreak,
    #             'lines': list(lines)
    #         })
    #     if self.order_line:
    #         for repair_line in self.order_line_service:
    #             report_pages[-1][0]['lines'].append(repair_line)
    #     else:
    #         for category, lines in groupby(self.order_line_service, lambda l: l.layout_category_id):
    #             # If last added category induced a pagebreak, this one will be on a new page
    #             if report_pages[-1] and report_pages[-1][-1]['pagebreak']:
    #                 report_pages.append([])
    #             # Append category to current report page
    #             report_pages[-1].append({
    #                 'name': category and category.name or 'Uncategorized',
    #                 'subtotal': category and category.subtotal,
    #                 'pagebreak': category and category.pagebreak,
    #                 'lines': list(lines)
    #             })
    #
    #     return report_pages

    @api.multi
    def open_add_repair_order_line(self):
        action_obj = self.env.ref(
            'car_repair_industry.action_sale_order_add_repair_order_line')
        action = action_obj.read([])[0]
        action['res_id'] = self[0].id
        return action

    @api.multi
    def open_add_order_line(self):
        action_obj = self.env.ref(
            'car_repair_industry.action_sale_order_add_order_line')
        action = action_obj.read([])[0]
        action['res_id'] = self[0].id
        return action

    @api.multi
    def save(self):
        return True

    @api.multi
    def work_lines_layouted(self):
        """
        Returns this order lines classified by sale_layout_category and separated in
        pages according to the category pagebreaks. Used to render the report.
        """
        self.ensure_one()
        report_pages = [[]]
        order_service = []
        prod_order = []
        for wo_id in self.order_line_service:
            order_service.append(wo_id)

        for prod_id in self.order_line:
            prod_order.append(prod_id)

        report_pages[-1].append({
            'order_service': order_service,
            'prod_order': prod_order,
        })

        return report_pages

    @api.multi
    @api.depends('order_line.price_subtotal')
    def _compute_total_price_before_tax_discount(self):
        for s in self:
            total_price_before_tax_discount = 0.0
            for line in s.order_line:
                total_price_before_tax_discount += line.price_subtotal
            s.total_price_before_tax_discount = total_price_before_tax_discount

    @api.multi
    @api.depends('order_line.discount', 'order_line.price_subtotal')
    def _compute_total_product_discount(self):
        for s in self:
            total_product_discount = 0.0
            for line in s.order_line:
                total_product_discount += line.price_subtotal * ((line.discount or 0.0) / 100.0)
            s.total_product_discount = total_product_discount

    @api.multi
    @api.depends('order_line.tax_id', 'order_line.price_subtotal', 'order_line.discount')
    def _compute_total_product_tax(self):
        for s in self:
            total_product_tax = 0.0
            for line in s.order_line:
                line_tax_amount = 0.0
                if line.tax_id:
                    for tax in line.tax_id:
                        line_tax_amount += tax.amount
                total_product_tax += (line.price_subtotal * (1 - (line.discount or 0.0) / 100.0)) * (line_tax_amount / 100.0)
            s.total_product_tax = total_product_tax

    @api.multi
    @api.depends('order_line.sub_price_after_tax_discount')
    def _compute_total_price_after_tax_discount(self):
        for s in self:
            total_price_after_tax_discount = 0.0
            for line in s.order_line:
                total_price_after_tax_discount += line.sub_price_after_tax_discount
            s.total_price_after_tax_discount = total_price_after_tax_discount

    @api.multi
    def bave_print_quotation(self):
        # self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})
        return self.env['report'].get_action(self, 'sale.report_saleorder')

    @api.multi
    def bave_print_saleorder(self):
        return self.env['report'].get_action(self, 'car_repair_industry.report_repairorder')

    @api.multi
    @api.depends('amount_total_repair')
    def _compute_amount_total_repair_in_word(self):
        for s in self:
            if s.amount_total_repair:
                s.amount_total_repair_in_word = s.env['read.number'].docso(int(s.amount_total_repair))

    @api.one
    @api.depends('date_order')
    def _compute_day_order(self):
        user_tz = self.env.user.tz or str(pytz.utc)
        tz_now = datetime.now(pytz.timezone(user_tz))
        difference = tz_now.utcoffset().total_seconds() / 60 / 60
        difference = int(difference)
        if self.date_order:
            date_order_convert = datetime.strptime(self.date_order, '%Y-%m-%d %H:%M:%S') + timedelta(hours=difference)
            self.day_order = str(
                datetime.strftime(date_order_convert, '%d-%m-%Y'))

    @api.one
    @api.depends('validity_date')
    def _compute_day_validity(self):
        user_tz = self.env.user.tz or str(pytz.utc)
        tz_now = datetime.now(pytz.timezone(user_tz))
        difference = tz_now.utcoffset().total_seconds() / 60 / 60
        difference = int(difference)
        if self.validity_date:
            validity_date_convert = datetime.strptime(self.validity_date,'%Y-%m-%d')
            self.day_validity = str(datetime.strftime(validity_date_convert, '%d-%m-%Y'))

    @api.constrains('date_order', 'validity_date')
    def check_date(self):
        user_tz = self.env.user.tz or str(pytz.utc)
        tz_now = datetime.now(pytz.timezone(user_tz))
        difference = tz_now.utcoffset().total_seconds() / 60 / 60
        difference = int(difference)
        if self.date_order:
            date_order = datetime.strptime(self.date_order, '%Y-%m-%d %H:%M:%S') + timedelta(hours=difference)
            day_order = date_order.date()
            if self.validity_date:
                day_validity = datetime.strptime(self.validity_date, '%Y-%m-%d').date()
                if day_validity < day_order:
                    raise ValidationError(_('Validity date can not less than date order.'))

    def auto_process_done_picking(self):
        self.ensure_one()
        for picking in self.picking_ids:
            if picking.state != 'done':
                picking.done_picking()
        return True

    def auto_done_workorder(self):
        self.ensure_one()
        workorder_s = self.env['fleet.workorder'].search(
            [('sale_order_id', '=', self.id)])
        for workorder in workorder_s:
            if workorder.state != 'done':
                workorder.auto_done()
        return True

    def auto_done_picking_workorder_by_config(self):
        self.ensure_one()
        if self.company_id.workorder_auto_done:
            self.auto_done_workorder()
        if self.company_id.picking_auto_done:
            self.auto_process_done_picking()
        return True

    def auto_done_picking_workorder_without_config(self):
        self.ensure_one()
        self.auto_done_workorder()
        self.auto_process_done_picking()
        return self.pre_ordered()

    def open_wizard_auto_done_confirm(self):
        picking_done = True
        workorder_done = True
        for picking in self.picking_ids:
            if picking.state != 'done':
                picking_done = False
                continue
        workorder_s = self.env['fleet.workorder'].search(
            [('sale_order_id', '=', self.id)])
        for workorder in workorder_s:
            if workorder.state != 'done':
                workorder_done = False
                continue

        message = _('delivery and workorder')
        if picking_done and not workorder_done:
            message = _('workorder')
        if not picking_done and workorder_done:
            message = _('delivery')

        if not self.company_id.picking_auto_done \
                and not self.company_id.workorder_auto_done:
            raise UserError(_('You must done {} before ordered!').format(message))
        
        action_obj = self.env.ref(
            'car_repair_industry.action_done_picking_workorder_confirm_repair')
        action = action_obj.read([])[0]
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
        action = self.env.ref('sale.action_view_sale_advance_payment_inv').read()[0]
        return action

    def pre_ordered_again(self):
        if self.workorder_id and self.workorder_id.state != 'done':
            raise UserError(_('Must be done work order before confirm.'))
        if self.picking_ids:
            for picking in self.picking_ids:
                if picking.state != 'done':
                    raise UserError(_('Must be done picking before confirm.'))
        action = self.env.ref('sale.action_view_sale_advance_payment_inv').read()[0]
        action['context'] = {'default_advance_payment_method': 'percentage'}
        return action

class sale_advance_payment_inv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"
    _description = "Sales Advance Payment Invoice"

    @api.multi
    def create_invoices(self):
        res = super(sale_advance_payment_inv, self).create_invoices()
        if self._context.get('active_id'):
            sale_obj = self.env['sale.order'].browse(self._context.get('active_id'))
            if sale_obj.fleet_repair_id:
                sale_obj.fleet_repair_id.write({'state': 'invoiced'})

            sale_obj.write(
                {
                    'done_date': datetime.now()
                }
            )

        return res


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    repair_line_ids = fields.Many2many(
        'repair.order.line',
        'repair_order_line_invoice_rel',
        'invoice_line_id', 'order_line_id',
        string='Repair Order Lines', readonly=True, copy=False)


class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.multi
    def post(self):
        inv_id = self.env['account.invoice'].search([('id', '=', self._context.get('active_id'))])
        inv_id.invoice_validate()
        inv_id.write({'state': 'paid'})
        return super(AccountPayment, self).post()


class AccountInvoice(models.Model):
    _inherit = "account.invoice"
    
    create_form_fleet = fields.Boolean(string='Fleet')
    order_id = fields.Many2one('sale.order', 'Order')
    license_plate = fields.Char(related='order_id.license_plate', store=True)
    
    @api.model
    def create(self, vals):
        if vals.get('origin'):
            sale_obj = self.env['sale.order'].search([('name', '=', vals.get('origin'))], limit=1)
            invoice_obj = self.env['account.invoice'].search([('number', '=', vals.get('origin')),
                                                              ('type', '=', 'out_invoice')])
            if sale_obj and sale_obj.workorder_id and sale_obj.workorder_id.fleet_repair_id:
                vals.update({'create_form_fleet': True})
            if sale_obj and sale_obj.fleet_ids:
                vals.update({'create_form_fleet': True})
            if sale_obj:
                vals['order_id'] = sale_obj[0].id
            if not sale_obj and invoice_obj:
                vals['order_id'] = invoice_obj.order_id.id
        return super(AccountInvoice, self).create(vals= vals)

    @api.multi
    def write(self,vals):
        if vals.get('state'):
            if vals.get('state') == 'paid':
                sale_obj = self.env['sale.order'].search([('id', '=', self.order_id.id)])
                if sale_obj  and sale_obj.workorder_id and sale_obj.workorder_id.fleet_repair_id:
                    repair_obj = self.env['fleet.repair'].search([('id', '=', sale_obj.workorder_id.fleet_repair_id.id)])
                    repair_obj.write({'state': 'done'})
        return super(AccountInvoice, self).write(vals)

    @api.multi
    def cash_action_invoice_open(self):
        to_open_invoices = self.filtered(lambda inv: inv.state != 'open')
        if to_open_invoices.filtered(lambda inv: inv.state not in ['proforma2', 'draft']):
            raise UserError(_("Invoice must be in draft or Pro-forma state in order to validate it."))
        to_open_invoices.action_date_assign()
        to_open_invoices.action_move_create()
        action = self.env.ref('car_repair_industry.cash_action_account_invoice_payment').read()[0]
        if action:
            return action
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def bank_action_invoice_open(self):
        to_open_invoices = self.filtered(lambda inv: inv.state != 'open')
        if to_open_invoices.filtered(lambda inv: inv.state not in ['proforma2', 'draft']):
            raise UserError(_("Invoice must be in draft or Pro-forma state in order to validate it."))
        to_open_invoices.action_date_assign()
        to_open_invoices.action_move_create()
        action = self.env.ref('car_repair_industry.bank_action_account_invoice_payment').read()[0]
        if action:
            return action
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def action_account_invoice_refund(self):
        for s in self:
            is_paid = False
            if not s.payment_ids:
                is_paid = False
            else:
                for payment in s.payment_ids:
                    if payment.state != 'draft':
                        is_paid = True
            if not is_paid:
                raise UserError(
                    _('You can not refund unpaid invoices.'))
            total_refund = 0.0
            if s.refund_invoice_ids:
                for refund_invoice in s.refund_invoice_ids:
                    total_refund += refund_invoice.amount_total
            if total_refund < (s.amount_total - s.residual):
                action_obj = self.env.ref(
                    'account.action_account_invoice_refund')
                action = action_obj.read([])[0]
                return action
            else:
                raise UserError(
                    _('You can not refund more than the amount paid. '
                      'Please check invoice refund again. '
                      'Must be delete invoice refund have state is draft to create new invoice refund.'))


class mail_compose_message(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def send_mail(self, auto_commit=False):
        if self._context.get('default_model') == 'sale.order' and self._context.get('default_res_id') and self._context.get('mark_so_as_sent'):
            order = self.env['sale.order'].browse([self._context['default_res_id']])
            if order.state == 'draft':
                order.state = 'sent'
                if order.diagnose_id and order.diagnose_id.fleet_repair_id:
                    order.diagnose_id.fleet_repair_id.write({'state': 'quote'})
            self = self.with_context(mail_post_autofollow=True)
        return super(mail_compose_message, self).send_mail(auto_commit=auto_commit)
