# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import AccessDenied, UserError
import odoo.addons.decimal_precision as dp
import datetime


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    def get_time_dotay(self):
        for r in self:
            if r.payment_date:
                return (r.payment_date[8:10]) + '/' + (r.payment_date[5:7]) + '/' + (r.payment_date[0:4])
            else:
                return ""

    def get_move_line(self):
        for r in self:
            if r.move_line_ids:
                return r.move_line_ids

    def _num2word_with_tax_pay(self):
        for item in self:
            in_word = self.env['account.voucher']._num2word_with_tax_pay(item)
            return in_word

    def get_rate(self):
        for r in self:
            if r.company_id.currency_id.rate:
                return r.company_id.currency_id.rate
            else:
                return 0

    def _get_quyen_so(self, number):
        if number:
            if number.count('/') >=2 and ('PT' in number or 'PC' in number):
                return number.split('/', 1)[1]
            return number
        return '..............'


