# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class FleetRepairReason(models.TransientModel):
    _name = 'fleet.repair.reason'

    text = fields.Char(string='Reason', required=True)

    def add_reason(self):
        if self._context.get('active_model') == 'fleet.repair':
            fleet_id = self.env['fleet.repair'].browse(self._context.get('active_id'))
            so_id = self.env['sale.order'].search([('fleet_repair_id', '=', fleet_id.id)])
            so_id.write({'reason_cancel': self.text, 'state': 'cancel'})

        if self._context.get('active_model') == 'sale.order':
            so_id = self.env['sale.order'].search([('id', '=', self._context.get('active_id'))])
            so_id.write({'reason_cancel': self.text, 'state': 'cancel'})
        return {'type': 'ir.actions.act_window_close'}
