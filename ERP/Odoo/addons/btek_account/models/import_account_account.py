# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime


code_index = 0
name_index = 1
currency_index = 2
parent_code_index = 3
type_index = 4

MIN_COL_NUMBER = 5


class WizardImportAccountAccount(models.TransientModel):
    _name = 'wizard.import.account.account'
    _inherits = {'ir.attachment': 'attachment_id'}

    attachment_id = fields.Many2one(
        'ir.attachment', 'Attachment',
        required=True)
    template_file_url = fields.Char(compute='_compute_template_file_url',
                                    default=lambda self:
                                    self.env['ir.config_parameter'].
                                    get_param('web.base.url') +
                                    '/btek_account/static/import_template/'
                                    'import_account_account.xls')

    @api.multi
    def _compute_template_file_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        url = base_url + '/btek_account/static/import_template/import_account_account.xls'
        for ip in self:
            ip.template_file_url = url

    @api.multi
    def import_account_account(self):
        self = self.with_context(show_parent_account=True)
        # read excel file
        data = self.datas
        sheet = False

        user = self.env.user
        path = '/import_account_account_' \
               + user.login + '_' + str(
            self[0].id) + '_' + str(
            datetime.now()) + '.xls'
        path = path.replace(' ', '_')

        read_excel_obj = self.env['read.excel']
        excel_data = read_excel_obj.read_file(data, sheet, path)

        # check content excel data
        if len(excel_data) < 3:
            raise UserError(_('Error: Cannot import empty file!'))

        # delete header excel (2 first line in file)
        del excel_data[0]

        # check number column excel file
        if len(excel_data[1]) < MIN_COL_NUMBER:
            raise UserError(_(
                'Error: Format file incorrect, you must import file have at least {} column!').format(
                MIN_COL_NUMBER))

        # check format data in excell file(unicode, str, ...)
        self.verify_excel_data(excel_data)

        # Get db data dict for many2one, many2many field: dict with key = name,
        # value = ID db
        db_account_dict, type_dict, \
        currency_dict, code_excel_dict = \
            self.get_db_data(excel_data)

        # Get values list to create from excel data map with db data
        values_list = []

        row_num = 1
        for row in excel_data:
            row_num += 1
            values = self.get_value_from_excel_row(
                row, row_num, db_account_dict,
                type_dict, currency_dict
            )
            values_list.append(values)

        code_values_dict = dict((v['code'], v) for v in values_list)

        self.create_record(values_list, code_values_dict,
                           code_excel_dict, db_account_dict)

        return True

    @api.multi
    def verify_excel_data(self, excel_data):
        row_count = 1

        for row in excel_data:
            row_count += 1

            if not row[code_index]:
                raise UserError(
                    _('Error: row {} code invalid!').format(row_count))

            try:
                row[code_index] = unicode(row[code_index])
                if '.' in row[code_index]:
                    code_list = row[code_index].split('.')
                    if code_list:
                        row[code_index] = code_list[0]

            except:
                raise UserError(
                    _('Error: row {} code invalid!').format(row_count))

            if not row[name_index]:
                raise UserError(
                    _('Error: row {} name invalid!').format(row_count))

            try:
                row[name_index] = unicode(row[name_index])
            except:
                raise UserError(
                    _('Error: row {} name invalid!').format(row_count))

            if row[currency_index]:
                try:
                    row[currency_index] = unicode(row[currency_index])
                except:
                    raise UserError(
                        _('Error: row {} currency invalid!').format(row_count))

            if row[parent_code_index]:
                try:
                    row[parent_code_index] = unicode(row[parent_code_index])
                except:
                    raise UserError(
                        _('Error: row {} parent code invalid!').format(row_count))

            if not row[type_index]:
                raise UserError(
                    _('Error: row {} type blank!').format(row_count))

            try:
                row[type_index] = unicode(row[type_index])
            except:
                raise UserError(
                    _('Error: row {} type invalid!').format(row_count))

        return True

    @api.multi
    def get_db_data(self, excel_data):
        code_list = []
        code_excel_dict = {}

        for row in excel_data:
            code = row[code_index].strip()
            code_excel_dict[code] = row

            if code:
                code_list.append(code)

        account_s = \
            self.env['account.account'].search_read(
                [('code', 'in', code_list),
                 ('company_id', '=', self.env.user.company_id.id)],
                ['code']
            )

        db_account_dict = \
            dict((account['code'], account['id']) for account in account_s)

        type_s = \
            self.env['account.account.type'].search_read(
                [], ['name', 'type']
            )

        type_dict = \
            dict((t['name'], t) for t in type_s)

        currency_s = \
            self.env['res.currency'].search_read(
                [], ['name']
            )

        currency_dict = \
            dict((c['name'], c['id']) for c in currency_s)

        return db_account_dict, type_dict, currency_dict, code_excel_dict

    @api.multi
    def get_value_from_excel_row(
            self, row, row_num, db_account_dict,
            type_dict, currency_dict):

        type_name = row[type_index]
        type = type_dict.get(type_name, False)
        
        if not type:
            raise UserError(
                _('Error: row {} type invalid'.format(row_num)))

        type_id = type['id']
        reconcile = False
        if type['type'] in ('receivable', 'payable'):
            reconcile = True

        currency_name = row[currency_index]
        currency_id = False
        if currency_name:
            currency_id = currency_dict.get(currency_name, False)
            if not currency_id:
                raise UserError(
                    _('Error: row {} currency invalid'.format(row_num)))

        value = {
            'name': row[name_index],
            'code': row[code_index],
            'user_type_id': type_id,
            'reconcile': reconcile,
        }
        if currency_id:
            value['currency_id'] = currency_id

        return value

    def find_parent(self, value, code_values_dict,
                    code_excel_dict, db_account_dict):

        code = value['code']
        excel_row = code_excel_dict.get(code, False)
        if not excel_row:
            return False

        parent_code = excel_row[parent_code_index]
        parent_id = False
        if parent_code:
            parent_id = db_account_dict.get(parent_code, False)

            if parent_id:
                return parent_id
        parent_code = code
        while parent_code:
            parent_code = parent_code[0:len(parent_code)-1]
            parent_id = db_account_dict.get(parent_code, False)

            if parent_id:
                return parent_id

        return parent_id

    def create_record(self, values_list, code_values_dict,
                      code_excel_dict, db_account_dict):
        res = []
        for value in values_list:
            if value['code'] in db_account_dict.keys():
                continue

            parent_id = self.find_parent(value, code_values_dict,
                                         code_excel_dict, db_account_dict)
            value['parent_id'] = parent_id

            account = self.env['account.account'].create(value)
            db_account_dict[value['code']] = account.id
            res.append(account.id)

        return res

