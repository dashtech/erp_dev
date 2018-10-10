# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime,timedelta
import pytz


class ImportProductCategory(models.TransientModel):
    _name = 'import.product.category'
    _inherits = {'ir.attachment': 'attachment_id'}
    _import_model_name = 'product.category'
    _import_date_format = '%d-%m-%Y'

    template_file_url = fields.Char(compute='_compute_template_file_url',
                                    default=lambda self:
                                    self.env['ir.config_parameter'].
                                    get_param('web.base.url') +
                                    '/bave_import/static/import_template/'
                                    'import_product_category.xlsx')

    @api.multi
    def _compute_template_file_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        url = base_url + '/bave_import/static/import_template/import_product_category.xlsx'
        for ip in self:
            ip.template_file_url = url

    def import_product_category(self):
        content = self.get_value_from_excel_row()
        if content['atts_create']:
            for att in content['atts_create']:
                self.env['product.category'].create(att)
        return True

    @api.multi
    def get_value_from_excel_row(self):
        excel_data = self.env['read.excel'].read_file(data=self.datas, sheet="Sheet1", path=False)
        # delete header excel (2 first line in file)
        # del excel_data[0]
        categ_model = self.env['product.category']
        company_id = self.env.user.company_id.id
        if excel_data:
            catg_data = {}
            atts_create = []
            atts_write = []
            chenhlechgia_id = categ_model.default_get(['property_account_creditor_price_difference_categ'])['property_account_creditor_price_difference_categ']
            doanhthu_id = categ_model.default_get(['property_account_income_categ_id'])['property_account_income_categ_id']
            chiphi_id = categ_model.default_get(['property_account_expense_categ_id'])['property_account_expense_categ_id']
            nhapkho_id = categ_model.default_get(['property_stock_account_input_categ_id'])['property_stock_account_input_categ_id']
            xuatkho_id = categ_model.default_get(['property_stock_account_output_categ_id'])['property_stock_account_output_categ_id']
            tonkho_id = categ_model.default_get(['property_stock_valuation_account_id'])['property_stock_valuation_account_id']
            sonhatky_id = categ_model.default_get(['property_stock_journal'])['property_stock_journal']

            row_count = 1
            for i in excel_data[1:]:
                row_count += 1
                if not i[0]:
                    raise UserError(_('Category name can not empty, Row %s - Column A') % row_count)

                parent_catg_id = self.env['product.category'].sudo().search(
                    [('name', '=', i[1])])

                if i[1] and not parent_catg_id:
                    raise UserError(_('Parent Category can not empty, Row %s - Column B') % row_count)

                x_type_1 = u'Thông thường'
                x_type_2 = u'Xem'

                x_type = ''
                if i[2].encode('utf-8').strip().lower() == x_type_1.encode('utf-8').lower():
                    x_type = 'normal'
                if i[2].encode('utf-8').strip().lower() == x_type_2.encode('utf-8').lower():
                    x_type = 'view'

                property_cost_1 = u'Giá tiêu chuẩn'
                property_cost_2 = u'Giá trung bình'
                property_cost_3 = u'Giá thực tế'

                property_cost_method = ''
                if i[3].encode('utf-8').strip().lower() == property_cost_1.encode('utf-8').lower():
                    property_cost_method = 'standard'
                if i[3].encode('utf-8').strip().lower() == property_cost_2.encode('utf-8').lower():
                    property_cost_method = 'average'
                if i[3].encode('utf-8').strip().lower() == property_cost_3.encode('utf-8').lower():
                    property_cost_method = 'real'
                if property_cost_method is '':
                    raise UserError(_('Không tìm thấy trường Phương pháp tính giá vốn, Hàng %s - Cột D') % row_count)

                property_val_1 = u'Không sinh hạch toán'
                property_val_2 = u'Sinh hạch toán'

                property_valuation = ''
                if i[4].encode('utf-8').lower() == property_val_1.encode('utf-8').lower():
                    property_valuation = 'manual_periodic'
                if i[4].encode('utf-8').lower() == property_val_2.encode('utf-8').lower():
                    property_valuation = 'real_time'
                if property_valuation is '':
                    raise UserError(_('Không tìm thấy trường Tạo bút toán kho, Dòng %s - Cột E') % row_count)
                if type(i[5]) is float:
                    x_chenhlechgia_id = self.env['account.account'].with_context(show_parent_account=True).search(
                        [('code', '=', str(i[5]).split('.')[0].encode('utf-8')), ('company_id', '=', company_id)])
                    if not x_chenhlechgia_id:
                        raise UserError(_('Tài khoản chênh lệch giá không tồn tại! Dòng %s - Cột F') % row_count)
                    else:
                        chenhlechgia_id = x_chenhlechgia_id.id

                if type(i[5]) is unicode:
                    x_chenhlechgia_id = self.env['account.account'].with_context(show_parent_account=True).search(
                        [('code', '=', i[5].encode('utf-8').strip()), ('company_id', '=', company_id)])
                    if not x_chenhlechgia_id:
                        raise UserError(_('Tài khoản chênh lệch giá không tồn tại! Dòng %s - Cột F') % row_count)
                    else:
                        chenhlechgia_id = x_chenhlechgia_id.id

                if type(i[6]) is float:
                    x_doanhthu_id = self.env['account.account'].with_context(show_parent_account=True).search(
                            [('code', '=', str(i[6]).split('.')[0].encode('utf-8')), ('company_id', '=', company_id)])
                    if not x_doanhthu_id:
                        raise UserError(_('Tài khoản doanh thu không tồn tại ! Dòng %s - Cột G') % row_count)
                    else:
                        doanhthu_id = x_doanhthu_id.id

                if type(i[6]) is unicode:
                    x_doanhthu_id = self.env['account.account'].with_context(show_parent_account=True).search(
                        [('code', '=', i[6].encode('utf-8').strip()), ('company_id', '=', company_id)])
                    if not x_doanhthu_id:
                        raise UserError(_('Tài khoản doanh thu không tồn tại ! Dòng %s - Cột G') % row_count)
                    else:
                        doanhthu_id = x_doanhthu_id.id

                if type(i[7]) is float:
                    x_chiphi_id = self.env['account.account'].with_context(show_parent_account=True).search(
                        [('code', '=', str(i[7]).split('.')[0].encode('utf-8')), ('company_id', '=', company_id)])
                    if not x_chiphi_id:
                        raise UserError(_('Tài khoản chi phí không tồn tại ! Dòng %s - Cột H') % row_count)
                    else:
                        chiphi_id = x_chiphi_id.id

                if type(i[7]) is unicode:
                    x_chiphi_id = self.env['account.account'].with_context(show_parent_account=True).search(
                        [('code', '=', i[7].encode('utf-8').strip()), ('company_id', '=', company_id)])
                    if not x_chiphi_id:
                        raise UserError(_('Tài khoản chi phí không tồn tại ! Dòng %s - Cột H') % row_count)
                    else:
                        chiphi_id = x_chiphi_id.id

                if type(i[8]) is float:
                    x_nhapkho_id = self.env['account.account'].with_context(show_parent_account=True).search(
                        [('code', '=', str(i[8]).split('.')[0].encode('utf-8')), ('company_id', '=', company_id)])
                    if not x_nhapkho_id:
                        raise UserError(_('Tài khoản nhập kho không tồn tại ! Dòng %s - Cột I') % row_count)
                    else:
                        nhapkho_id = x_nhapkho_id.id

                if type(i[8]) is unicode:
                    x_nhapkho_id = self.env['account.account'].with_context(show_parent_account=True).search(
                        [('code', '=', i[8].encode('utf-8').strip()), ('company_id', '=', company_id)])
                    if not x_nhapkho_id:
                        raise UserError(_('Tài khoản nhập kho không tồn tại ! Dòng %s - Cột I') % row_count)
                    else:
                        nhapkho_id = x_nhapkho_id.id

                if type(i[9]) is float:
                    x_xuatkho_id = self.env['account.account'].with_context(show_parent_account=True).search(
                        [('code', '=', str(i[9]).split('.')[0].encode('utf-8')), ('company_id', '=', company_id)])
                    if not x_xuatkho_id:
                        raise UserError(_('Tài khoản xuất kho không tồn tại ! Dòng %s - Cột J') % row_count)
                    else:
                        xuatkho_id = x_xuatkho_id.id

                if type(i[9]) is unicode:
                    x_xuatkho_id = self.env['account.account'].with_context(show_parent_account=True).search(
                        [('code', '=', i[9].encode('utf-8').strip()), ('company_id', '=', company_id)])
                    if not x_xuatkho_id:
                        raise UserError(_('Tài khoản xuất kho không tồn tại ! Dòng %s - Cột J') % row_count)
                    else:
                        xuatkho_id = x_xuatkho_id.id

                if type(i[10]) is float:
                    x_tonkho_id = self.env['account.account'].with_context(show_parent_account=True).search(
                        [('code', '=', str(i[10]).split('.')[0].encode('utf-8')), ('company_id', '=', company_id)])
                    if not x_tonkho_id:
                        raise UserError(_('Tài khoản tồn kho không tồn tại ! Dòng %s - Cột K') % row_count)
                    else:
                        xuatkho_id = x_tonkho_id.id

                if type(i[10]) is unicode:
                    x_tonkho_id = self.env['account.account'].with_context(show_parent_account=True).search(
                        [('code', '=', i[10].encode('utf-8').strip()), ('company_id', '=', company_id)])
                    if not x_tonkho_id:
                        raise UserError(_('Tài khoản tồn kho không tồn tại ! Dòng %s - Cột K') % row_count)
                    else:
                        xuatkho_id = x_tonkho_id.id

                if type(i[11]) is unicode:
                    x_sonhatky_id = self.env['account.journal'].search(
                        [('name', '=', i[11].encode('utf-8').strip())])
                    if not x_sonhatky_id:
                        raise UserError(_('Sổ nhật ký không tồn tại ! Dòng %s - Cột L') % row_count)
                    else:
                        sonhatky_id = x_sonhatky_id.id

                atts_create.append({
                    'name': i[0],
                    'parent_id': parent_catg_id.id if parent_catg_id else False,
                    'type': x_type,
                    'property_cost_method': property_cost_method,
                    'property_valuation': property_valuation,
                    'property_account_creditor_price_difference_categ': chenhlechgia_id,
                    'property_account_income_categ_id': doanhthu_id,
                    'property_account_expense_categ_id': chiphi_id,
                    'property_stock_account_input_categ_id': nhapkho_id,
                    'property_stock_account_output_categ_id': xuatkho_id,
                    'property_stock_valuation_account_id': tonkho_id,
                    'property_stock_journal': sonhatky_id,
                })
            catg_data['atts_create'] = atts_create
            # catg_data['atts_write'] = atts_write
            return catg_data


