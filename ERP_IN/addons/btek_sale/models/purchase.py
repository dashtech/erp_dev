# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.multi
    def _prepare_stock_moves(self, picking):
        res = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)

        consignment = self[0].order_id.consignment

        if not consignment:
            return res

        location_id = \
            self[0].order_id.picking_type_id.default_location_src_id.id

        if not location_id:
            return res

        for line in res:
            line['location_id'] = location_id

        return res

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    consignment = fields.Boolean(default=False)

    @api.model
    def _prepare_picking(self):
        res = super(PurchaseOrder, self)._prepare_picking()

        if not self.consignment:
            return res

        location_id = \
            self.picking_type_id.default_location_src_id.id

        if not location_id:
            return res

        if location_id:
            res['location_id'] = location_id

        return res
