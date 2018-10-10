#!/usr/bin/python
# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
import datetime
import xlrd
import xlwt
import xlsxwriter
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx

group_user_index = 17
min_col_number = 3
class btek_res_partner(models.Model):
    _inherit = 'res.partner'

    @api.one
    def _get_last_day(self):
        self.last_day_of_sale = self.env['sale.order'].search([('partner_id', '=', self.id)], order='create_date desc',
                                                              limit=1).confirmation_date
        self.write({'relate_lastday': self.last_day_of_sale})

    date_of_birth = fields.Date(string=_('Ngày sinh'))
    birth_day = fields.Char(compute='_compute_birth_day', store=True)
    sex = fields.Selection([('male', _('Nam')), ('female', 'Nữ'), ('other', 'Other')], string=_('Giới tính'))
    source_melee = fields.Many2one('btek.partner.source', string=_('Nguồn tiếp cận'))
    # group_user = fields.Many2one('btek.partner.group', string='Nhóm quản lý')
    insurance_status = fields.Selection([('yes', _('Có')), ('no', _('Không'))], string=_('Tình trạng mua bảo hiểm'))
    date_insurance = fields.Date(string=_('Ngày hết hạn bảo hiểm'))
    last_day_of_sale = fields.Date(string=_('Ngày mua hàng(S0) gần nhất'), compute=_get_last_day)
    relate_lastday = fields.Date(string=_('Relate Lastday SO'))
    # sale_person = fields.Char(string=_('Người bán hàng'))
    zalo_id = fields.Char(string='Zalo ID', readonly=True)
    facebook_id = fields.Char(string='Facebook ID', readonly=True)
    viber_id = fields.Char(string='Viber ID', readonly=True)
    is_invite_zalo = fields.Boolean(default=False)
    member_id = fields.Char(string='Member ID', readonly=True)

    btek_function_id = fields.Many2one('btek.function', string=_('Vị trí công tác'))

    btek_career_id = fields.Many2one('btek.career', string=_('Ngành/Dịch vụ'))

    @api.onchange('zalo_id')
    def _change_is_invite_zalo(self):
        if self.zalo_id:
            self.is_invite_zalo = True

    @api.multi
    @api.depends('date_of_birth')
    def _compute_birth_day(self):
        for s in self:
            if s.date_of_birth:
                s.birth_day = s.date_of_birth[5:]

class Customer_supplier(models.Model):
    _name= "customer.supplier"

    name = fields.Char(size=64)

    def customer_supplier(self):

        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        return self.env['report'].get_action(active_ids, 'export_excel')

class Export_excel(ReportXlsx):

    _name='report.export_excel'

    def generate_xlsx_report(self, workbook, data, partners):

        lst_total = []

        for user_partner in partners:
            type_user = self.env['res.partner'].browse(user_partner.id)
            if type_user.customer == True:
                name = 'Khách hàng'
            else:
                name = 'Nhà cung cấp'

        worksheet = workbook.add_worksheet(_(name))
        worksheet.set_column(0, 0, 20)
        worksheet.set_column(1, 1, 30)
        worksheet.set_column(2, 2, 20)
        worksheet.set_column(3, 3, 15)
        worksheet.set_column(4, 4, 15)
        worksheet.set_column(5, 5, 15)
        worksheet.set_column(6, 6, 15)
        worksheet.set_column(7, 7, 20)
        worksheet.set_column(8, 8, 20)
        worksheet.set_column(9, 9, 20)
        worksheet.set_column(10, 10, 20)
        worksheet.set_column(11, 11, 20)
        worksheet.set_column(12, 12, 20)
        worksheet.set_column(13, 13, 20)
        worksheet.set_column(14, 14, 30)
        worksheet.set_column(15, 15, 20)
        worksheet.set_column(16, 16, 20)
        worksheet.set_column(17, 17, 15)
        row = 0

        title = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 1,
            'font_name': 'Times New Roman',
            'font_size': 12,
            'text_wrap': True,
            'bold': True,
        })
        content_left = workbook.add_format({
            'valign': 'vcenter',
            'align': 'left',
            'border': 1,
            'font_name': 'Times New Roman',
            'font_size': 12,
            'text_wrap': True,
        })
        content_right = workbook.add_format({
            'valign': 'vcenter',
            'align': 'right',
            'border': 1,
            'font_name': 'Times New Roman',
            'font_size': 12,
            'text_wrap': True,
        })
        worksheet.write('A1', u'Nhóm khách hàng', title)
        worksheet.write('B1', u'Tên nhà cung cấp', title)
        worksheet.write('C1', u'Mã nhà cung cấp', title)
        worksheet.write('D1', u'Địa chỉ', title)
        worksheet.write('E1', u'Quốc gia', title)
        worksheet.write('F1', u'Thành phố', title)
        worksheet.write('G1', u'Quận/huyện', title)
        worksheet.write('H1', u'Phường/xã', title)
        worksheet.write('I1', u'Mã số thuế', title)
        worksheet.write('J1', u'Giới tính', title)
        worksheet.write('K1', u'Ngày sinh', title)
        worksheet.write('L1', u'Tiêu đề', title)
        worksheet.write('M1', u'Ghi chú nội bộ', title)
        worksheet.write('N1', u'Số điện thoại', title)
        worksheet.write('O1', u'Email', title)
        worksheet.write('P1', u'Tài khoản phải thu', title)
        worksheet.write('Q1', u'Tài khoản phải trả', title)
        worksheet.write('R1', u'Nhóm', title)

        row = row+1

        for partner in partners:
            record = self.env['res.partner'].browse(partner.id)
            if record.customer == True:
                row = 0
                worksheet.write('A1', u'Loại khách hàng', title)
                worksheet.write('B1', u'Tên khách hàng', title)
                worksheet.write('C1', u'Mã khách hàng', title)
                worksheet.write('D1', u'Địa chỉ', title)
                worksheet.write('E1', u'Quốc gia', title)
                worksheet.write('F1', u'Thành phố', title)
                worksheet.write('G1', u'Quận/huyện', title)
                worksheet.write('H1', u'Phường/xã', title)
                worksheet.write('I1', u'Mã số thuế', title)
                worksheet.write('J1', u'Giới tính', title)
                worksheet.write('K1', u'Ngày sinh', title)
                worksheet.write('L1', u'Tiêu đề', title)
                worksheet.write('M1', u'Ghi chú nội bộ', title)
                worksheet.write('N1', u'Số điện thoại', title)
                worksheet.write('O1', u'Email', title)
                worksheet.write('P1', u'Tài khoản phải thu', title)
                worksheet.write('Q1', u'Tài khoản phải trả', title)
                worksheet.write('R1', u'Nhóm', title)

                row = row+1

            lst_field = []

            if record.company_type == 'person':
                person = u'Cá nhân'
                lst_field.append(unicode(person))
            else:
                company = u'Công ty'
                lst_field.append(company)
            str_date_of_birth = str(record.date_of_birth)
            if record.date_of_birth:
                mmddyy = str_date_of_birth[8:10] + '-' + str_date_of_birth[5:7] + '-' + str_date_of_birth[0:4]
            else:
                mmddyy = ''
            lst_field.append(record.name)
            lst_field.append(record.code or '')
            lst_field.append(record.street or '')
            lst_field.append(record.country_id.name or '')
            lst_field.append(record.state_id.name or '')
            lst_field.append(record.district_id.name or '')
            lst_field.append(record.ward_id.name or '')
            lst_field.append(record.vat or '')
            lst_field.append(record.sex or '')
            lst_field.append(mmddyy)
            lst_field.append(record.title.name or '')
            lst_field.append(record.comment or '')
            lst_field.append(record.phone or '')
            lst_field.append(record.email or '')
            lst_field.append(record.property_account_receivable_id.code or '')
            lst_field.append(record.property_account_payable_id.code or '')
            lst_field.append(record.group_user.name or '')
            lst_total.append(lst_field)

        for total in lst_total:

            worksheet.write(row, 0, total[0], content_left)
            worksheet.write(row, 1, total[1], content_left)
            worksheet.write(row, 2, total[2], content_left)
            worksheet.write(row, 3, total[3], content_left)
            worksheet.write(row, 4, total[4], content_left)
            worksheet.write(row, 5, total[5], content_left)
            worksheet.write(row, 6, total[6], content_left)
            worksheet.write(row, 7, total[7], content_left)
            worksheet.write(row, 8, total[8], content_right)
            worksheet.write(row, 9, total[9], content_left)
            worksheet.write(row, 10, total[10], content_left)
            worksheet.write(row, 11, total[11], content_left)
            worksheet.write(row, 12, total[12], content_left)
            worksheet.write(row, 13, total[13], content_left)
            worksheet.write(row, 14, total[14], content_left)
            worksheet.write(row, 15, total[15], content_right)
            worksheet.write(row, 16, total[16], content_right)
            worksheet.write(row, 17, total[17], content_left)
            row += 1

Export_excel('report.export_excel','customer.supplier')