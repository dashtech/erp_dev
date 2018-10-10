# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime,timedelta
import pytz


class ImportSupplier(models.TransientModel):
    _name = 'import.supplier'
    _inherits = {'ir.attachment': 'attachment_id'}
    _import_model_name = 'res.partner'
    _import_date_format = '%d-%m-%Y'

    template_file_url = fields.Char(compute='_compute_template_file_url',
                                    default=lambda self:
                                    self.env['ir.config_parameter'].
                                    get_param('web.base.url') +
                                    '/bave_import/static/import_template/'
                                    'import_supplier.xlsx')

    @api.multi
    def _compute_template_file_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        url = base_url + '/bave_import/static/import_template/import_supplier.xlsx'
        for ip in self:
            ip.template_file_url = url

    def import_supplier(self):
        content = self.get_value_from_excel_row()
        if content['atts_create']:
            for att in content['atts_create']:
                self.env['res.partner'].create(att)
        return True

    @api.multi
    def get_value_from_excel_row(self):
        excel_data = self.env['read.excel'].read_file(data=self.datas, sheet="Sheet1", path=False)
        partner_model = self.env['res.partner']
        company_id = self.env.user.company_id.id
        if excel_data:
            catg_data = {}
            atts_create = []
            row_count = 1
            for i in excel_data[1:]:
                row_count += 1
                if not i[1]:
                    raise UserError(_('Supplier name can not empty, Row %s - Column B') % row_count)
                if not i[2]:
                    raise UserError(_('Supplier code can not empty, Row %s - Column C') % row_count)
                exist_code = partner_model.sudo().search([('code', '=', i[2])])
                if exist_code:
                    raise UserError(_('Customer already exists, Row %s - Column C') % row_count)
                if not i[15]:
                    raise UserError(_('Receivable Account can not empty, Row %s - Column P') % row_count)

                if not i[16]:
                    raise UserError(_('Payable Account can not empty, Row %s - Column Q') % row_count)

                x_type_1 = u'Cá nhân'
                x_type_2 = u'Công ty'

                x_type = ''
                if i[0].encode('utf-8').strip().lower() == x_type_1.encode('utf-8').strip().lower():
                    x_type = 'person'
                elif i[0].encode('utf-8').strip().lower() == x_type_2.encode('utf-8').strip().lower():
                    x_type = 'company'

                if not x_type:
                    raise UserError(_('Type customer does not exists, Row %s - Column A') % row_count)

                country_id = self.env['res.country'].search([('name', '=', i[4].encode('utf-8').strip())])
                if i[4] and not country_id:
                    raise UserError(_('Không tìm thấy trường quốc gia, Hàng %s - Cột E') % row_count)
                state_id = self.env['res.country.state'].search([('name', '=', i[5].encode('utf-8').strip())])
                if i[5] and not state_id:
                    raise UserError(_('Không tìm thấy trường thành phố, Hàng %s - Cột F') % row_count)
                district_id = self.env['res.country.district'].search([('name', '=', i[6].encode('utf-8').strip())])
                if i[6] and not district_id:
                    raise UserError(_('Không tìm thấy trường Quận/Huyện, Hàng %s - Cột G') % row_count)
                ward_id = self.env['res.country.ward'].search([('name', '=', i[7].encode('utf-8').strip())])
                if i[7] and not ward_id:
                    raise UserError(_('Không tìm thấy trường Phường xã, Hàng %s - Cột G') % row_count)

                receivable_id = False
                payable_id = False

                if type(i[15]) is float:
                    x_receivable_id = self.env['account.account'].with_context(show_parent_account=True).search(
                        [('code', '=', str(i[15]).split('.')[0].encode('utf-8')), ('company_id', '=', company_id)])
                    if not x_receivable_id:
                        raise UserError(_('Receivable Account does not exists! Row %s - Column P') % row_count)
                    else:
                        receivable_id = x_receivable_id[0].id

                if type(i[15]) is unicode:
                    x_receivable_id = self.env['account.account'].with_context(show_parent_account=True).search(
                        [('code', '=', i[15].encode('utf-8')), ('company_id', '=', company_id)])
                    if not x_receivable_id:
                        raise UserError(_('Receivable Account does not exists! Dòng %s - Column P') % row_count)
                    else:
                        receivable_id = x_receivable_id[0].id

                if type(i[16]) is float:
                    x_payable_id = self.env['account.account'].with_context(show_parent_account=True).search(
                            [('code', '=', str(i[16]).split('.')[0].encode('utf-8')), ('company_id', '=', company_id)])
                    if not x_payable_id:
                        raise UserError(_('Payable Account does not exists! Row %s - Column Q') % row_count)
                    else:
                        payable_id = x_payable_id[0].id

                if type(i[16]) is unicode:
                    x_payable_id = self.env['account.account'].with_context(show_parent_account=True).search(
                        [('code', '=', i[16].encode('utf-8')), ('company_id', '=', company_id)])
                    if not x_payable_id:
                        raise UserError(_('Payable Account does not exists! Row %s - Column Q') % row_count)
                    else:
                        payable_id = x_payable_id[0].id

                x_sex_1 = u'Nam'
                x_sex_2 = u'Nữ'
                x_sex_3 = u'Khác'

                x_sex = ''
                if i[9].encode('utf-8').strip().lower() == x_sex_1.encode('utf-8').strip().lower():
                    x_sex = 'male'
                elif i[9].encode('utf-8').strip().lower() == x_sex_2.encode('utf-8').strip().lower():
                    x_sex = 'female'
                elif i[9].encode('utf-8').strip().lower() == x_sex_3.encode('utf-8').strip().lower():
                    x_sex = 'other'

                title = self.env['res.partner.title'].search([('name', '=', i[11].encode('utf-8').strip())])
                if i[11] and not title:
                    raise UserError(_('Không tìm thấy trường tiêu đề, Hàng %s - Cột L') % row_count)

                if type(i[10]) != unicode:
                    raise UserError(_('Định dạng nhập trường ngày không đúng, vui lòng nhập định dạng chuỗi như mẫu, Hàng %s - Cột K') % row_count)
                check_birth = ''
                if i[10]:
                    date_birth = str(datetime.strptime(i[10], '%d/%m/%Y'))
                    check_birth = str(datetime.strptime(date_birth, '%Y-%m-%d 00:00:00'))

                atts_create.append({
                    'company_type': x_type,
                    'name': i[1],
                    'code': i[2],
                    'vat': i[8],
                    'street': i[3],
                    'district_id': district_id.id if district_id else False,
                    'country_id': country_id.id if country_id else False,
                    'state_id': state_id.id if state_id else False,
                    'ward_id': ward_id.id if ward_id else False,
                    'sex': x_sex,
                    'date_of_birth': check_birth,
                    'title': title.id,
                    'comment': i[12],
                    'property_account_receivable_id': receivable_id,
                    'property_account_payable_id': payable_id,
                    'phone': i[13],
                    'email': i[14],
                    'supplier': True,
                    'customer': False
                })
            catg_data['atts_create'] = atts_create
            return catg_data
