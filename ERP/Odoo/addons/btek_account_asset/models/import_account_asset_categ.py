# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime,timedelta
import pytz


class ImportAssetCategory(models.TransientModel):
    _name = 'import.account.asset.category'
    _inherits = {'ir.attachment': 'attachment_id'}
    _import_model_name = 'account.asset.category'
    _import_date_format = '%d-%m-%Y'

    template_file_url = fields.Char(compute='_compute_template_file_url',
                                    default=lambda self:
                                    self.env['ir.config_parameter'].
                                    get_param('web.base.url') +
                                    '/btek_account_asset/static/import_template/'
                                    'import_account_asset_categ.xlsx')

    @api.multi
    def _compute_template_file_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        url = base_url + '/btek_account_asset/static/import_template/import_account_asset_categ.xlsx'
        for ip in self:
            ip.template_file_url = url

    def import_asset_category(self):
        content = self.get_value_from_excel_row()
        if content['atts_create']:
            for att in content['atts_create']:
                self.env['account.asset.category'].create(att)
        return True

    @api.multi
    def get_value_from_excel_row(self):
        excel_data = self.env['read.excel'].read_file(data=self.datas, sheet="Sheet1", path=False)
        company_id = self.env.user.company_id.id
        if excel_data:
            catg_data = {}
            atts_create = []
            row_count = 1
            for i in excel_data[1:]:
                row_count += 1
                if not i[0]:
                    raise UserError(_('Nhóm tài sản không thể để trống, Hàng %s - Cột A') % row_count)
                if not i[1]:
                    raise UserError(_('Sổ nhật ký không thể để trống, Hàng %s - Cột B') % row_count)
                if not i[2]:
                    raise UserError(_('Tài khoản nguyên giá không thể để trống, Hàng %s - Cột C') % row_count)

                if not i[3]:
                    raise UserError(_('Bút toán KH: TK tài sản không thể để trống, Hàng %s - Cột D') % row_count)

                if not i[4]:
                    raise UserError(_('Bút toán KH: TK chi phí không thể để trống, Hàng %s - Cột E') % row_count)

                if not i[5]:
                    raise UserError(_('Phương thức khấu hao không thể để trống, Hàng %s - Cột F') % row_count)

                if not i[6]:
                    raise UserError(_('Số lần khấu hao không thể để trống, Hàng %s - Cột G') % row_count)

                if not i[7]:
                    raise UserError(_('Chu kỳ không thể để trống, Hàng %s - Cột H') % row_count)

                sonhatky = self.env['account.journal'].search([('name', '=', i[1].encode('utf-8').strip()),
                                                               ('company_id', '=', company_id)])
                if not sonhatky:
                    raise UserError(_('Không tìm thấy tên sổ nhật ký trong hệ thống, Hàng %s - Cột B') % row_count)

                tk_nguyengia = self.env['account.account'].search([('code', '=', int(i[2])),
                                                                   ('company_id', '=', company_id)])
                if not tk_nguyengia:
                    raise UserError(_('Không tìm thấy tài khoản nguyên giá, Hàng %s - Cột C') % row_count)
                tk_taisan = self.env['account.account'].search([('code', '=', int(i[3])),
                                                                ('company_id', '=', company_id)])
                if not tk_taisan:
                    raise UserError(_('Không tìm thấy Bút toán KH: TK tài sản, Hàng %s - Cột D') % row_count)
                tk_chiphi = self.env['account.account'].search([('code', '=', int(i[4])),
                                                                ('company_id', '=', company_id)])
                if not tk_chiphi:
                    raise UserError(_('Không tìm thấy Bút toán KH: TK chi phí, Hàng %s - Cột E') % row_count)

                x_type_1 = u'Số lần khấu hao'
                x_type_2 = u'Ngày kết thúc'

                method_time = ''
                if i[5].encode('utf-8').strip().lower() == x_type_1.encode('utf-8').strip().lower():
                    method_time = 'number'
                elif i[5].encode('utf-8').strip().lower() == x_type_2.encode('utf-8').strip().lower():
                    method_time = 'end'

                method_1 = u'Đường thẳng'
                method_2 = u'Khấu hao giảm dần'

                method = ''
                if i[8].encode('utf-8').strip().lower() == method_1.encode('utf-8').strip().lower():
                    method = 'linear'
                elif i[8].encode('utf-8').strip().lower() == method_2.encode('utf-8').strip().lower():
                    method = 'degressive'

                atts_create.append({
                    'name': i[0],
                    'journal_id': sonhatky.id,
                    'account_asset_id': tk_nguyengia.id,
                    'account_depreciation_id': tk_taisan.id,
                    'account_depreciation_expense_id': tk_chiphi.id,
                    'method_time': method_time,
                    'method': method,
                    'method_number': int(i[6]),
                    'method_period': int(i[7])
                })
            catg_data['atts_create'] = atts_create
            return catg_data
