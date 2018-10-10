#!/usr/bin/python
# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _

class btek_account_journal(models.Model):
    _inherit = "account.journal"

    x_type = fields.Selection([
            ('payment', _(u'Chi tiền')),
            ('receipt',  _(u'Thu tiền')),
        ], string='Kiểu')



class btek_account_move(models.Model):
    _inherit = "account.move"

    x_voucher_day = fields.Date(string='Ngày chứng từ')

class btek_account_move_line(models.Model):
    _inherit = "account.move.line"

    x_account_groups = fields.Text(string='Nhóm tài khoản')


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    _sql_constraints = [
        ('unique_number', 'Check(1=1)', 'Account Number must be unique'),
    ]

    # @api.constrains('acc_number')
    # def _check_account_number(self):
    #     for record in self:
    #         if self.acc_number
    #     for journal_id in self.journal_id:
    #         if self.acc_number == journal_id.bank_acc_number and journal_id.type == 'bank' and joir:

