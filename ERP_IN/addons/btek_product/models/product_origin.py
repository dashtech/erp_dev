# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _

class ProductOrigin(models.Model):
    _name = 'product.origin'

    name = fields.Char()
    code = fields.Char()
    addr = fields.Char('Address')
