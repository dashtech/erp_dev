# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError


class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'

    html =  fields.Html(readonly=True, compute='compute_pre')
    @api.multi
    def auto_confirm_purchase(self):
        res_comfirm = self.button_confirm()
        self.env.cr.execute('select auto_picking from purchase_config_settings order by id DESC limit 1')
        result = self.env.cr.fetchone()
        if not result or 'auto' in result:
            action = self.picking_ids.do_new_transfer()
            if action:
                res_id = action['res_id']
                res_model = action['res_model']
                self.env[res_model].browse(res_id).process()
        # cont = self.env.context.copy()
        # cont.update({
        #     'active_model': 'purchase.order',
        #     'default_purchase_id': self[0].id,
        #     'active_ids': self.ids,
        #     'active_id': self[0].id,
        #     'type': 'in_invoice',
        # })
        # field = [u'comment', u'message_follower_ids', u'date_due', u'partner_bank_id', u'root_invoice_id', u'company_id', u'company_currency_id', u'template_symbol', u'payments_widget', u'partner_id', u'message_ids', u'purchase_id', u'reference', u'supplier_invoice_number', u'journal_id', u'amount_tax', u'state', u'fiscal_position_id', u'refund_invoice_ids', u'invoice_line_ids', u'number_refund', u'account_id', u'reconciled', u'origin', u'residual', u'move_name', u'date_invoice', u'vat_partner', u'payment_term_id', u'outstanding_credits_debits_widget', u'date', u'amount_untaxed', u'move_id', u'amount_total', u'currency_id', u'name', u'user_id', u'type', u'tax_code', u'number', u'tax_line_ids', u'invoice_symbol', u'has_outstanding', u'purchase_person']
        # aivals = self.env['account.invoice'].with_context(**cont).default_get(field)
        journal_id = self.env['account.journal'].search([('type', '=', 'purchase'),
                ('company_id', '=', self.company_id.id)], limit=1)
        account_id = self.env['account.account'].search([('internal_type', '=', 'payable'),
                ('company_id', '=', self.company_id.id),
                ('code', 'like', '331%')], limit=1)
        if not journal_id:
            raise UserError(_('Can not find account journal!'))
        vals = {
            'partner_id': self.partner_id.id,
            'origin': self.name,
            'journal_id': journal_id.id,
            'account_id': account_id.id,
            'type': 'in_invoice',
            'purchase_id': self.id,
        }
        res_iv = self.env['account.invoice'].create(vals)
        res_iv.purchase_order_change()
        # res_iv._onchange_product_id()
        res_iv._onchange_partner_id()
        res_iv._onchange_invoice_line_ids()
        # self.auto_create_invoice()
        self.auto_confirm_invoice()
        return self.action_view_invoice()

    @api.multi
    def auto_confirm_invoice(self):
        for invoice in self.invoice_ids:
            if invoice.state != 'draft':
                continue
            invoice.action_invoice_open()
        return True

    def pre_confirm_order(self):
        action = self.env.ref('bave_basic.action_pre_confirm_po').read()[0]
        action['res_id'] = self.id
        return action

    @api.depends('amount_total')
    def compute_pre(self):
        for s in self:
            amount_total = s.format_money(s.amount_total, s.currency_id.name or '')
            if s.currency_id.currency_text:
                text = u' ' + unicode(s.currency_id.currency_text)
            else:
                text = u' đồng'
            amount_int = int(s.amount_total)
            amount_fl = int(str(s.amount_total-amount_int)[:1])
            amount_txt = s.env['read.number'].docso(amount_int) + text
                         # s.env['read.number'].docso(amount_fl) + text
            s.html = _(u'''
            <span style="text-align: center; color: blue;">
                <h1>Are you sure ordering this?</h1>
            </span></br>
            <span style="font-size: 13; text-align: center">
                <h3> Amount total payment : {}</h3>
            </span></br>
            <span style="text-align: center"><h3>Equal text : <i>{}</i></h3></span>
            ''').format(amount_total, amount_txt)

    def format_money(self, num, unit=''):
        num = round(num / 1, 2)
        num_text = '{:,}'.format(num).replace(
            '.', '/').replace(',', '.').replace('/', ',') + ' ' + unit
        return num_text
