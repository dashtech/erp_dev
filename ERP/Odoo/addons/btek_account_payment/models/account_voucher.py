# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import AccessDenied, UserError
import odoo.addons.decimal_precision as dp
import datetime


class AccountVoucherLine(models.Model):
    _inherit = 'account.voucher.line'

    @api.onchange('price_subtotal', 'tax_ids')
    def onchange_x_rounding_price_tax(self):
        res = {}
        if self.tax_ids:

            currency = self.voucher_id.journal_id.currency_id or self.voucher_id.journal_id.company_id.currency_id
            taxes = self.tax_ids.compute_all(self.price_subtotal, quantity=1)['taxes']
            amount = 0.0
            for tax in taxes:
                amount += currency.round(tax['amount'])
            self.x_rounding_price_tax = amount
            res = {'x_rounding_price_tax': amount}
        return {'value': res}

    x_description = fields.Char(string=u'Diễn giải')
    x_supplier_invoice_number = fields.Char(string=u"Số hóa đơn")
    x_rounding_price_tax = fields.Float(string='Tiền thuế', digits=dp.get_precision('Account'))

    @api.onchange('product_id', 'voucher_id', 'price_unit', 'company_id')
    def _onchange_line_details(self):
        res = super(AccountVoucherLine,self)._onchange_line_details()
        if self.product_id.is_cost_item is True:
            if self.product_id.property_account_expense_id:
                self.account_id = self.product_id.property_account_expense_id.id
                self.name = self.product_id.name
        return res


class AccountVoucherTax(models.Model):
    _name = "x.account.voucher.tax"
    _description = "Voucher Tax"
    _order = 'sequence'

    @api.one
    @api.depends('base', 'base_amount', 'amount', 'tax_amount')
    def _compute_factors(self):
        self.factor_base = self.base_amount / self.base if self.base else 1.0
        self.factor_tax = self.tax_amount / self.amount if self.amount else 1.0

    @api.v8
    def compute(self, voucher):
        tax_grouped = {}
        current_rate = 1.0
        currency = voucher.currency_id.with_context(date=voucher.date or fields.Date.context_today(voucher),
                                                    current_rate=current_rate)
        company_currency = voucher.company_id.currency_id
        for line in voucher.line_ids:
            taxes = line.tax_ids.compute_all(line.price_subtotal, quantity=1)['taxes']
            for tax in taxes:
                amount = tax['amount']
                val = {
                    'voucher_id': voucher.id,
                    'voucher_line_id': line.id,
                    'name': tax['name'],
                    'amount': line.x_rounding_price_tax or amount,
                    'manual': False,
                    'sequence': tax['sequence'],
                    'base': currency.round(line.price_subtotal),
                    'x_partner_id': line.voucher_id.partner_id and line.voucher_id.partner_id.id or False,
                    'x_supplier_invoice_number': line.x_supplier_invoice_number and line.x_supplier_invoice_number.strip() or False,
                    'x_invoice_symbol': False,
                    'x_date_invoice': line.voucher_id.account_date or False,
                    'x_registration_date': datetime.date.today() or False,
                }
                val['base_code_id'] = tax['refund_account_id']
                val['base_amount'] = tax['base']
                val['tax_amount'] = tax['amount']
                val['account_id'] = tax['account_id'] or line.account_id.id
                key = (tax['id'], val['base_code_id'], val['account_id'], val['x_partner_id'],
                       val['x_supplier_invoice_number'], val['x_invoice_symbol'])
                if not key in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['base'] += val['base']
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base_amount'] += val['base_amount']
                    tax_grouped[key]['tax_amount'] += val['tax_amount']

        for t in tax_grouped.values():
            t['base'] = currency.round(t['base'])
            t['amount'] = currency.round(t['amount'])
            t['base_amount'] = currency.round(t['base_amount'])
            t['tax_amount'] = currency.round(t['tax_amount'])
        return tax_grouped

    voucher_id = fields.Many2one('account.voucher', string='Voucher Line', ondelete='cascade', index=True)
    name = fields.Char(string='Tax Description', required=True)
    account_id = fields.Many2one('account.account', string='Tax Account', required=True)
    base = fields.Float(string='Base', digits=dp.get_precision('Account'))
    manual = fields.Boolean(string='Manual', default=True)
    sequence = fields.Integer(string='Sequence', help="Gives the sequence order when displaying a list of voucher tax.")
    base_amount = fields.Float(string='Base Code Amount', digits=dp.get_precision('Account'), default=0.0)
    base_code_id = fields.Many2one('account.tax.code', string='Base Code', help="The account basis of the tax declaration.")
    tax_code_id = fields.Many2one('account.tax.code', string='Tax Code', help="The tax basis of the tax declaration.")
    amount = fields.Float(string='Amount', digits=dp.get_precision('Account'))
    tax_amount = fields.Float(string='Tax Code Amount', digits=dp.get_precision('Account'), default=0.0)
    company_id = fields.Many2one('res.company', string='Company', related='account_id.company_id', store=True, readonly=True)
    factor_base = fields.Float(string='Multipication factor for Base code', compute='_compute_factors')
    factor_tax = fields.Float(string='Multipication factor Tax code', compute='_compute_factors')
    x_partner_id = fields.Many2one('res.partner', string=(u"Đối tượng"))
    x_supplier_invoice_number = fields.Char(string=(u"Số hóa đơn"), help="The reference of this invoice as provided by the supplier.")
    x_invoice_symbol = fields.Char(string=(u"Ký hiệu hóa đơn"), size=128)
    x_date_invoice = fields.Date(string=(u"Ngày hạch toán"))
    x_registration_date = fields.Date(string=(u"Ngày hóa đơn"))
    voucher_line_id = fields.Many2one('account.voucher.line', copy=False, ondelete='cascade')


class AccountVoucher(models.Model):
    _inherit = 'account.voucher'

    recipient_pay = fields.Char(string=u'Người nhận, nộp')
    x_name = fields.Char(string=u'Lý do')
    x_voucher_tax_line = fields.One2many('x.account.voucher.tax', 'voucher_id', string='Tax Lines', readonly=True,
                                         states={'draft': [('readonly', False)]})

    x_amount_untax = fields.Monetary(string='Amount Untaxed', digits=dp.get_precision('Account'), compute='get_amount_untaxed')
    check_tax = fields.Boolean(default=False)

    @api.constrains('x_voucher_tax_line')
    def _check_related_x_voucher_tax_line(self):
        for r in self:
            if len(r.line_ids.ids) < len(r.x_voucher_tax_line.ids):
                raise UserError(('Không thể áp dụng 2 loại thuế.!'))

    @api.multi
    def first_move_line_get(self, move_id, company_currency, current_currency):
        res = super(AccountVoucher, self).first_move_line_get(move_id, company_currency, current_currency)
        if not self.x_name:
            return res
        res['name'] = self.x_name
        return res

    @api.multi
    @api.depends('line_ids')
    def get_amount_untaxed(self):
        if self.line_ids:
            amount = 0
            for r in self.line_ids:
                amount += r.price_subtotal
            self.x_amount_untax = amount


    @api.multi
    def proforma_voucher(self):
        if self.check_tax is False:
            self.button_reset_taxes()
        res = super(AccountVoucher, self).proforma_voucher()
        return res

    @api.onchange('journal_id')
    def onchang_journal_voucher(self):
        if self.journal_id:
            if self.journal_id.default_debit_account_id and self.journal_id.x_type == 'receipt':
                self.account_id = self.journal_id.default_debit_account_id
            if self.journal_id.default_credit_account_id and self.journal_id.x_type == 'payment':
                self.account_id = self.journal_id.default_credit_account_id
    @api.one
    def button_reset_taxes(self):
        account_voucher_tax = self.env['x.account.voucher.tax']
        ctx = dict(self._context)
        for voucher in self:
            self._cr.execute("DELETE FROM x_account_voucher_tax WHERE voucher_id=%s AND manual is False", (voucher.id,))
            self.invalidate_cache()
            partner = voucher.partner_id
            if partner.lang:
                ctx['lang'] = partner.lang
            for taxe in account_voucher_tax.compute(voucher.with_context(ctx)).values():
                account_voucher_tax.create(taxe)
            voucher.check_tax = True
        return self.with_context(ctx).write({'line_ids': []})

    @api.multi
    def account_move_get(self):
        res = super(AccountVoucher, self).account_move_get()
        if res.has_key('name'):
            if res['name'].startswith('CSHT'):
                res['name'] = res['name'].replace('CSHT', 'PT')
            elif res['name'].startswith('CSHC'):
                res['name'] = res['name'].replace('CSHC', 'PC')
        return res
