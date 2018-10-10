# -*- coding: utf-8 -*-

from odoo import fields, models, api
from datetime import date, time, datetime


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    real_date_invoice = fields.Char('Real Date Invoice', compute='get_real_date_invoice')

    @api.one
    @api.depends('date_invoice')
    def get_real_date_invoice(self):
        if self.date_invoice:
            real_date = datetime.strptime(self.date_invoice, '%Y-%m-%d')
            self.real_date_invoice = str(datetime.strftime(real_date, '%d-%m-%Y'))

    @api.multi
    def invoice_print(self):
        """ Print the invoice and mark it as sent, so that we can see more
            easily the next step of the workflow
        """
        self.ensure_one()
        self.sent = True
        return self.env['report'].get_action(self, 'btek_account.btek_report_invoice_document')