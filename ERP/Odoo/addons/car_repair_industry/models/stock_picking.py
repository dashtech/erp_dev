# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from datetime import date, time, datetime
import xmlrpclib
from datetime import timedelta
import re
from odoo.exceptions import UserError, ValidationError
from itertools import groupby
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT


class DeliveryOrder(models.Model):
    _inherit = 'stock.picking'

    repair_id = fields.Many2one('fleet.repair', 'Service Request')
    order_id = fields.Many2one('sale.order', 'Order')
    license_plate = fields.Char(compute='_compute_plate')
    create_from_fleet = fields.Boolean(related='order_id.create_form_fleet', store=True)
    note = fields.Char()

    @api.model
    def create(self, values):
        # res = super(DeliveryOrder, self).create(values)
        if not values.has_key('origin'):
            return super(DeliveryOrder, self).create(values)
        if self._context.has_key('active_model') and self._context['active_model'] == 'sale.order':
            so_id = self.env['sale.order'].browse(self._context['active_id'])
            if so_id.create_form_fleet is True:
                values['repair_id'] = so_id.fleet_repair_id.id
            if so_id:
                values['order_id'] = so_id.id
        else:
            so_id = self.env['sale.order'].search([('name', '=', values['origin'])],order='id desc')
            if so_id:
                if so_id[0].create_form_fleet is True:
                    values['repair_id'] = so_id[0].fleet_repair_id.id
                if so_id[0]:
                    values['order_id'] = so_id[0].id
        return super(DeliveryOrder, self).create(values)

    @api.depends('order_id.fleet_ids')
    def _compute_plate(self):
        for s in self:
            if not s.order_id:
                return
            else:
                plates = [fleet.license_plate for fleet in s.order_id.fleet_ids]
                if plates:
                    s.license_plate = ' / '.join(plates)

    @api.multi
    def do_new_transfer(self):
        confirm_pick = super(DeliveryOrder, self).do_new_transfer()
        if self.order_id.state == 'cancel':
            raise UserError(_('You can not confirm a picking when sale order is cancel!'))
        else:
            return confirm_pick

    @api.multi
    def done_picking(self):
        if self.state == 'done':
            return True
        if self.state in ['confirmed'] :
            # picking.action_assign()
            self.force_assign()
        if self.state in ['assigned','partially_available']:
            self.force_assign()
            act = self.do_new_transfer()
            if not act:
                return
            res_id = act['res_id']
            res_model = act['res_model']
            wizard = self.env[res_model].browse(res_id)
            wizard.process()

        if self.state != 'done' and not self.env.context.get('pre', False):
            self.with_context(pre=True).done_picking()
        return True
