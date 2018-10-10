# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by 73lines
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class UserWishList(models.Model):
    _name = 'user.wishlist'

    product_template_id = fields.Many2one('product.template', string='Product')
    qty = fields.Float(string='Qty', default=1)
    user_id = fields.Many2one('res.users', string='User')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.multi
    def is_favorite(self):
        self.ensure_one()
        if self.id:
            result_wish = self.env['user.wishlist'].search(
                [('product_template_id', '=', self.id),
                 ('user_id', '=', self.env.uid)])
            if len(result_wish) > 0:
                return True
            else:
                return False
