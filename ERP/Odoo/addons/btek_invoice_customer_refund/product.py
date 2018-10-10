#!/usr/bin/python

from odoo import models, fields, api, _


class product(models.Model):
    _inherit = ["product.template"]

    x_property_account_refund = fields.Many2one(
        'account.account',
        string="Customer Return Account",
        help="This account will be used for invoices to value customer return.")

