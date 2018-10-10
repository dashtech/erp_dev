#!/usr/bin/python
# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
import xlwt
from xlwt import Formula
from xlsxwriter.workbook import Workbook
import datetime
import base64
import cStringIO
from  calendar import monthrange
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx


class btek_assets_report(models.Model):
    _name = "btek.assets.report"
    _description = "Assets Report"

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    @api.model
    def _getdate(self):
        return datetime.date(datetime.date.today().year, 1, 1)

    start_date = fields.Date(default=_getdate)
    end_date = fields.Date(default=fields.Date.today)
    res_company_id = fields.Many2one('res.company', required=True, default=_get_company)
    x_category_id = fields.Many2one('account.asset.category')

    def action_print(self):
        return self.env['report'].get_action(self, 'btek_account_asset_report.assets_report')


class assets_report(ReportXlsx):
    _name = 'report.btek_account_asset_report.assets_report'

    def write_asset_report(self, ws, data, form):
        ws.set_column(0, 0, 10)
        ws.set_column(1, 1, 25)
        ws.set_column(2, 2, 17)
        ws.set_column(3, 3, 17)
        ws.set_column(4, 4, 16)
        ws.set_column(5, 5, 16)
        ws.set_column(6, 6, 16)
        ws.set_column(7, 7, 16)
        ws.set_column(8, 8, 16)
        ws.set_column(9, 9, 15)
        ws.set_column(10, 10, 15)
        ws.set_column(11, 11, 15)
        ws.set_column(12, 12, 15)
        ws.set_column(13, 13, 15)
        ws.set_column(14, 14, 16)
        ws.set_row(5, 25)

        address = ''
        if form.res_company_id.street: address = form.res_company_id.street
        if form.res_company_id.street2: address = address + ', ' + form.res_company_id.street2
        if form.res_company_id.city: address = address + ', ' + form.res_company_id.city
        if form.res_company_id.country_id.name: address = address + ', ' + form.res_company_id.country_id.name
        mst = form.res_company_id.vat

        start = form.start_date
        end = form.end_date

        # Header
        ws.write("A1", u'Đơn vị báo cáo :', )
        ws.write("A2", u'Địa chỉ :', )
        ws.write("A4", u'MST :', )
        ws.merge_range("B1:E1", unicode(form.res_company_id.name) or '', self.bold)
        ws.merge_range("B2:E3", unicode(address) or '', self.bold)
        ws.merge_range("B4:C4", mst or '', self.bold)

        string_lable = u"BÁO CÁO TỔNG HỢP TĂNG GIẢM VÀ KHẤU HAO TSCĐ"
        ws.merge_range("E6:K6", string_lable, self.title)
        if start and end:
            start_view = datetime.datetime.strptime(start, '%Y-%m-%d').strftime('%d/%m/%Y').decode('unicode-escape')
            end_view = datetime.datetime.strptime(end, '%Y-%m-%d').strftime('%d/%m/%Y').decode('unicode-escape')
            ws.merge_range("E7:K7", u" Từ ngày: " + start_view + u" đến ngày: " + end_view + u"", self.text_center)

        # Header Table

        ws.merge_range("A10:A11", u"Mã SP", self.table_header)
        ws.merge_range("B10:B11", u"Tên tài sản", self.table_header)
        ws.merge_range("C10:C11", u"Ngày SD", self.table_header)
        ws.merge_range("D10:D11", u"Số kì khấu hao", self.table_header)
        ws.merge_range("E10:G10", u"Đầu kì", self.table_header)
        ws.write("E11", u"Nguyên giá", self.table_header)
        ws.write("F11", u"GT đã khấu hao", self.table_header)
        ws.write("G11", u"GT còn lại", self.table_header)
        ws.merge_range("H10:J10", u"Trong kì", self.table_header)
        ws.write("H11", u"Tăng", self.table_header)
        ws.write("I11", u"Giảm", self.table_header)
        ws.write("J11", u"KH trong kì", self.table_header)
        ws.merge_range("K10:K11", u"Tài khoản", self.table_header)
        ws.merge_range("L10:N10", u"Cuối kì", self.table_header)
        ws.write("L11", u"Nguyên giá", self.table_header)
        ws.write("M11", u"GT đã khấu hao", self.table_header)
        ws.write("N11", u"GT còn lại", self.table_header)
        ws.merge_range("O10:O11", u"Nhóm TSCĐ", self.table_header)
        row = 12
        if data:
            for r in data:
                ws.write("A{row}".format(row=row), r['code'] or '', self.table_row_left)
                ws.write("B{row}".format(row=row), r['name'] or '', self.table_row_left)
                ws.write("C{row}".format(row=row), r['purchase_date'] or '', self.table_row_left)
                ws.write("D{row}".format(row=row), r['method_number'] or '', self.table_row_left)
                ws.write("E{row}".format(row=row), r['nguyen_gia'] or '', self.num_left)
                ws.write("F{row}".format(row=row), r['gt_dakhauhao_dauki'] or '', self.num_left)
                ws.write("G{row}".format(row=row), r['gt_conlai_dauki'] or '', self.num_left)
                ws.write("H{row}".format(row=row), r['tang_trongki'] or '', self.num_left)
                ws.write("I{row}".format(row=row), r['giam_trongki'] or '', self.num_left)
                ws.write("J{row}".format(row=row), r['khauhao_trongki'] or '', self.num_left)
                ws.write("K{row}".format(row=row), r['tk'] or '', self.table_row_left)
                ws.write("L{row}".format(row=row), r['nguyen_gia_cuoi_ki'] or '', self.num_left)
                ws.write("M{row}".format(row=row), r['gt_dakh_cuoiki'] or '', self.num_left)
                ws.write("N{row}".format(row=row), r['gt_conlaicuoiki'] or '', self.num_left)
                ws.write("O{row}".format(row=row), r['tscd'] or '', self.table_row_left)
                row += 1

    def generate_xlsx_report(self, wb, data, form):
        reports = {
            'report': self.write_asset_report,
        }
        ws = wb.add_worksheet('report')
        wb.formats[0].font_name = 'Times New Roman'
        wb.formats[0].font_size = 11
        ws.set_paper(9)
        ws.center_horizontally()
        ws.set_margins(left=0.28, right=0.28, top=0.5, bottom=0.5)
        ws.fit_to_pages(1, 0)
        ws.set_landscape()
        ws.fit_to_pages(1, 1)

        # DEFINE FORMATS
        self.header = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_name': 'Times New Roman'
        })

        self.xxxxx = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'font_name': 'Times New Roman'
        })
        self.title = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 18,
            'font_name': 'Times New Roman',
        })
        self.bold_right_big = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'align': 'right',
            'valign': 'vcenter',
            'font_name': 'Times New Roman'
        })
        self.bold = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'valign': 'vcenter',
            'font_name': 'Times New Roman'
        })
        self.right = wb.add_format({
            'text_wrap': 1,
            'align': 'right',
            'valign': 'vcenter',
            'num_format': '#,##0.00',
            'font_name': 'Times New Roman'
        })

        self.num_left = wb.add_format({
            'text_wrap': 1,
            'align': 'left',
            'valign': 'vcenter',
            'num_format': '#,##0.00',
            'font_name': 'Times New Roman',
            'border': 1,

        })

        self.center = wb.add_format({
            'text_wrap': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_name': 'Times New Roman'
        })

        self.text_center = wb.add_format({
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_name': 'Times New Roman'
        })

        self.table_header = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'font_name': 'Times New Roman',
        })

        self.table_row_left = wb.add_format({
            'text_wrap': 1,
            'align': 'left',
            'valign': 'vcenter',
            'border': 1,
            'font_name': 'Times New Roman',
        })

        self.table_row_left_bold = wb.add_format({
            'text_wrap': 1,
            'align': 'left',
            'bold': 1,
            'valign': 'vcenter',
            'border': 1,
            'font_name': 'Times New Roman',
        })

        self.table_row_right = wb.add_format({
            'text_wrap': 1,
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
            'num_format': '#,##0.00',
            'font_name': 'Times New Roman',
        })
        self.table_row_right_bold = wb.add_format({
            'text_wrap': 1,
            'align': 'right',
            'valign': 'vcenter',
            'bold': 1,
            'border': 1,
            'num_format': '#,##0.00',
            'font_name': 'Times New Roman',
        })
        asset_id = self.env['account.asset.asset'].search([]).ids
        asset_ids = ",".join([str(x) for x in asset_id])
        if form.x_category_id:
            category_ids = str(form.x_category_id.id)
        if not form.x_category_id:
            category_ids = ",".join([str(x) for x in self.env['account.asset.category'].search([]).ids])
        args = {
            'start': form.start_date,
            'end': form.end_date,
            'company_id': form.res_company_id.id,
            'category_id': category_ids,
            'asset_ids': asset_ids or '1',
        }
        report_data = self.get_data_from_query(args)
        reports['report'](ws, report_data, form)

    def get_data_from_query(self, kwargs):
        sql = self.get_query(kwargs)
        self.env.cr.execute(sql)
        data = self.env.cr.dictfetchall()
        return data

    def get_query(self, kwargs):
        sql = """
             WITH account_tbl AS
              (SELECT aaa.code,
                      aaa.name,
                      date,
                      aaa.method_number, value, aaa.salvage_value,
                      --Dauki
             COALESCE(
                        (SELECT value
                         FROM account_asset_asset
                         WHERE date(date) < date('{start}')
                           AND id = aaa.id),0) AS nguyen_gia,
             COALESCE(
                        (SELECT sum(amount) + aaa.salvage_value
                         FROM account_asset_depreciation_line
                         WHERE asset_id = aaa.id
                           AND date(depreciation_date) < date('{start}')
                           AND dispose_flag = False
                           AND move_check=TRUE),0) AS gt_dakhauhao_dauki,
             COALESCE( (select amount from  account_asset_depreciation_line
                where asset_id = aaa.id
                AND dispose_flag = True
                AND date(depreciation_date) < date('{start}')
                AND move_check=TRUE), 0) as giam_dauki
                           --Trongki
             ,
             COALESCE(
                        (SELECT value
                         FROM account_asset_asset
                         WHERE date(date) >= date('{start}')
                           AND date(date) <= date('{end}')
                           AND id = aaa.id),0) AS tang_trongki ,
             COALESCE((select amount from  account_asset_depreciation_line
                where asset_id = aaa.id
                AND dispose_flag = True
             AND date(depreciation_date) >= date('{start}')
             AND date(depreciation_date) <= date('{end}')
             AND move_check=TRUE ), 0) AS giam_trongki ,
             COALESCE(
                        (SELECT sum(amount)
                         FROM account_asset_depreciation_line
                         WHERE asset_id = aaa.id
                           AND date(depreciation_date) >= date('{start}')
                           AND date(depreciation_date) <= date('{end}')
                           AND dispose_flag = False
                           AND move_check=TRUE),0) AS khauhao_trongki ,
             aa.code AS tk,
             --cuoiki
             COALESCE(
                        (SELECT value
                         FROM account_asset_asset
                         WHERE date(date) <= date('{end}')
                           AND id = aaa.id),0) AS nguyen_gia_cuoi_ki,
             aac.name as tscd, aaa.state
               FROM account_asset_asset aaa
               JOIN account_asset_category aac ON aaa.category_id = aac.id
               JOIN account_account aa ON aa.id = aac.account_depreciation_expense_id
               WHERE aaa.id in ({asset_ids}) and aaa.company_id = {company_id} and aac.id in ({category_id})
              )
            SELECT tscd ,
                   code,
                   name,
                   to_char(date,'dd/mm/YYYY') as purchase_date,
                   method_number,
                   value,
                   nguyen_gia,
                   gt_dakhauhao_dauki,
                   nguyen_gia - gt_dakhauhao_dauki AS gt_conlai_dauki,
                   tang_trongki,
                   COALESCE(giam_trongki,0) as giam_trongki,
                   khauhao_trongki,
                   tk,
                   value as pu,
                   nguyen_gia_cuoi_ki,
                   gt_dakhauhao_dauki + giam_trongki + khauhao_trongki AS gt_dakh_cuoiki,
                   nguyen_gia_cuoi_ki - (gt_dakhauhao_dauki+ giam_trongki + khauhao_trongki) AS gt_conlaicuoiki, date
            FROM account_tbl
            where date(date) <= date('{end}') and state != 'draft'
            order by date asc
                       """.format(**kwargs)
        return sql


assets_report('report.btek_account_asset_report.assets_report', 'btek.assets.report')
