# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime,timedelta
import pytz


class ImportAccountAsset(models.TransientModel):
    _name = 'import.account.asset.asset'
    _inherits = {'ir.attachment': 'attachment_id'}
    _import_model_name = 'account.asset.asset'
    _import_date_format = '%d-%m-%Y'

    template_file_url = fields.Char(compute='_compute_template_file_url',
                                    default=lambda self:
                                    self.env['ir.config_parameter'].
                                    get_param('web.base.url') +
                                    '/btek_account_asset/static/import_template/'
                                    'import_account_asset_asset.xlsx')

    @api.multi
    def _compute_template_file_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        url = base_url + '/btek_account_asset/static/import_template/import_account_asset_asset.xlsx'
        for ip in self:
            ip.template_file_url = url

    def import_asset(self):
        content = self.get_value_from_excel_row()
        if content['atts_create']:
            for att in content['atts_create']:
                self.env['account.asset.asset'].create(att)
        return True

    @api.multi
    def get_value_from_excel_row(self):
        excel_data = self.env['read.excel'].read_file(data=self.datas, sheet="Sheet1", path=False)
        if excel_data:
            catg_data = {}
            atts_create = []
            row_count = 1
            for i in excel_data[1:]:
                row_count += 1
                if not i[0]:
                    raise UserError(_('Tên tài sản không thể để trống, Hàng %s - Cột A') % row_count)
                if not i[1]:
                    raise UserError(_('Loại tài sản không thể để trống, Hàng %s - Cột B') % row_count)
                if not i[2]:
                    raise UserError(_('Ngày bắt đầu tính KH không thể để trống, Hàng %s - Cột C') % row_count)

                if not i[6]:
                    raise UserError(_('Đơn vị tiền không thể để trống, Hàng %s - Cột D') % row_count)

                if not i[7]:
                    raise UserError(_('Giá trị nguyên giá không thể để trống, Hàng %s - Cột H') % row_count)

                if not i[10]:
                    raise UserError(_('Phương pháp tính khấu hao không thể để trống, Hàng %s - Cột K') % row_count)

                if not i[11]:
                    raise UserError(_('Số lần khấu hao không thể để trống, Hàng %s - Cột L') % row_count)

                if not i[12]:
                    raise UserError(_('Chu kỳ không thể để trống, Hàng %s - Cột M') % row_count)

                category_id = self.env['account.asset.category'].search([('name', '=', i[1].encode('utf-8').strip())])
                if not category_id:
                    raise UserError(_('Không tìm thấy Nhóm tài sản, Hàng %s - Cột B') % row_count)

                if type(i[2]) != unicode:
                    raise UserError(_('Định dạng nhập trường ngày không đúng, vui lòng nhập định dạng chuỗi như mẫu, Hàng %s - Cột C') % row_count)
                start_date_format = str(datetime.strptime(i[2], '%d/%m/%Y'))
                start_date = str(datetime.strptime(start_date_format, '%Y-%m-%d 00:00:00'))

                manu_date = ''
                if i[3]:
                    if type(i[3]) != unicode:
                        raise UserError(_('Định dạng nhập trường ngày không đúng, vui lòng nhập định dạng chuỗi như mẫu, Hàng %s - Cột D') % row_count)
                    manu_date_format = str(datetime.strptime(i[3], '%d/%m/%Y'))
                    manu_date = str(datetime.strptime(manu_date_format, '%Y-%m-%d 00:00:00'))

                country_id = self.env['res.country'].search([('name', '=', i[4].encode('utf-8').strip())])
                if i[4] and not country_id:
                    raise UserError(_('Không tìm thấy trường quốc gia, Hàng %s - Cột E') % row_count)

                purchase_date = ''
                if i[5]:
                    if type(i[5]) != unicode:
                        raise UserError(_(
                            'Định dạng nhập trường ngày không đúng, vui lòng nhập định dạng chuỗi như mẫu, Hàng %s - Cột D') % row_count)
                    purchase_date_format = str(datetime.strptime(i[5], '%d/%m/%Y'))
                    purchase_date = str(datetime.strptime(purchase_date_format, '%Y-%m-%d 00:00:00'))

                currency_id = self.env['res.currency'].search([('name', '=', i[6].encode('utf-8').strip())])
                if not currency_id:
                    raise UserError(_('Không tìm thấy trường đơn vị tiền tệ, Hàng %s - Cột G') % row_count)

                partner_id = self.env['res.partner'].search([('name', '=', i[9].encode('utf-8').strip())])
                if i[9] and not partner_id:
                    raise UserError(_('Không tìm thấy trường Nhà cung cấp, Hàng %s - Cột J') % row_count)

                method_1 = u'Đường thẳng'
                method_2 = u'Khấu hao giảm dần'

                method = ''
                if i[10].encode('utf-8').strip().lower() == method_1.encode('utf-8').strip().lower():
                    method = 'linear'
                elif i[10].encode('utf-8').strip().lower() == method_2.encode('utf-8').strip().lower():
                    method = 'degressive'

                atts_create.append({
                    'name': i[0],
                    'category_id': category_id.id,
                    'date': start_date,
                    'year_of_manufacture': manu_date,
                    'country_of_manufacture': country_id.id,
                    'purchase_date': purchase_date,
                    'currency_id': currency_id.id,
                    'value': i[7],
                    'salvage_value': i[8],
                    'partner_id': partner_id.id,
                    'method': method,
                    'method_number': int(i[11]),
                    'method_period': int(i[12])
                })
            catg_data['atts_create'] = atts_create
            return catg_data
