#!/usr/bin/python
# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _

class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    @api.model
    def _default_journal(self):
        voucher_type = self._context.get('voucher_type', 'sale')
        company_id = self._context.get('company_id', self.env.user.company_id.id)
        domain = [
            ('type', '=', voucher_type),
            ('company_id', '=', company_id),
        ]
        if self._context.get('journal_type', ['NO'])[0] == 'cash' and self._context.get('x_type', ['NO'])[0] == 'receipt':
            domain = [('type','=','cash'),('x_type','=','receipt')]
        if self._context.get('voucher_type', False) == 'purchase':
            domain = [('type','=','cash'),('x_type','=','payment')]
        if self._context.get('journal_type', ['NO'])[0] == 'bank' and self._context.get('x_type', ['NO'])[0] == 'receipt':
            domain = [('type','=','bank'),('x_type','=','receipt')]
        if self._context.get('journal_type', ['NO'])[0] == 'bank' and self._context.get('x_type', ['NO'])[0] == 'payment':
            domain = [('type','=','bank'),('x_type','=','payment')]
        return self.env['account.journal'].search(domain, limit=1)

    @api.model
    def get_company_id(self):
        return self.env.user.company_id

    journal_id = fields.Many2one('account.journal', 'Journal',
                                 required=True, readonly=True, states={'draft': [('readonly', False)]},
                                 default=_default_journal)

    company_id = fields.Many2one('res.company', 'Company',
                                 required=True, readonly=True, states={'draft': [('readonly', False)]},
                                 default=get_company_id)
