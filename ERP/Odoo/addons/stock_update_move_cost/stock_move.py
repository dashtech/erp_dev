#!/usr/bin/python
# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
import datetime
from odoo import SUPERUSER_ID


class StockMove(models.Model):
    _inherit = "stock.move"

    def product_price_update_before_done(self):
        '''
        This method adapts the price on the product when necessary
        '''
        super(StockMove, self).product_price_update_before_done()
        product_obj = self.pool.get('product.product')
        tmpl_dict = {}
        for move in self:
            if move.location_id.usage == 'internal' and move.product_id.cost_method == 'average':
                move.write({'price_unit': move.product_id.standard_price})
            if (move.location_id.usage == 'customer') and (move.product_id.cost_method == 'average'):
                product = move.product_id
                prod_tmpl_id = move.product_id.product_tmpl_id.id
                qty_available = move.product_id.product_tmpl_id.qty_available
                if tmpl_dict.get(prod_tmpl_id):
                    product_avail = qty_available + tmpl_dict[prod_tmpl_id]
                else:
                    tmpl_dict[prod_tmpl_id] = 0
                    product_avail = qty_available
                if product_avail <= 0:
                    new_std_price = move.price_unit
                else:
                    amount_unit = product.standard_price
                    new_std_price = ((amount_unit * product_avail) + (move.price_unit * move.product_qty)) / (
                        product_avail + move.product_qty)
                tmpl_dict[prod_tmpl_id] += move.product_qty
                ctx = dict(self._context or {}, force_company=move.company_id.id)
                product_obj.write(self._cr, SUPERUSER_ID, [product.id], {'standard_price': new_std_price}, context=ctx)
