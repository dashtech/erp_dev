# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime,timedelta
import pytz
import xlsxwriter
from copy import deepcopy
import tempfile
import os
import base64


min_col_number = 12
code_inx = 0
name_inx = 1
type_inx = 2
sup_code_inx = 3
categ_inx = 4
price_inx = 5
po_price_inx = 6
po_uom_inx = 7
so_uom_inx = 8
cus_tax_inx = 9
asset_categ_inx = 10
sup_tax_inx = 11

class ImportProduct(models.TransientModel):
    _name = 'import.product.template'
    _inherits = {'ir.attachment': 'attachment_id'}
    _import_model_name = 'product.product'
    _import_date_format = '%d-%m-%Y'

    template_file_url = fields.Char(compute='_compute_template_file_url',
                                    default=lambda self:
                                    self.env['ir.config_parameter'].
                                    get_param('web.base.url') +
                                    '/bave_import/static/import_template/'
                                    'du_lieu_VTHH.xlsx')
    error_file = fields.Binary(attachment=True)
    f_name = fields.Char()
    line_error = fields.Char()
    success = fields.Char(default=u'Nhập thành công!')

    @api.multi
    def _compute_template_file_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        url = base_url + '/bave_import/static/import_template/du_lieu_VTHH.xlsx'
        for ip in self:
            ip.template_file_url = url

    def import_product_template(self):
        content = self.get_value_from_excel()

        if content['import']:
            pre_datas = self.verify_excel_data(content['import'])
            if pre_datas['data_fail']:
                content['fail'] += pre_datas['data_fail']
            if pre_datas['datas']:
                self.create_record(pre_datas['datas'])
        if not content['fail']:
            action_obj = self.env.ref(
                'bave_import.import_product_success_action')
            action = action_obj.read([])[0]
            action['res_id'] = self.id
            return action
        self.line_error = u'Có {} dòng nhập vào không thành công'.format(len(content['fail']))
        return self.return_error_excel(header_row=content['header'], return_excel_data=content['fail'])

    @api.multi
    def get_value_from_excel(self):
        excel_data = self.env['read.excel'].read_file(data=self.datas, sheet="Sheet1", path=False)
        if len(excel_data) < 2:
            raise UserError(_(
                'Error: Format file incorrect, you must import file have at least 2 row!'))

        if len(excel_data[0]) < min_col_number:
            raise UserError(_(
                'Error: Format file incorrect, you must import file have at least {} column!').format(
                min_col_number))
        # delete header excel (2 first line in file)
        # del excel_data[0]
        if excel_data:
            datas = {}
            import_fails = []
            import_lst = []
            row_count = 1
            for i in excel_data[1:]:
                row_count += 1
                fail = u''
                if not i[0]:
                    fail += u'Thiếu mã VTHH; '
                else:
                    check_code = self.env['product.product'].search([('default_code','=',i[0])])
                    if len(check_code) > 0:
                        fail += u'Mã VTHH đã tồn tại'
                if not i[1]:
                    fail += u'Thiếu tên VTHH; '
                if not i[2]:
                    fail += u'Thiếu loại VTHH; '
                if not i[4]:
                    fail += u'Thiếu nhóm nội bộ; '
                if not i[7]:
                    fail += u'Thiếu đơn vị mua; '
                if not i[7]:
                    fail += u'Thiếu đơn vị bán; '

                if len(fail) > 0:
                    i.append(fail)
                    import_fails.append(i)
                else:
                    import_lst.append(i)
            header_row = deepcopy(excel_data[0])
            header_row.append(u'Lỗi')
            datas.update({'import': import_lst, 'fail': import_fails, 'header': header_row})
            return datas

    @api.multi
    def verify_excel_data(self, excel_data):
        def char_format(source):
            return unicode(row[index]).strip()

        def date_format(source):
            return datetime.strptime(unicode(row[index]).strip(), '%d/%m/%Y').strftime('%Y-%m-%d')

        def float_format(source):
            return float(source)

        def int_format(source):
            return int(source)

        row_count = 1
        verify_ = {}

        categ_check = {i.name.lower().encode('utf-8'): i.id for i in self.env['product.category'].search([])}
        uom_check = {i.name.lower().encode('utf-8'): i.id for i in self.env['product.uom'].search([('active','=',True)])}
        cus_tax_check = {i.name.lower().encode('utf-8'): i.id for i in self.env['account.tax'].search([
            ('type_tax_use','=','sale')])}
        sup_tax_check = {i.name.lower().encode('utf-8'): i.id for i in self.env['account.tax'].search(
            [('type_tax_use','=','purchase')])}
        asset_check = {i.name.lower().encode('utf-8'): i.id for i in self.env['account.asset.category'].search([])}

        verify_data = []
        verify_fail = []
        for row in excel_data:
            row_count += 1
            row_check = row
            text_error = u''

            for field_index in [
                (char_format, code_inx, _('Product code'), True),
                (char_format, name_inx, _('Product name'), True),
                (char_format, type_inx, _('Type'), True),
                (char_format, sup_code_inx, _('Supplier code'), False),
                (char_format, categ_inx, _('Category'), True),
                (float_format, price_inx, _('Price'), False),
                (float_format, po_price_inx, _('PO price'), False),
                (char_format, po_uom_inx, _('PO uom'), True),
                (char_format, so_uom_inx, _('SO uom'), True),
                (char_format, cus_tax_inx, _('Customer tax'), False),
                (char_format, asset_categ_inx, _('Asset category'), False),
                (char_format, sup_tax_inx, _('Supplier tax'), False)
            ]:
                format_fnct = field_index[0]
                index = field_index[1]
                label = field_index[2]
                required = field_index[3]

                if row[index]:
                    try:
                        row[index] = format_fnct(row[index])
                    except:
                        text_error + (u'Dữ liệu {} không chính xác; '.format(label))

            categ = False
            if row[4].lower().encode('utf-8') in categ_check.keys():
                    categ = categ_check[row[4].lower().encode('utf-8')]
            po_uom = False
            if row[7].lower().encode('utf-8') in uom_check.keys():
                po_uom = uom_check[row[7].lower().encode('utf-8')]
            so_uom = False
            if row[8].lower().encode('utf-8') in uom_check.keys():
                so_uom = uom_check[row[8].lower().encode('utf-8')]
            cus_tax = False
            if row[9] == '':
                cus_tax = [(6, 0, [])]
            elif row[9].find(',') == 0:
                cus_taxs = row[9].split(',')
                if len(cus_taxs[0]) > 3:
                    cus_taxs[0] = cus_taxs[0][-3:]
                tax_ids = [cus_tax_check[tax.lower().encode('utf-8')] for tax in cus_taxs if\
                           tax.lower().encode('utf-8') in cus_tax_check]
                cus_tax = [(6, 0, tax_ids)]
            elif row[9].lower().encode('utf-8') in cus_tax_check.keys():
                    tax_id = [cus_tax_check[row[9].lower().encode('utf-8')]]
                    cus_tax = [(6, 0, tax_id)]
            sup_tax = False
            if row[11] == '':
                sup_tax = [(6, 0, [])]
            elif row[11].find(',') == 0:
                sup_taxs = row[11].split(',')
                if len(cus_taxs[0]) > 3:
                    sup_taxs[0] = sup_taxs[0][-3:]
                tax_ids = [sup_tax_check[tax.lower().encode('utf-8')] for tax in sup_taxs if\
                           tax.lower().encode('utf-8') in sup_tax_check]
                sup_tax = [(6, 0, tax_ids)]
            elif row[11].lower().encode('utf-8') in sup_tax_check.keys():
                    tax_id = [sup_tax_check[row[11].lower().encode('utf-8')]]
                    sup_tax = [(6, 0, tax_id)]
            asset = False
            if row[10] == '':
                asset = ''
            elif row[10].lower().encode('utf-8') in asset_check.keys():
                asset = asset_check[row[10].lower().encode('utf-8')]
            type = False
            if row[2].lower() == u'dịch vụ':
                type = 'service'
            elif row[2].lower() == u'vt-hh có thể lưu trữ' \
                    or row[2].lower() == u'sản phẩm có thể lưu trữ'\
                    or row[2].lower() == u'vthh có thể lưu trữ':
                type = 'product'
            elif row[2].lower() == u'có thể tiêu thụ':
                type = 'consu'

            if categ is False:
                text_error += u'Nhóm nội bộ không có trên hệ thống; '
            if type is False:
                text_error += u'Loại VTHH không có trên hệ thống; '
            if po_uom is False:
                text_error += u'Đơn vị mua không có trên hệ thống; '
            if so_uom is False:
                text_error += u'Đơn vị bán không có trên hệ thống; '
            if sup_tax is False:
                text_error += u'Thuế NCC không có trên hệ thống; '
            if cus_tax is False:
                text_error += u'Thuế khách hàng không có trên hệ thống; '
            if asset is False:
                text_error += u'Nhóm tài sản không có trên hệ thống; '

            if len(text_error) > 0:
                row_check.append(text_error)
                verify_fail.append(row_check)
            else:
                verify_data.append({
                    'default_code': row[0],
                    'name': row[1],
                    'type': type,
                    'hs_code': row[3],
                    'categ_id': categ,
                    'lst_price': row[5],
                    'standard_price': row[6],
                    'uom_id': so_uom,
                    'uom_po_id': po_uom,
                    'taxes_id': cus_tax,
                    'supplier_taxes_id': sup_tax,
                    'asset_category_id': asset,
                })
        verify_.update({'datas': verify_data, 'data_fail': verify_fail})
        return verify_

    def create_record(self, value_list):
        res = []
        for value in value_list:
            product_id = self.env['product.product'].create(value)
            res.append(product_id)
        return res

    def return_error_excel(self, header_row, return_excel_data):
        filename = 'Nhap_du_lieu_loi.xlsx'
        temppath = tempfile.gettempdir()
        filepath = os.path.join(temppath, filename)
        workbook = xlsxwriter.Workbook(filepath)
        worksheet = workbook.add_worksheet()

        worksheet.set_column('A:A', 20)
        worksheet.set_column('B:B', 28)
        worksheet.set_column('C:C', 15)
        worksheet.set_column('D:D', 13)
        worksheet.set_column('E:E', 15)
        worksheet.set_column('F:F', 12)
        worksheet.set_column('G:G', 12)
        worksheet.set_column('H:H', 10)
        worksheet.set_column('I:I', 10)
        worksheet.set_column('J:J', 15)
        worksheet.set_column('K:K', 12)
        worksheet.set_column('L:L', 15)
        worksheet.set_column('M:M', 25)


        normal_normal = workbook.add_format({
            'valign': 'vcenter',
            'text_wrap': 0,
            'align': 'left',
            'font_name': 'Times New Roman',
            'num_format': '#,##0.00',
        })
        normal_number = workbook.add_format({
            'valign': 'vcenter',
            'align': 'right',
            'font_name': 'Times New Roman',
            'num_format': '#,##0.00',
        })

        normal_header = workbook.add_format({
            'bold': True,
            'valign': 'vcenter',
            'font': 'Times New Roman',
        })
        normal_header_required = workbook.add_format({
            'bold': True,
            'valign': 'vcenter',
            'font': 'Times New Roman',
            'color': 'red'
        })

        col = 0
        for header_item in header_row:
            if col in [0,1,2,4,7,8]:
                worksheet.write(0, col, header_item, normal_header_required)
            else:
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
            'error_file': encoded_string,
        }
        self.write(return_error_vals)
        action_obj = self.env.ref(
            'bave_import.import_product_failed_action')
        action = action_obj.read([])[0]
        action['res_id'] = self.id
        return action

    @api.model
    def create(self, vals):
        vals['f_name'] = 'du_lieu_loi.xlsx'
        return super(ImportProduct, self).create(vals)

    def ok_act(self):
        return

