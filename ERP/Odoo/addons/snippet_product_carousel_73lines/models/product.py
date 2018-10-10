# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by 73lines
# See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = ['product.template', 'carousel.slider']
    _name = 'product.template'

    is_new = fields.Boolean(string='Is New ?')
    is_best_seller = fields.Boolean(string='Is Best Seller ?')
    is_trending = fields.Boolean(string='Is Trending ?')
    is_on_sale = fields.Boolean(String='Is On Sale ?')
