# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by 73lines
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    cover_banner = fields.Binary(string='Cover Banner')
    categ_title_background = fields.Char(string='Category Background Color')
    categ_title_color = fields.Char(string='Category Font Color')
    categ_icon = fields.Char('Category Icon')


class Website(models.Model):
    _inherit = 'website'

    @api.multi
    def get_categories(self):
        category_ids = self.env['product.public.category'].search(
            [('parent_id', '=', False)])
        res = {
            'categories': category_ids,
        }
        return res
