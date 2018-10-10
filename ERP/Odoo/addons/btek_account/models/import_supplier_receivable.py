# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime,timedelta
import pytz

account_code_index = 1
partner_code_index = 2
currency_index = 4
debit_index = 5
credit_index = 6


MIN_COL_NUMBER = 7


class ImportCustomerReceivable(models.TransientModel):
    _name = 'wizard.import.supplier.receivable'
    _inherits = {'ir.attachment': 'attachment_id'}
    _import_model_name = 'account.move'
    # _import_date_format = '%d-%m-%Y'

    account_move_name = fields.Char(required=True)
    journal_id = fields.Many2one('account.journal', required=True)
    date = fields.Date(required=True)
    voucher_day = fields.Date()
    account_reciprocal = fields.Many2one('account.account', required=True)
    template_file_url = fields.Char(compute='_compute_template_file_url',
                                    default=lambda self:
                                    self.env['ir.config_parameter'].
                                    get_param('web.base.url') +
                                    '/btek_account/static/import_template/'
                                    'import_supplier_receivable.xlsx')

    @api.multi
    def _compute_template_file_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        url = base_url + '/btek_account/static/import_template/import_supplier_receivable.xlsx'
        for ip in self:
            ip.template_file_url = url

    @api.multi
    def import_supplier_receivable(self):
        # read excel file
        data = self.datas
        sheet = False

        user = self.env.user
        path = '/import_supplier_receivable_template_' \
               + user.login + '_' + str(
            self[0].id) + '_' + str(
            datetime.now()) + '.xls'
        path = path.replace(' ', '_')

        read_excel_obj = self.env['read.excel']
        excel_data = read_excel_obj.read_file(data, sheet, path)

        # check content excel data
        if len(excel_data) < 3:
            raise ValidationError(_('Cannot import empty file!'))

        # delete header excel (2 first line in file)
        del excel_data[0]
        del excel_data[0]

        # check number column excel file
        if len(excel_data[0]) < MIN_COL_NUMBER:
            raise ValidationError(_(
                'Format file incorrect, you must import file have at least {} column!').format(
                MIN_COL_NUMBER))

        # check format data in excell file(unicode, str, ...)
        self.verify_excel_data(excel_data)

        # Get db data dict for many2one, many2many field: dict with key = name,
        # value = ID db
        partner_dict, account_dict, currency_dict = \
            self.get_db_data(excel_data)

        row_num = 2
        for row in excel_data:
            row_num += 1
            vals_debit, vals_credit= self.get_value_from_excel_row(row, row_num, partner_dict, account_dict, currency_dict)
            if vals_debit['line_ids'][0][2]['debit'] != 0:
                self.create_record(vals_debit)
            if vals_credit['line_ids'][0][2]['credit'] != 0:
                self.create_record(vals_credit)

        return True

    @api.multi
    def verify_excel_data(self, excel_data):
        row_count = 2

        for row in excel_data:
            row_count += 1

            if not row[account_code_index]:
                raise UserError(
                    _('Error: row {} account code invalid!').format(row_count))

            try:
                row[account_code_index] = unicode(row[account_code_index])
            except:
                raise UserError(
                    _('Error: row {} account code invalid!').format(row_count))

            if not row[partner_code_index]:
                raise UserError(
                    _('Error: row {} supplier code invalid!').format(row_count))

            try:
                row[partner_code_index] = unicode(row[partner_code_index])
            except:
                raise UserError(
                    _('Error: row {} supplier code invalid!').format(row_count))

            if not row[currency_index]:
                raise UserError(
                    _('Error: row {} currency invalid!').format(row_count))

            try:
                row[currency_index] = unicode(row[currency_index])
            except:
                raise UserError(
                    _('Error: row {} currency code invalid!').format(row_count))

            if not row[debit_index]:
                row[debit_index] = 0.0
            try:
                row[debit_index] = float(row[debit_index])
            except:
                raise UserError(
                    _('Error: row {} debit invalid!').format(row_count))
            if not row[credit_index]:
                row[credit_index] = 0.0
            try:
                row[credit_index] = float(row[credit_index])
            except:
                raise UserError(
                    _('Error: row {} credit invalid!').format(row_count))

        return True

    @api.multi
    def get_db_data(self, excel_data):
        partner_code_list = []
        account_code_list = []
        currency_list = []
        for row in excel_data:
            partner_code = row[partner_code_index].strip()
            account_code = row[account_code_index].strip()
            currency = row[currency_index].strip()
            if partner_code:
                partner_code_list.append(partner_code)
            if account_code:
                account_code_list.append(account_code)
            if currency:
                currency_list.append(currency)

        partner_s = \
            self.env['res.partner'].search_read(
                [('code', 'in', partner_code_list)],
                ['code', 'name']
            )

        partner_dict = \
            dict((partner['code'], partner) for partner in partner_s)

        account_s = \
            self.env['account.account'].search_read(
                [('code', 'in', account_code_list)],
                ['code']
            )
        account_dict = \
            dict((account['code'], account['id']) for account in account_s)

        currency_s = \
            self.env['res.currency'].search_read(
                [('name', 'in', currency_list)],
                ['name']
            )
        currency_dict = \
            dict((currency['name'], currency['id']) for currency in
                 currency_s)

        return partner_dict, account_dict, currency_dict

    @api.multi
    def get_value_from_excel_row(self, row, row_num, partner_dict, account_dict, currency_dict):
        account_code = row[account_code_index]
        partner_code = row[partner_code_index]
        currency = row[currency_index]
        debit = row[debit_index]
        credit = row[credit_index]
        account = account_dict.get(account_code, False)
        if not account:
            raise UserError(
                _('Error: row {}: cannot find account with account code ="{}"'
                  ).format(row_num, account_code))

        partner = partner_dict.get(partner_code, False)
        if not partner:
            raise UserError(
                _('Error: row {}: cannot find supplier with supplier code ="{}"'
                  ).format(row_num, partner_code))
        partner_id = partner['id']
        ref = u'Công nợ NCC: {}; mã {}; tài khoản {}'.format(
            partner['name'], partner_code, account_code)
        currency_id = False
        if currency:
            currency_id = currency_dict.get(currency, False)
            if not currency_id:
                raise UserError(
                    _('Error: row {} currency invalid !').format(row_num))
        else:
            raise UserError(
                _('Error: row {} currency empty !').format(row_num))
        vals_debit = {
            'name': self.account_move_name,
            'journal_id': self.journal_id.id,
            'date': self.date
        }

        if self.voucher_day:
            vals_debit['x_voucher_day'] = self.voucher_day

        vals_debit['ref'] = ref
        vals_debit['line_ids'] = []
        values_if_debit = (0, 0, {
            'account_id': account,
            'partner_id': partner_id,
            'name': ref,
            'currency_id': currency_id,
            'debit': debit,
            'credit': 0.0,
        })
        vals_debit['line_ids'].append(values_if_debit)

        name_reciprocal = u'Trung gian: ' + ref
        debit_reciprocal_if_debit = 0.0
        credit_reciprocal_if_debit = debit
        values_reciprocal_if_debit = (0, 0, {
            'account_id': self.account_reciprocal.id,
            'name': name_reciprocal,
            'currency_id': currency_id,
            'debit': debit_reciprocal_if_debit,
            'credit': credit_reciprocal_if_debit,
        })
        vals_debit['line_ids'].append(values_reciprocal_if_debit)

        vals_credit = {
            'name': self.account_move_name,
            'journal_id': self.journal_id.id,
            'date': self.date
        }

        if self.voucher_day:
            vals_credit['x_voucher_day'] = self.voucher_day

        vals_credit['ref'] = ref
        vals_credit['line_ids'] = []
        values_if_credit = (0, 0, {
            'account_id': account,
            'partner_id': partner_id,
            'name': ref,
            'currency_id': currency_id,
            'debit': 0.0,
            'credit': credit,
        })
        vals_credit['line_ids'].append(values_if_credit)

        debit_reciprocal_if_credit = credit
        credit_reciprocal_if_credit = 0.0
        values_reciprocal_if_credit = (0, 0, {
            'account_id': self.account_reciprocal.id,
            'name': name_reciprocal,
            'currency_id': currency_id,
            'debit': debit_reciprocal_if_credit,
            'credit': credit_reciprocal_if_credit,
        })
        vals_credit['line_ids'].append(values_reciprocal_if_credit)

        return vals_debit, vals_credit

# Create record from values list
    @api.multi
    def create_record(self, value):
        self.env['account.move'].create(value)
        return True
