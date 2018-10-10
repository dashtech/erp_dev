#!/usr/bin/python
# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _


class btek_account_payment(models.Model):
    _inherit = "account.payment"

    number = fields.Char(string='Number')
    recipient_pay = fields.Char(string=u'Người nhận, nộp')
    x_name = fields.Char(string=u'Lý do')

    @api.onchange('payment_type')
    def _onchange_payment_type(self):
        res = super(btek_account_payment, self)._onchange_payment_type()
        for r in self:
            if r.payment_type == 'outbound':
                res['domain']['journal_id'].append(('x_type', '=', 'payment'))
                x_type = 'payment'
            elif r.payment_type == 'inbound':
                res['domain']['journal_id'].append(('x_type', '=', 'receipt'))
                x_type = 'receipt'
            else:
                res['domain']['journal_id'].append(('x_type', 'in', ('payment', 'receipt')))
                x_type = False
            if self._context.get('kh_tienmat', False):
                self.partner_type = 'customer'
            elif self._context.get('ncc_tienmat', False):
                self.partner_type = 'supplier'

            if self._context.get('cash', False):
                for i, item in enumerate(res['domain']['journal_id']):
                    if item[0] == 'type':
                        res['domain']['journal_id'][i] = ('type', '=', 'cash')
                        user_login = self.env['res.users'].search([('id', '=', self._context.get('uid'))])
                        journal_id = self.env['account.journal'].search([('x_type', '=', x_type),
                                                                         ('type', '=', 'cash'),
                                                                         ('company_id', '=', user_login.company_id.id)])
                        if journal_id:
                            self.journal_id = journal_id[0].id

            if self._context.get('bank', False):
                for i, item in enumerate(res['domain']['journal_id']):
                    if item[0] == 'type':
                        res['domain']['journal_id'][i] = ('type', '=', 'bank')
                        user_login = self.env['res.users'].search([('id', '=', self._context.get('uid'))])
                        journal_id = self.env['account.journal'].search(
                            [('x_type', '=', x_type), ('type', '=', 'bank'),
                             ('company_id', '=', user_login.company_id.id)])
                        if journal_id:
                            self.journal_id = journal_id[0].id
        return res

    def _get_counterpart_move_line_vals(self, invoice=False):
        res = super(btek_account_payment,self)._get_counterpart_move_line_vals(invoice=False)
        if not self.x_name:
            return res
        res['name'] = self.x_name
        return res
