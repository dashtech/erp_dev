# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by 73lines
# See LICENSE file for full copyright and licensing details.

from openerp import models, fields


class BlogPost(models.Model):
    _name = 'blog.post'
    _inherit = ['blog.post', 'carousel.slider']

    image = fields.Binary('Image', attachment=True)
