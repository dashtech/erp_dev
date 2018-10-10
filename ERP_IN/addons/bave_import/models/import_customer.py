# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime,timedelta
import pytz
from validate_email import validate_email
from copy import deepcopy
import xlsxwriter
import base64
import os
import tempfile

partner_type_index = 0
name_index = 1
code_index = 2
street_index = 3
country_index = 4
state_index = 5
district_index = 6
ward_index = 7
vat_index = 8
sex_index = 9
date_of_birth_index = 10
title_index = 11
comment_index = 12
phone_index = 13
mobile_index = 14
email_index = 15
account_receivable_index = 16
account_payable_index = 17
group_user_index = 18
insurance_index = 19
source_melee_index = 20

MIN_COL_NUMBER = 21


class ImportResPartner(models.TransientModel):
    _name = 'import.customer'
    _inherits = {'ir.attachment': 'attachment_id'}
    _import_model_name = 'res.partner'
    _import_date_format = '%d-%m-%Y'

    attachment_id = fields.Many2one('ir.attachment', 'Attachment', required=True)

    template_file_url = fields.Char(compute='_compute_template_file_url',
                                    default=lambda self:
                                    self.env['ir.config_parameter'].
                                    get_param('web.base.url') +
                                    '/bave_import/static/import_template/'
                                    'import_customer.xlsx')

    f_name = fields.Char()
    return_error_file = fields.Binary(attachment=True)

    @api.model
    def create(self, vals):
        vals['f_name'] = _('Return_error_customer.xlsx')
        return super(ImportResPartner, self).create(vals)

    @api.multi
    def _compute_template_file_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        url = base_url + '/bave_import/static/import_template/import_customer.xlsx'
        for ip in self:
            ip.template_file_url = url

    def format_name(self, name):
        if not name:
            return name
        return name.strip().lower()

    def date_format(self, source):
        date_birth = str(datetime.strptime(source, '%d/%m/%Y'))
        birth_of_date = str(datetime.strptime(date_birth, '%Y-%m-%d 00:00:00'))
        return birth_of_date

    @api.multi
    def import_customer(self):
        # read excel file
        data = self.datas
        sheet = False

        user = self.env.user
        path = '/import_customer_' \
               + user.login + '_' + str(
            self[0].id) + '_' + str(
            datetime.now()) + '.xlsx'
        path = path.replace(' ', '_')

        read_excel_obj = self.env['read.excel']
        excel_data = read_excel_obj.read_file(data, sheet, path)

        # check content excel data
        if len(excel_data) < 2:
            raise UserError(_('Error: Cannot import empty file!'))

        header_row = deepcopy(excel_data[0])
        header_row.append(_('Error description'))
        excel_data_copy = deepcopy(excel_data)
        return_excel_data = []

        # delete header excel (first line in file)
        del excel_data[0]

        # check number column excel file
        if len(excel_data[0]) < MIN_COL_NUMBER:
            raise UserError(_(
                'Error: Format file incorrect, you must import file have at least {} column!').format(
                MIN_COL_NUMBER))

        # check format data in excell file(unicode, str, ...)
        error_dict = self.verify_excel_data(excel_data)

        # Get db data dict for many2one, many2many field: dict with key = name,
        # value = ID db

        partner_code_s, mobile_s, partner_type_dict, sex_dict, \
        insurance_dict, country_dict, state_dict, district_dict, \
        ward_dict, title_dict, account_code_dict, partner_group_dict, \
        partner_source_dict = self.get_db_data(excel_data)

        value_list = []
        index = 1
        for row in excel_data:
            index += 1

            if error_dict.get(str(index), False):
                error_row = deepcopy(row)
                error_item = error_dict.get(str(index))
                error_text = u','.join([u'{}:{}'.format(e, error_item[e]) for e in error_item.keys()])
                error_row.append(error_text)
                return_excel_data.append(error_row)
                continue

            value = self.get_value_from_excel_data(row, index, partner_code_s, mobile_s
                                                   , partner_type_dict, sex_dict
                                                   , insurance_dict, country_dict
                                                   , state_dict, district_dict
                                                   , ward_dict, title_dict
                                                   , account_code_dict, partner_group_dict
                                                   , partner_source_dict, error_dict)

            if error_dict.get(str(index), False):
                error_row = deepcopy(row)
                error_item = error_dict.get(str(index))
                error_text = u','.join(
                    [u'{}:{}'.format(e, error_item[e]) for e in
                     error_item.keys()])
                error_row.append(error_text)
                return_excel_data.append(error_row)
                continue

            value_list.append(value)

        res = self.create_record(value_list)

        if return_excel_data:
            return self.return_error_excel(header_row, return_excel_data)

        return res

    def process_error(self, row_count, error_text, label, error_dict):
        if not error_dict.get(str(row_count), False):
            error_dict[str(row_count)] = {}
        error_text = u'{},{}'.format(error_dict[str(row_count)].get(label, ''), error_text)
        error_dict[str(row_count)][label] = error_text

    @api.multi
    def verify_excel_data(self, excel_data):

        def char_format(source):
            return unicode(source).strip()

        def float_format(source):
            return float(source)

        def int_format(source):
            return int(source)

        # def date_format(source):
        #     date_birth = str(datetime.strptime(source, '%d/%m/%Y'))
        #     birth_of_date = str(datetime.strptime(date_birth, '%Y-%m-%d 00:00:00'))
        #     return birth_of_date

        def mail_format(source):
            if validate_email(source):
                return source
            raise

        def char_format_float(source):
            return unicode(source).strip().replace('.0', '')

        error_dict = {}
        partner_code_list = []
        mobile_list = []

        row_count = 1

        for row in excel_data:
            row_count += 1

            for field_index in [(char_format, partner_type_index, _('customer type'), True),
                                (char_format, name_index , _('customer name'), True),
                                (char_format, code_index, _('customer code'), True),
                                (char_format, street_index, _('street'), False),
                                (char_format, country_index, _('country'), False),
                                (char_format, state_index, _('state'), False),
                                (char_format, district_index, _('district'), False),
                                (char_format, ward_index, _('ward'), False),
                                (char_format_float, vat_index, _('vat'), False),
                                (char_format, sex_index, _('sex'), False),
                                (char_format, date_of_birth_index, _('Birthday'), False),
                                (char_format, title_index, _('Title'), False),
                                (char_format, comment_index, _('Comment'),False),
                                (char_format, phone_index, _('phone'), False),
                                (char_format, mobile_index, _('mobile'), False),
                                (char_format, email_index, _('email'), False),
                                (char_format_float, account_receivable_index, _('account receivable'), True),
                                (char_format_float, account_payable_index, _('account payable'), True),
                                (char_format, group_user_index, _('group customer'), False),
                                (char_format, insurance_index, _('insurance'), False),
                                (char_format, source_melee_index, _('source melee'), False),
                                ]:
                format_fnct = field_index[0]
                index = field_index[1]
                label = field_index[2]
                required = field_index[3]

                if required and not row[index]:
                    error_text = _('Error: row {} {} is blank!').format(
                            row_count, label
                        )
                    self.process_error(
                        row_count, error_text, label, error_dict)

                if row[index]:
                    try:
                        row[index] = format_fnct(row[index])
                    except:
                        error_text = _('Error: row {} {} invalid!').format(row_count, label)
                        self.process_error(row_count, error_text, label, error_dict)

            if row[code_index] in partner_code_list:
                error_text = _(
                    u'Error: Partner code {} in row {} exist on other row'
                    ).format(row[code_index], row_count)
                self.process_error(
                    row_count, error_text, label, error_dict)
            partner_code_list.append(row[code_index])
            if row[mobile_index]:
                if row[mobile_index] in mobile_list:
                    error_text = _(
                        u'Error: Mobile {} in row {} exist on other row'
                        ).format(row[mobile_index], row_count)
                    self.process_error(
                        row_count, error_text, label, error_dict)
                mobile_list.append(row[mobile_index])

        return error_dict


    @api.multi
    def get_db_data(self, excel_data):
        partner_code_list = []
        mobile_list = []
        # country_name_list = []
        # state_name_list = []
        # district_name_list = []
        # ward_name_list = []
        # title_name_list = []
        # account_code_list = []
        partner_group_list = []
        partner_source_list = []

        country_dict = {}
        state_dict = {}
        district_dict = {}
        ward_dict = {}

        for row in excel_data:
            partner_code = row[code_index].strip()
            partner_code_list.append(partner_code)

            mobile = row[mobile_index].strip()
            mobile_list.append(mobile)

            domain_state = []
            domain_district = []
            domain_ward = []

            if row[country_index]:
                country_list = self.env['res.country'].search_read([('name', 'ilike', self.format_name(row[country_index]))], ['name'])
                if country_list:
                    country_dict[self.format_name(row[country_index])] = country_list[0]['id']
                    domain_state.append(('country_id', '=', country_list[0]['id']))

            if row[state_index]:
                domain_state.append(('name', 'ilike', self.format_name(row[state_index])))
                state_list = self.env['res.country.state'].search_read(domain_state, ['name'])
                if state_list:
                    state_dict[self.format_name(row[state_index])] = state_list[0]['id']
                    domain_district.append(('state_id', '=', state_list[0]['id']))

            if row[district_index]:
                domain_district.append(('name', 'ilike', self.format_name(row[district_index])))
                district_list = self.env['res.country.district'].search_read(domain_district, ['name'])
                if district_list:
                    district_dict[self.format_name(row[district_index])] = district_list[0]['id']
                    domain_ward.append(('district_id', '=', district_list[0]['id']))

            if row[ward_index]:
                domain_ward.append(('name', 'ilike', self.format_name(row[ward_index])))
                ward_list = self.env['res.country.ward'].search_read(domain_ward, ['name'])
                if ward_list:
                    ward_dict[self.format_name(row[ward_index])] = ward_list[0]['id']

            # country_name = self.format_name(row[country_index])
            # country_name_list.append(country_name)
            #
            # state_name = self.format_name(row[state_index])
            # state_name_list.append(state_name)
            #
            # state_name = self.format_name(row[state_index])
            # state_name_list.append(state_name)
            #
            # district_name = self.format_name(row[district_index])
            # district_name_list.append(district_name)
            #
            # ward_name = self.format_name(row[ward_index])
            # ward_name_list.append(ward_name)

            # title_name = self.format_name(row[title_index])
            # title_name_list.append(title_name)
            #
            # account_receivable_code = row[account_receivable_index]
            # account_code_list.append(account_receivable_code)
            # account_payable_code = row[account_payable_index]
            # account_code_list.append(account_payable_code)

            partner_group_name = self.format_name(row[group_user_index])
            partner_group_list.append(partner_group_name)

            partner_source_name = self.format_name(row[source_melee_index])
            partner_source_list.append(partner_source_name)

        # country_name_list = list(set(country_name_list))
        # state_name_list = list(set(state_name_list))
        # district_name_list = list(set(district_name_list))
        # ward_name_list = list(set(ward_name_list))
        # title_name_list = list(set(title_name_list))
        # account_code_list = list(set(account_code_list))
        partner_group_list = list(set(partner_group_list))
        partner_source_list = list(set(partner_source_list))

        partner_code_db = \
            self.env['res.partner'].search_read(
                [('code', 'in', partner_code_list)],
                ['code']
            )

        partner_code_s = [partner_code['code'] for partner_code in partner_code_db]

        mobile_db = self.env['res.partner'].search_read(
                [('mobile', 'in', mobile_list)],
                ['mobile']
            )

        mobile_s = [partner_code['mobile'] for partner_code in mobile_db]

        partner_type_dict = {u'công ty': 'company', u'cá nhân': 'person'}

        sex_dict = {u'nam': 'male', u'nữ': 'female', u'không xác định': 'other'}

        insurance_dict = {u'có': 'yes', u'không': 'no'}

        # country_name_where = u"','".join(country_name_list)
        #
        # query_country = u"""
        #             select id, name from res_country
        #             where trim(lower(name)) in ('{}')
        #         """.format(country_name_where)
        # self.env.cr.execute(query_country)
        #
        # country_dict = {}
        #
        # for c in self.env.cr.dictfetchall():
        #     country_name = self.format_name(c['name'])
        #     country_dict[country_name] = c['id']
        #
        # state_name_where = u"','".join(state_name_list)
        # query_state = u"""
        #                     select id, name from res_country_state
        #                     where trim(lower(name)) in ('{}')
        #                 """.format(state_name_where)
        # self.env.cr.execute(query_state)
        #
        # state_dict = {}
        # for s in self.env.cr.dictfetchall():
        #     state_name = self.format_name(s['name'])
        #     state_dict[state_name] = s['id']
        #
        # district_name_where = u"','".join(district_name_list)
        # query_district = u"""
        #                         select id, name from res_country_district
        #                         where trim(lower(name)) in ('{}')
        #                     """.format(district_name_where)
        # self.env.cr.execute(query_district)
        #
        # district_dict = {}
        # for d in self.env.cr.dictfetchall():
        #     district_name = self.format_name(d['name'])
        #     district_dict[district_name] = d['id']
        #
        # ward_name_where = u"','".join(ward_name_list)
        # query_ward = u"""
        #                         select id, name from res_country_ward
        #                         where trim(lower(name)) in ('{}')
        #                     """.format(ward_name_where)
        # self.env.cr.execute(query_ward)
        #
        # ward_dict = {}
        # for w in self.env.cr.dictfetchall():
        #     ward_name = self.format_name(w['name'])
        #     ward_dict[ward_name] = w['id']
        #
        # title_name_where = u"','".join(title_name_list)
        # query_title = u"""
        #                     select id, name from res_partner_title
        #                     where trim(lower(name)) in ('{}')
        #                 """.format(title_name_where)
        # self.env.cr.execute(query_title)
        #
        # title_dict = {}
        # for t in self.env.cr.dictfetchall():
        #     title_name = self.format_name(t['name'])
        #     title_dict[title_name] = t['id']

        # country_list = self.env['res.country'].search_read([], ['name'])
        # country_dict = {}
        # for country in country_list:
        #     country_dict[self.format_name(country['name'])] = country['id']
        #
        # state_list = self.env['res.country.state'].search_read([], ['name'])
        # state_dict = {}
        # for state in state_list:
        #     state_dict[self.format_name(state['name'])] = state['id']
        #
        # district_list = self.env['res.country.district'].search_read([], ['name'])
        # district_dict = {}
        # for district in district_list:
        #     state_dict[self.format_name(district['name'])] = district['id']
        #
        # ward_list = self.env['res.country.ward'].search_read([], ['name'])
        # ward_dict = {}
        # for ward in ward_list:
        #     ward_dict[self.format_name(ward['name'])] = ward['id']

        title_list = self.env['res.partner.title'].search_read([], ['name'])
        title_dict = {}
        for title in title_list:
            title_dict[self.format_name(title['name'])] = title['id']

        account_code_list = self.env['account.account'].search_read([], ['code'])
        account_code_dict = {}
        for account_code in account_code_list:
            account_code_dict[unicode(account_code['code'])] = account_code['id']

        partner_group_name_where = u"','".join(partner_group_list)
        query_partner_group = u"""
                                    select id, name from btek_partner_group
                                    where trim(lower(name)) in ('{}')
                                """.format(partner_group_name_where)
        self.env.cr.execute(query_partner_group)

        partner_group_dict = {}
        for g in self.env.cr.dictfetchall():
            partner_group_name = self.format_name(g['name'])
            partner_group_dict[partner_group_name] = g['id']

        partner_source_name_where = u"','".join(partner_source_list)
        query_partner_source = u"""
                                    select id, name from btek_partner_source
                                    where trim(lower(name)) in ('{}')
                                """.format(partner_source_name_where)
        self.env.cr.execute(query_partner_source)

        partner_source_dict = {}
        for s in self.env.cr.dictfetchall():
            partner_source_name = self.format_name(s['name'])
            partner_source_dict[partner_source_name] = s['id']

        return partner_code_s, mobile_s, partner_type_dict, sex_dict, insurance_dict\
            , country_dict, state_dict, district_dict, ward_dict, title_dict\
            , account_code_dict, partner_group_dict, partner_source_dict

    def get_value_from_excel_data(self, row, index, partner_code_s, mobile_s,
                                  partner_type_dict, sex_dict,
                                  insurance_dict, country_dict,
                                  state_dict, district_dict, ward_dict,
                                  title_dict, account_code_dict,
                                  partner_group_dict, partner_source_dict, error_dict):

        partner_code = row[code_index].strip()

        if partner_code in partner_code_s:
            error_text = _(
                u'Error: Partner code {} already exist!'
            ).format(partner_code)
            self.process_error(
                index, error_text, _('customer code'), error_dict)

        if row[mobile_index]:
            mobile = row[mobile_index].strip()

            if mobile in mobile_s:
                error_text = _(
                    u'Error: Mobile {} already exist!'
                ).format(mobile)
                self.process_error(
                    index, error_text, _('mobile'), error_dict)

        value = {
            'name': row[name_index],
            'code': row[code_index],
            'street': row[street_index] or False,
            'vat': row[vat_index].replace('.0', '') or False,
            # 'date_of_birth': self.date_format(row[date_of_birth_index]) or False,
            'comment': row[comment_index] or False,
            'phone': row[phone_index] or False,
            'mobile': row[mobile_index] or False,
            'email': row[email_index] or False,
        }

        if row[date_of_birth_index]:
            date_of_birth = self.date_format(row[date_of_birth_index])
            value['date_of_birth'] = date_of_birth

        company_type = partner_type_dict.get(self.format_name(row[partner_type_index]), False)
        if not company_type:
            error_text = _('Error: Cannot find customer type {} in row {}'
                           ).format(row[partner_type_index], index)
            self.process_error(
                index, error_text, _('customer type'), error_dict)
        value['company_type'] = company_type

        if row[country_index]:
            country_id = country_dict.get(self.format_name(row[country_index]), False)
            if not country_id:
                error_text = _('Error: Cannot find country {} in row {}'
                               ).format(row[country_index], index)
                self.process_error(
                    index, error_text, _('country'), error_dict)
            value['country_id'] = country_id

        if row[state_index]:
            state_id = state_dict.get(self.format_name(row[state_index]), False)
            if not state_id:
                error_text = _('Error: Cannot find state {} in row {}'
                               ).format(row[state_index], index)
                self.process_error(
                    index, error_text, _('state'), error_dict)
            value['state_id'] = state_id

        if row[district_index]:
            district_id = district_dict.get(self.format_name(row[district_index]), False)
            if not district_id:
                error_text = _('Error: Cannot find district {} in row {}'
                               ).format(row[district_index], index)
                self.process_error(
                    index, error_text, _('district'), error_dict)
            value['district_id'] = district_id

        if row[ward_index]:
            ward_id = ward_dict.get(self.format_name(row[ward_index]), False)
            if not ward_id:
                error_text = _('Error: Cannot find ward {} in row {}'
                               ).format(row[ward_index], index)
                self.process_error(
                    index, error_text, _('ward'), error_dict)
            value['ward_id'] = ward_id

        if row[sex_index]:
            sex = sex_dict.get(self.format_name(row[sex_index]), False)
            if not sex:
                error_text = _('Error: Cannot find sex {} in row {}'
                               ).format(row[sex_index], index)
                self.process_error(
                    index, error_text, _('sex'), error_dict)
            value['sex'] = sex

        if row[title_index]:
            title = title_dict.get(self.format_name(row[title_index]), False)
            if not title:
                error_text = _('Error: Cannot find title {} in row {}'
                               ).format(row[title_index], index)
                self.process_error(
                    index, error_text, _('Title'), error_dict)
            value['title'] = title

        property_account_receivable_id = account_code_dict.get(row[account_receivable_index], False)
        if not property_account_receivable_id:
            error_text = _('Error: Cannot find account code {} in row {}'
                           ).format(row[account_receivable_index].replace('.0', ''), index)
            self.process_error(
                index, error_text, _('account receivable'), error_dict)
        value['property_account_receivable_id'] = property_account_receivable_id

        property_account_payable_id = account_code_dict.get(row[account_payable_index], False)
        if not property_account_payable_id:
            error_text = _('Error: Cannot find account code {} in row {}'
                           ).format(row[account_payable_index].replace('.0', ''), index)
            self.process_error(
                index, error_text, _('account payable'), error_dict)
        value['property_account_payable_id'] = property_account_payable_id

        if row[group_user_index]:
            group_user = partner_group_dict.get(self.format_name(row[group_user_index]), False)
            if not group_user:
                error_text = _('Error: Cannot find group customer {} in row {}'
                               ).format(row[group_user_index], index)
                self.process_error(
                    index, error_text, _('group customer'), error_dict)
            value['group_user'] = group_user

        if row[insurance_index]:
            insurance_status = insurance_dict.get(self.format_name(row[insurance_index]), False)
            if not insurance_status:
                error_text = _('Error: Cannot find insurance status {} in row {}'
                               ).format(row[insurance_index], index)
                self.process_error(
                    index, error_text, _('insurance'), error_dict)
            value['insurance_status'] = insurance_status

        if row[source_melee_index]:
            source_melee = partner_source_dict.get(self.format_name(row[source_melee_index]), False)
            if not insurance_status:
                error_text = _('Error: Cannot find source melee {} in row {}'
                               ).format(row[source_melee_index], index)
                self.process_error(
                    index, error_text, _('source melee'), error_dict)
            value['source_melee'] = source_melee

        return value

    def create_record(self, value_list):
        res = []
        for value in value_list:
            partner_id = self.env['res.partner'].create(value)
            res.append(partner_id)
        return res

    def return_error_excel(self, header_row, return_excel_data):
        filename = 'return_error_customer_' \
               + self.env.user.login + '_' + str(
            self[0].id) + '_' + str(
            datetime.now())
        filename = filename.replace(' ', '_')
        filename = filename.replace(':', '_')
        filename = filename.replace('.', '_') + '.xlsx'
        temppath = tempfile.gettempdir()
        filepath = os.path.join(temppath, filename)

        workbook = xlsxwriter.Workbook(filepath)
        worksheet = workbook.add_worksheet()

        worksheet.set_column('A:A', 15)
        worksheet.set_column('B:B', 25)
        worksheet.set_column('C:C', 18)
        worksheet.set_column('D:D', 25)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 15)
        worksheet.set_column('G:G', 15)
        worksheet.set_column('H:H', 15)
        worksheet.set_column('I:I', 15)
        worksheet.set_column('J:J', 10)
        worksheet.set_column('K:K', 10)
        worksheet.set_column('L:L', 10)
        worksheet.set_column('M:M', 25)
        worksheet.set_column('N:N', 15)
        worksheet.set_column('O:O', 15)
        worksheet.set_column('P:P', 25)
        worksheet.set_column('Q:Q', 15)
        worksheet.set_column('R:R', 15)
        worksheet.set_column('S:S', 15)
        worksheet.set_column('T:T', 20)
        worksheet.set_column('U:U', 15)
        worksheet.set_column('V:V', 50)

        normal_normal = workbook.add_format(
            {
                'valign': 'vcenter',
                # 'num_format': '#,##0',
            }
        )
        normal_normal.set_font_name('Times New Roman')
        normal_normal.set_text_wrap()
        normal_normal.set_top()
        normal_normal.set_bottom()
        normal_normal.set_left()
        normal_normal.set_right()
        # normal_normal.set_format('text')

        normal_header = workbook.add_format(
            {
                'bold': True,
                'valign': 'vcenter',
                # 'num_format': '#,##0',
            }
        )
        normal_header.set_font_name('Times New Roman')
        normal_header.set_align('center')
        normal_header.set_text_wrap()
        normal_header.set_top()
        normal_header.set_bottom()
        normal_header.set_left()
        normal_header.set_right()
        normal_header.set_fg_color('#99CCFF')

        col = 0
        for header_item in header_row:
            worksheet.write(0, col, header_item, normal_header)
            col += 1

        row_index = 1
        for row in return_excel_data:
            col = 0
            for item in row:
                worksheet.write(row_index, col, item, normal_normal)
                col += 1
            row_index += 1

        workbook.close()

        f = open(filepath, "rb")
        encoded_string = base64.b64encode(f.read())
        f.close()

        return_error_vals = {
            'return_error_file': encoded_string,
        }
        self.write(return_error_vals)

        action_obj = self.env.ref('bave_import.wizard_import_customer_return_error_form_view_action')
        action = action_obj.read([])[0]
        action['res_id'] = self.id
        return action

