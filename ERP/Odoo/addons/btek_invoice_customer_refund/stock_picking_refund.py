# -*- coding: utf-8 -*-

from odoo import models, api, fields


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.model
    def _get_invoice_line_vals(self, move, partner, inv_type):
        res = super(StockMove, self)._get_invoice_line_vals(move, partner, inv_type)

        if res and 'account_id' in res and move.location_id.usage == 'customer':
            product_o = move.product_id
            new_account_id = product_o.x_property_account_refund.id or product_o.categ_id.x_property_account_refund_categ.id
            if new_account_id:
                res.update({'account_id': new_account_id})
        return res
