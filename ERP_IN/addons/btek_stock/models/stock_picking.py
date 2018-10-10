# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime,timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare


class StockPickingInherit(models.Model):
    _inherit = 'stock.picking'

    check_return = fields.Boolean('Returned')
    is_return = fields.Boolean('Is return picking')
    source_picking = fields.Many2one('stock.picking', string='Source Picking')
    state = fields.Selection([
        ('draft', 'Draft'), ('cancel', 'Cancelled'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Out stock'),
        ('partially_available', 'Partially stock'),
        ('assigned', 'Wait export'), ('done', 'Exported')], string='Status', compute='_compute_state',
        copy=False, index=True, readonly=True, store=True, track_visibility='onchange',
        help=" * Draft: not confirmed yet and will not be scheduled until confirmed\n"
             " * Waiting Another Operation: waiting for another move to proceed before it becomes automatically available (e.g. in Make-To-Order flows)\n"
             " * Out stock: still waiting for the availability of products\n"
             " * Partially stock: some products are available and reserved\n"
             " * Wait export: products reserved, simply waiting for confirmation.\n"
             " * Exported: has been processed, can't be modified or cancelled anymore\n"
             " * Cancelled: has been cancelled, can't be confirmed anymore")

    @api.multi
    def do_new_transfer(self):
        res = super(StockPickingInherit, self).do_new_transfer()
        is_check = self.move_lines.filtered(lambda x: x.state == 'assigned')
        if not is_check:
            for record in self.move_lines:
                    precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
                    product_qty = record.product_uom._compute_quantity(record.product_uom_qty, record.product_id.uom_id)
                    if float_compare(record.product_id.virtual_available, product_qty, precision_digits=precision) == -1:
                        raise UserError(_(
                                'You plan to sell %s %s but you only have %s %s available!\nThe stock on hand is %s %s.') % \
                                       (record.product_uom_qty, record.product_uom.name, record.product_id.virtual_available,
                                        record.product_id.uom_id.name, record.product_id.qty_available,
                                        record.product_id.uom_id.name))
        return res

    @api.multi
    def action_cancel(self):
        res = super(StockPickingInherit, self).action_cancel()
        if self.order_id.state != 'done':
            for line in self.order_id.order_line:
                move_delete = self.move_lines.filtered(lambda x: x.product_id.id == line.product_id.id)
                if line.product_id.id == move_delete.product_id.id:
                    line.unlink()
        else:
            raise UserError(_('You can not cancel picking when sale order state has done!'))
        return res


class ReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    source_picking = fields.Many2one('stock.picking', string='Source Picking')

    @api.model
    def default_get(self, fields):
        res = super(ReturnPicking, self).default_get(fields)
        picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))
        res['source_picking'] = picking.id
        return res

    @api.multi
    def _create_returns(self):
        res = super(ReturnPicking, self)._create_returns()
        picking_return = self.env['stock.picking'].search([('id', '=', res[0])])
        picking_return.write({'is_return': True, 'source_picking': self.source_picking.id})
        return res


class ReturnPickingLine(models.TransientModel):
    _inherit = "stock.return.picking.line"

    @api.model
    def create(self, values):
        res = super(ReturnPickingLine, self).create(values)
        wazard_id = self.env['stock.return.picking'].search([('id', '=', values['wizard_id'])])
        pack_ids = wazard_id.source_picking.pack_operation_product_ids

        for line in pack_ids:
            if values['product_id'] == line.product_id.id and values['quantity'] > line.qty_done:
                raise UserError(_('You can not set quantity return greater quantity move done!'))
        return res
