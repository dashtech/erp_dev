# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by 73lines
# See LICENSE file for full copyright and licensing details.

from odoo import models


class ProductBrand(models.Model):
    _name = 'product.brand'
    _inherit = ['product.brand', 'carousel.slider']
