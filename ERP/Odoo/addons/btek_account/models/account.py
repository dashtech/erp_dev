# -*- coding: utf-8 -*-
from lxml import etree
from odoo import models, fields, api, _, exceptions
from odoo.exceptions import AccessDenied, UserError
import odoo.addons.decimal_precision as dp
from odoo.osv.orm import setup_modifiers


class BtekAccountPayment(models.Model):
    _inherit = "account.payment"

    invoice_id = fields.Many2one('account.invoice', readonly=True)
    amount_text = fields.Text(compute='_compute_amount_text', readonly=True)
    pre_order_html = fields.Html(readonly=True, compute='pre_order')

    @api.model
    def create(self, vals):
        context = self.env.context
        if context.get('active_model', False) == 'account.invoice':
            if context.get('active_id', False):
                vals['invoice_id'] = context.get('active_id')
        res = super(BtekAccountPayment, self).create(vals)
        return res

    @api.multi
    @api.depends('amount', 'currency_id')
    def _compute_amount_text(self):
        for s in self:
            if s.amount:
                read_amount = s.env['read.number'].docso(int(s.amount))
                if s.currency_id:
                    if s.currency_id.currency_text:
                        read_amount = read_amount + ' ' + s.currency_id.currency_text + u' chẵn.'
                s.amount_text = read_amount

    def pre_post(self):
        action = self.env.ref('btek_account.action_pre_confirm_account_payment').read()[0]
        action['res_id'] = self.id
        return action

    @api.depends('amount')
    def pre_order(self):
        for s in self:
            amount = s.format_money(s.amount, s.currency_id.name or '')
            if s.currency_id.currency_text:
                text = u' ' + unicode(s.currency_id.currency_text)
            else:
                text = u' đồng'
            amount_int = int(s.amount)
            amount_fl = int(str(s.amount - amount_int)[:1])
            amount_txt = s.env['read.number'].docso(amount_int) + text
            # s.env['read.number'].docso(amount_fl) + text
            s.pre_order_html = _(u'''
                            <span style="text-align: center; color: blue;">
                                <h1>Are you sure payment this?</h1>
                            </span></br>
                            <span style="font-size: 13; text-align: center">
                                <h3> Amount total payment : {}</h3>
                            </span></br>
                            <span style="text-align: center"><h3>Equal text : <i>{}</i></h3></span>
                            ''').format(amount, amount_txt)

    def format_money(self, num, unit=''):
        num = round(num / 1, 2)
        num_text = '{:,}'.format(num).replace(
            '.', '/').replace(',', '.').replace('/', ',') + ' ' + unit
        return num_text

    @api.multi
    def account_cancel(self):
        self.unlink()
        return True


class AccountInvoiceTemplate(models.Model):
    _name = 'account.invoicel.template'
    _rec_name = 'template_symbol'

    template_symbol = fields.Char(string=(u"Ký hiệu mẫu hóa đơn"), size=128, required=True)


class AccountInvoiceSymbol(models.Model):
    _name = 'account.invoicel.symbol'
    _rec_name = 'invoice_symbol'

    invoice_symbol = fields.Char(string=(u"Ký hiệu hóa đơn"), size=128, required=True)


class AccountInvoiceNumber(models.Model):
    _name = 'account.invoice.number'

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    template_symbol = fields.Many2one('account.invoicel.template', string=(u"Ký hiệu mẫu hóa đơn"), size=128)
    invoice_symbol = fields.Many2one('account.invoicel.symbol', string=(u"Ký hiệu hóa đơn"), size=128)
    active = fields.Boolean(string='Active')
    company_id = fields.Many2one('res.company', required=True, default=_get_company)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'
    _description = 'Account invoice'

    note = fields.Char()
    @api.multi
    def check_partner_account(self, raise_error=True):
        for invoice in self:
            if invoice.type in ('out_invoice', 'out_refund'):
                account = invoice.partner_id.property_account_receivable_id
                if account.user_type_id.type == 'receivable':
                    continue
                if not raise_error:
                    return False
                raise UserError(_(
                    "Error: Incorrect customer account setup, \nYou have to choose a receivable account that has the type of receivable!"))
            elif invoice.type in ('in_invoice', 'in_refund'):
                account = invoice.partner_id.property_account_payable_id
                if account.user_type_id.type == 'payable':
                    continue
                if not raise_error:
                    return False
                raise UserError(_(
                    "Error: Incorrect customer account setup, \nYou have to choose a payable account that has the type of payable!"))
        return True

    @api.multi
    def action_invoice_open(self):
        self.check_partner_account()
        return super(AccountInvoice, self).action_invoice_open()

    @api.multi
    def confirm_and_cash_payment(self):
        return self.confirm_and_payment()\

    @api.multi
    def confirm_and_bank_payment(self):
        return self.confirm_and_payment('bank')

    @api.multi
    def confirm_and_payment(self, type='cash'):
        if self[0].state == 'draft':
            self.action_invoice_open()

        payment_field_list = [
            "payment_type",
            "partner_type",
            "invoice_ids",
            "partner_id",
            "state",
            "journal_id",
            "hide_payment_method",
            "payment_method_id",
            "payment_method_code",
            "amount",
            "currency_id",
            "payment_date",
            "communication",
            "payment_difference",
            "payment_difference_handling",
            "writeoff_account_id",
        ]

        vals = self.env['account.payment'
        ].with_context(default_invoice_ids=[(4, self[0].id, None)]
                       ).default_get(payment_field_list)

        journal_domain = [('at_least_one_inbound', '=', True),
                          ('type', '=', type),
                          ('x_type', '=', 'receipt')]
        journals = self.env['account.journal'].search(journal_domain)
        if not journals:
            raise UserError(_('Error: cannot find payment journal!'))

        vals['journal_id'] = journals[0].id

        if vals.get('company_id'):
            company_id = self.env['res.company'].browse(vals['company_id'])
            vals['currency_id'] = journals[0].currency_id and \
                              journals[0].currency_id.id or \
                              company_id.currency_id.id

        payment_methods = vals.get('payment_type', '') == 'inbound' and \
                          journals[0].inbound_payment_method_ids or \
                          journals[0].outbound_payment_method_ids
        vals['payment_method_id'] = payment_methods and \
                                    payment_methods[0].id or False

        if vals.get('payment_method_code', '') == 'electronic':
            vals['payment_token_id'] = \
                self.env['payment.token'].search(
                    [('partner_id', '=', vals['partner_id']),
                     ('acquirer_id.auto_confirm', '!=', 'authorize')],
                    limit=1)
        else:
            vals['payment_token_id'] = False
        vals['invoice_id'] = self.id
        payment = self.env['account.payment'].create(vals)
        payment.post()
        return True

    @api.multi
    def default_symbol_tem(self):
        number = self.env['account.invoice.number'].search([('active', '=', True),('company_id', '=', self.env.user.company_id.id)], limit=1)
        if number:
            if number.template_symbol:
                return number.template_symbol

    @api.multi
    def default_symbol(self):
        number = self.env['account.invoice.number'].search([('active', '=', True),('company_id', '=', self.env.user.company_id.id)], limit=1)
        if number:
            if number.invoice_symbol: return number.invoice_symbol

    purchase_person = fields.Many2one('res.partner', u'Nguời mua hàng', states={'draft': [('readonly', False)]})
    vat_partner = fields.Char(string=u'Đối tượng VAT', size=128, states={'draft': [('readonly', False)]})
    tax_code = fields.Char(size=128, string=u'Mã số thuế', states={'draft': [('readonly', False)]})
    template_symbol = fields.Many2one('account.invoicel.template', string=(u"Ký hiệu mẫu hóa đơn"), size=128, states={'draft': [('readonly', False)]},
                                  default=default_symbol_tem)
    invoice_symbol = fields.Many2one('account.invoicel.symbol', string=(u"Ký hiệu hóa đơn"), size=128, states={'draft': [('readonly', False)]},
                                 default=default_symbol)

    supplier_invoice_number = fields.Char(string='Supplier Invoice Number',
                                          help="The reference of this invoice as provided by the supplier.",
                                          readonly=True, states={'draft': [('readonly', False)],'open': [('readonly', False)]})
    root_invoice_id = fields.Many2one('account.invoice', readonly=True)
    refund_invoice_ids = fields.One2many('account.invoice', 'root_invoice_id', readonly=True)
    number_refund = fields.Integer(compute='_compute_number_refund')

    account_payment_ids = fields.One2many('account.payment', 'invoice_id', readonly=True)
    number_payment = fields.Integer(compute='_compute_number_payment')
    discount_value = fields.Monetary(
        compute='_compute_discount_value',
        store=True)
    amount_undiscount_untaxed = fields.Monetary(
        compute='_compute_amount_undiscount_untaxed',
        store=True)
    total_amount_service = fields.Monetary(compute='_get_total_amount_service')
    total_amount_product = fields.Monetary(compute='_get_total_amount_product')
    amount_total_in_word = fields.Text(compute='_compute_amount_total_in_word')

    @api.depends('invoice_line_ids.price_unit',
                 'invoice_line_ids.quantity')
    def _compute_amount_undiscount_untaxed(self):
        for invoice in self:
            amount_undiscount_untaxed = 0
            for line in invoice.invoice_line_ids:
                amount_undiscount_untaxed += \
                    line.price_unit * line.quantity
            invoice.amount_undiscount_untaxed = \
                amount_undiscount_untaxed

    @api.depends('invoice_line_ids.discount',
                 'invoice_line_ids.price_unit',
                 'invoice_line_ids.quantity')
    def _compute_discount_value(self):
        for invoice in self:
            discount_value = 0
            for line in invoice.invoice_line_ids:
                discount_value += \
                    line.discount * 0.01 * line.price_unit \
                    * line.quantity
            invoice.discount_value = discount_value

    @api.multi
    @api.depends('refund_invoice_ids')
    def _compute_number_refund(self):
        for s in self:
            if s.refund_invoice_ids:
                s.number_refund = len(s.refund_invoice_ids)

    @api.multi
    @api.depends('account_payment_ids')
    def _compute_number_payment(self):
        for s in self:
            if s.account_payment_ids:
                s.number_payment = len(s.account_payment_ids)

    @api.multi
    def compute_root_quantity(self, root_invoice_id):
        root_product_quatity_dict = {}
        for line in root_invoice_id.invoice_line_ids:
            product_id = line.product_id
            if not root_product_quatity_dict.get(product_id, False):
                root_product_quatity_dict[product_id] = 0
            root_product_quatity_dict[product_id] += line.quantity
        return root_product_quatity_dict

    @api.multi
    def compute_refund_quantity(self, invoice_line_ids):
        refund_product_quatity_dict = {}
        for line in invoice_line_ids:
            product_id = line.product_id
            if not refund_product_quatity_dict.get(product_id, False):
                refund_product_quatity_dict[product_id] = 0
            refund_product_quatity_dict[product_id] += line.quantity
        return refund_product_quatity_dict

    @api.multi
    def write(self, vals):
        res = super(AccountInvoice, self).write(vals)
        for s in self:
            if s.root_invoice_id:
                if s.invoice_line_ids:
                    root_product_quatity_dict = s.compute_root_quantity(s.root_invoice_id)
                    refund_product_quatity_dict = s.compute_refund_quantity(s.invoice_line_ids)
                    for line in s.invoice_line_ids:
                        if refund_product_quatity_dict.get(line.product_id) > root_product_quatity_dict.get(line.product_id):
                            raise UserError(_('Can not refund with quantity great than root quantity for a product. Please check again product quantity in invoice refund'))
        return res

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(AccountInvoice, self).fields_view_get(view_id=view_id, view_type=view_type,
                                                          toolbar=toolbar, submenu=submenu)

        if not self.env.context.get('refund_invoice_action'):
            return res
        view_customer = self.env.ref('account.invoice_form').id
        view_supplier = self.env.ref('account.invoice_supplier_form').id

        if view_id != view_customer and view_id != view_supplier:
            return res
        elif view_id == view_customer:
            doc = etree.XML(res['arch'])
            if doc.xpath("//field[@name='partner_id']"):
                note_partner_id = doc.xpath("//field[@name='partner_id']")[0]
                note_partner_id.set('readonly', '1')
                setup_modifiers(note_partner_id, res['fields']['partner_id'])

            if doc.xpath("//field[@name='currency_id']"):
                note_currency_id = doc.xpath("//field[@name='currency_id']")[0]
                note_currency_id.set('readonly', '1')
                setup_modifiers(note_currency_id, res['fields']['currency_id'])
            res['arch'] = etree.tostring(doc)

            doc_o2m = etree.XML(res['fields']['invoice_line_ids']['views']['tree']['arch'])
            if doc_o2m.xpath("//tree"):
                node_tree = doc_o2m.xpath("//tree")[0]
                node_tree.set('create', 'false')

            if doc_o2m.xpath("//field[@name='product_id']"):
                node_product_id = doc_o2m.xpath("//tree/field[@name='product_id']")[0]
                node_product_id.set('readonly', '1')
                setup_modifiers(node_product_id, res['fields']['invoice_line_ids'])

            if doc_o2m.xpath("//field[@name='account_id']"):
                node_account_id = doc_o2m.xpath("//tree/field[@name='account_id']")[0]
                node_account_id.set('readonly', '1')
                setup_modifiers(node_account_id, res['fields']['invoice_line_ids'])

            if doc_o2m.xpath("//field[@name='uom_id']"):
                node_uom_id = doc_o2m.xpath("//tree/field[@name='uom_id']")[0]
                node_uom_id.set('readonly', '1')
                setup_modifiers(node_uom_id, res['fields']['invoice_line_ids'])

            if doc_o2m.xpath("//field[@name='discount']"):
                node_discount = doc_o2m.xpath("//tree/field[@name='discount']")[0]
                node_discount.set('readonly', '1')
                setup_modifiers(node_discount, res['fields']['invoice_line_ids'])

            if doc_o2m.xpath("//field[@name='invoice_line_tax_ids']"):
                node_invoice_line_tax_ids = doc_o2m.xpath("//tree/field[@name='invoice_line_tax_ids']")[0]
                node_invoice_line_tax_ids.set('readonly', '1')
                setup_modifiers(node_invoice_line_tax_ids, res['fields']['invoice_line_ids'])

            if doc_o2m.xpath("//field[@name='price_unit']"):
                node_price_unit = doc_o2m.xpath("//tree/field[@name='price_unit']")[0]
                node_price_unit.set('readonly', '1')
                setup_modifiers(node_price_unit, res['fields']['invoice_line_ids'])

            res['fields']['invoice_line_ids']['views']['tree']['arch'] = etree.tostring(doc_o2m)
        else:
            doc = etree.XML(res['arch'])
            if doc.xpath("//field[@name='partner_id']"):
                note_partner_id = doc.xpath("//field[@name='partner_id']")[0]
                note_partner_id.set('readonly', '1')
                setup_modifiers(note_partner_id, res['fields']['partner_id'])

            if doc.xpath("//field[@name='currency_id']"):
                note_currency_id = doc.xpath("//field[@name='currency_id']")[0]
                note_currency_id.set('readonly', '1')
                setup_modifiers(note_currency_id, res['fields']['currency_id'])
            res['arch'] = etree.tostring(doc)

            doc_o2m = etree.XML(
                res['fields']['invoice_line_ids']['views']['tree']['arch'])
            if doc_o2m.xpath("//tree"):
                node_tree = doc_o2m.xpath("//tree")[0]
                node_tree.set('create', 'false')

            if doc_o2m.xpath("//field[@name='product_id']"):
                node_product_id = \
                doc_o2m.xpath("//tree/field[@name='product_id']")[0]
                node_product_id.set('readonly', '1')
                setup_modifiers(node_product_id,
                                res['fields']['invoice_line_ids'])

            if doc_o2m.xpath("//field[@name='account_id']"):
                node_account_id = \
                doc_o2m.xpath("//tree/field[@name='account_id']")[0]
                node_account_id.set('readonly', '1')
                setup_modifiers(node_account_id,
                                res['fields']['invoice_line_ids'])

            if doc_o2m.xpath("//field[@name='uom_id']"):
                node_uom_id = doc_o2m.xpath("//tree/field[@name='uom_id']")[0]
                node_uom_id.set('readonly', '1')
                setup_modifiers(node_uom_id, res['fields']['invoice_line_ids'])

            if doc_o2m.xpath("//field[@name='discount']"):
                node_discount = \
                doc_o2m.xpath("//tree/field[@name='discount']")[0]
                node_discount.set('readonly', '1')
                setup_modifiers(node_discount,
                                res['fields']['invoice_line_ids'])

            if doc_o2m.xpath("//field[@name='invoice_line_tax_ids']"):
                node_invoice_line_tax_ids = \
                doc_o2m.xpath("//tree/field[@name='invoice_line_tax_ids']")[0]
                node_invoice_line_tax_ids.set('readonly', '1')
                setup_modifiers(node_invoice_line_tax_ids,
                                res['fields']['invoice_line_ids'])

            if doc_o2m.xpath("//field[@name='price_unit']"):
                node_price_unit = \
                doc_o2m.xpath("//tree/field[@name='price_unit']")[0]
                node_price_unit.set('readonly', '1')
                setup_modifiers(node_price_unit,
                                res['fields']['invoice_line_ids'])

            res['fields']['invoice_line_ids']['views']['tree'][
                'arch'] = etree.tostring(doc_o2m)
        return res

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None,
                        description=None, journal_id=None):
        res = super(AccountInvoice,self)._prepare_refund(invoice=invoice, date_invoice=date_invoice, date=date,
                        description=description, journal_id=journal_id)
        context = dict(self._context or {})
        root_invoice_id = self.browse(context.get('active_ids'))
        res['root_invoice_id'] = root_invoice_id[0].id
        return res

    @api.multi
    def action_view_invoice_customer_refund(self):
        context = dict(self._context or {})
        active_id = self[0].id
        action_obj = self.env.ref('btek_account.action_invoice_refund_tree1')
        action = action_obj.read([])[0]
        action['res_id'] = self._ids[0]
        domain = eval(action['domain'])
        domain.append(('root_invoice_id', '=', active_id))
        action['domain'] = domain
        return action

    @api.multi
    def action_view_invoice_supplier_refund(self):
        context = dict(self._context or {})
        active_id = self[0].id
        action_obj = self.env.ref('btek_account.action_invoice_supplier_refund_tree2')
        action = action_obj.read([])[0]
        action['res_id'] = self._ids[0]
        domain = eval(action['domain'])
        domain.append(('root_invoice_id', '=', active_id))
        action['domain'] = domain
        return action

    @api.multi
    def action_view_payment_form_invoice(self):
        context = dict(self._context or {})
        active_id = self[0].id
        action_obj = self.env.ref('account.action_account_payments')
        action = action_obj.read([])[0]
        action['res_id'] = self._ids[0]
        domain = [('invoice_id', '=', active_id)]
        action['domain'] = domain
        return action

    @api.multi
    @api.depends('invoice_line_ids')
    def _get_total_amount_service(self):
        for s in self:
            total_service = 0.0
            if s.invoice_line_ids:
                for invoice_line in s.invoice_line_ids:
                    if invoice_line.product_id.type == 'service':
                        total_service += invoice_line.price_subtotal
            s.total_amount_service = total_service

    @api.multi
    @api.depends('invoice_line_ids')
    def _get_total_amount_product(self):
        for s in self:
            total_product = 0.0
            if s.invoice_line_ids:
                for invoice_line in s.invoice_line_ids:
                    if invoice_line.product_id.type != 'service':
                        total_product += invoice_line.price_subtotal
            s.total_amount_product = total_product

    @api.multi
    @api.depends('amount_total')
    def _compute_amount_total_in_word(self):
        for s in self:
            if s.amount_total:
                s.amount_total_in_word = s.env['read.number'].docso(int(s.amount_total))


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.one
    @api.depends('price_unit', 'discount', 'invoice_line_tax_ids', 'quantity', 'product_id'
        , 'invoice_id.partner_id', 'invoice_id.currency_id')
    def _compute_prices(self):
        currency = self.invoice_id and self.invoice_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = self.invoice_line_tax_ids.compute_all(price, currency, self.quantity, product=self.product_id,
                                                     partner=self.invoice_id.partner_id)
        # self.price_subtotal = taxes['total']
        # self.price_tax = taxes['total_included'] - taxes['total']
        # currency_obj = self.env['res.users'].browse(self._uid).company_id.currency_id
        if taxes.get('taxes'):
            x_rounding_price_tax = 0.0
            for item in taxes.get('taxes'):
                x_rounding_price_tax += item['amount']
            self.x_rounding_price_tax = x_rounding_price_tax
        if self.invoice_id and taxes.get('taxes'):
            # self.price_subtotal = self.invoice_id.currency_id.round(self.price_subtotal)
            # self.price_tax = taxes['total_included'] - taxes['total']
            x_rounding_price_tax = 0.0
            for item in taxes.get('taxes'):
                x_rounding_price_tax += item['amount']
            self.x_rounding_price_tax = x_rounding_price_tax

    x_rounding_price_tax = fields.Float(
        string=u'Tiền thuế', digits=dp.get_precision('Account'),
        compute=_compute_prices)
    discount_value = fields.Monetary(
        digits=dp.get_precision('Account'),
        compute='_compute_discount_value', store=True)
    price_subtotal_not_discount_tax = fields.Monetary(
        string='Price subtotal', store=True,
        digits=dp.get_precision('Account'),
        compute='_compute_price_subtotal_not_discount_tax')

    @api.depends('discount', 'price_unit', 'quantity')
    def _compute_discount_value(self):
        for line in self:
            discount = line.discount or 0
            line.discount_value = \
                discount * 0.01 * line.price_unit \
                * line.quantity

    @api.depends('price_unit', 'quantity')
    def _compute_price_subtotal_not_discount_tax(self):
        for line in self:
            line.price_subtotal_not_discount_tax = \
                line.price_unit * line.quantity

    @api.onchange('discount')
    def onchange_discount(self):
        if self.discount and self.discount > 100:
            self.discount = 0.0
            title = _("Warning for discount")
            message = _('Discount greater 100%')
            warning = {
                'title': title,
                'message': message,
            }
            return {'warning': warning}


class AccountInvoiceRefund(models.TransientModel):
    """Refunds invoice"""
    _inherit = "account.invoice.refund"

    # overwrite function compute_refund base
    @api.multi
    def compute_refund(self, mode='refund'):
        from odoo.tools.safe_eval import safe_eval
        inv_obj = self.env['account.invoice']
        inv_tax_obj = self.env['account.invoice.tax']
        inv_line_obj = self.env['account.invoice.line']
        context = dict(self._context or {})
        xml_id = False

        for form in self:
            created_inv = []
            date = False
            description = False
            for inv in inv_obj.browse(context.get('active_ids')):
                if inv.state in ['draft', 'proforma2', 'cancel']:
                    raise UserError(_('Cannot refund draft/proforma/cancelled invoice.'))
                if inv.reconciled and mode in ('cancel', 'modify'):
                    raise UserError(_(
                        'Cannot refund invoice which is already reconciled, invoice should be unreconciled first. You can only refund this invoice.'))

                date = form.date or False
                description = form.description or inv.name
                refund = inv.refund(form.date_invoice, date, description, inv.journal_id.id)

                created_inv.append(refund.id)
                if mode in ('cancel', 'modify'):
                    movelines = inv.move_id.line_ids
                    to_reconcile_ids = {}
                    to_reconcile_lines = self.env['account.move.line']
                    for line in movelines:
                        if line.account_id.id == inv.account_id.id:
                            to_reconcile_lines += line
                            to_reconcile_ids.setdefault(line.account_id.id, []).append(line.id)
                        if line.reconciled:
                            line.remove_move_reconcile()
                    refund.action_invoice_open()
                    for tmpline in refund.move_id.line_ids:
                        if tmpline.account_id.id == inv.account_id.id:
                            to_reconcile_lines += tmpline
                    to_reconcile_lines.filtered(lambda l: l.reconciled == False).reconcile()
                    if mode == 'modify':
                        invoice = inv.read(inv_obj._get_refund_modify_read_fields())
                        invoice = invoice[0]
                        del invoice['id']
                        invoice_lines = inv_line_obj.browse(invoice['invoice_line_ids'])
                        invoice_lines = inv_obj.with_context(mode='modify')._refund_cleanup_lines(invoice_lines)
                        tax_lines = inv_tax_obj.browse(invoice['tax_line_ids'])
                        tax_lines = inv_obj._refund_cleanup_lines(tax_lines)
                        invoice.update({
                            'type': inv.type,
                            'date_invoice': form.date_invoice,
                            'state': 'draft',
                            'number': False,
                            'invoice_line_ids': invoice_lines,
                            'tax_line_ids': tax_lines,
                            'date': date,
                            'origin': inv.origin,
                            'fiscal_position_id': inv.fiscal_position_id.id,
                        })
                        for field in inv_obj._get_refund_common_fields():
                            if inv_obj._fields[field].type == 'many2one':
                                invoice[field] = invoice[field] and invoice[field][0]
                            else:
                                invoice[field] = invoice[field] or False
                        inv_refund = inv_obj.create(invoice)
                        if inv_refund.payment_term_id.id:
                            inv_refund._onchange_payment_term_date_invoice()
                        created_inv.append(inv_refund.id)
                xml_id = (inv.type in ['out_refund', 'out_invoice']) and 'action_invoice_refund_tree1' or \
                         (inv.type in ['in_refund', 'in_invoice']) and 'action_invoice_supplier_refund_tree2'
                # Put the reason in the chatter
                subject = _("Invoice refund")
                body = description
                refund.message_post(body=body, subject=subject)
        if xml_id:
            result = self.env.ref('btek_account.%s' % (xml_id)).read()[0]
            invoice_domain = safe_eval(result['domain'])
            invoice_domain.append(('id', 'in', created_inv))
            result['domain'] = invoice_domain
            return result
        return True


class AccountAccount(models.Model):
    _inherit = 'account.account'

    @api.multi
    @api.constrains('parent_id', 'parent_id.company_id', 'company_id')
    def _check_parent_company(self):
        for account in self:
            if not account.parent_id:
                continue
            if account.company_id.id != account.parent_id.company_id.id:
                raise exceptions.ValidationError(_(
                    'Account {} cannot set parent is other company account!'
                ).format(account.code))
        return True


class AccountTax(models.Model):
    _inherit = 'account.tax'

    name = fields.Char(string='Tax Name', required=True, translate=False)

    @api.model
    def change_tax_name(self):
        for tax_info in [
            {'tax_ex_id': 'l10n_vn.1_tax_purchase_vat0', 'name': '0%'},
            {'tax_ex_id': 'l10n_vn.1_tax_purchase_vat10', 'name': '10%'},
            {'tax_ex_id': 'l10n_vn.1_tax_purchase_vat5', 'name': '5%'},
            {'tax_ex_id': 'l10n_vn.1_tax_sale_vat0', 'name': '0%'},
            {'tax_ex_id': 'l10n_vn.1_tax_sale_vat10', 'name': '10%'},
            {'tax_ex_id': 'l10n_vn.1_tax_sale_vat5', 'name': '5%'},
        ]:
            name = tax_info['name']
            tax_ex_id = tax_info['tax_ex_id']
            try:
                tax = self.env.ref(tax_ex_id)
                tax.write({'name': name})
            except:
                pass
        return True
