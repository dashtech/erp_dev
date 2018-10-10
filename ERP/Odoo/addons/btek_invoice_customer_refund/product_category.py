#!/usr/bin/python

from odoo import api, fields, models, _

class ProductCategory(models.Model):
    _inherit = "product.category"

    x_property_account_refund_categ = fields.Many2one('account.account',
        string="Customer Return Account",
        help="This account will be used for invoices to value customer return.")

