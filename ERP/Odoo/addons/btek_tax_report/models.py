#!/usr/bin/python

from odoo import models, fields, api, _


class AccountInvoiceTax(models.Model):
    _inherit = "account.invoice.tax"


    x_base = fields.Monetary(sring='Base', related='base', store=True)
