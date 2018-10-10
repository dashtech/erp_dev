#!/usr/bin/python
# -*- encoding: utf-8 -*-
# ANHTT
from odoo import api, fields, models, _
import datetime


class TaxInOut(models.TransientModel):
    _name = 'tax.in.out.report'

    @api.model
    def _getdate(self):
        return datetime.date(datetime.date.today().year, 1, 1)

    @api.model
    def _gettoday(self):
        return datetime.date.today()

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    start_date = fields.Date(default=_getdate)
    end_date = fields.Date(default=_gettoday)
    type_report = fields.Selection([('in', 'in'), ('out', 'out')], required=1)
    company_id = fields.Many2one('res.company', required=True, default=_get_company)

    @api.multi
    def action_print(self):
        return self.env['report'].get_action(self, 'btek_tax_report.tax_in_out_report')


from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx


class TaxInOutReport(ReportXlsx):
    _name = 'report.btek_tax_report.tax_in_out_report'

    def write_tax_inout(self, ws, data, form):
        ws.set_column(0, 0, 7)
        ws.set_column(1, 1, 15)
        ws.set_column(2, 2, 15)
        ws.set_column(3, 3, 15)
        ws.set_column(4, 4, 15)
        ws.set_column(5, 5, 15)
        ws.set_column(6, 6, 15)
        ws.set_column(7, 7, 15)
        ws.set_column(8, 8, 15)
        ws.set_column(9, 9, 15)
        ws.set_column(10, 10, 15)
        ws.set_column(11, 11, 15)
        ws.set_column(12, 12, 15)
        ws.set_column(13, 13, 15)
        ws.set_column(14, 14, 15)
        ws.set_row(7, 40)

        # Header
        # address = u''
        # if form.company_id.street: address = form.company_id.street
        # if form.company_id.street2: address = address + ', ' + unicode(form.company_id.street2)
        # if form.company_id.city: address = address + ', ' + unicode(form.company_id.city)
        # ws.write('A%s' % 1, u'Đơn vị báo cáo:', )
        # ws.merge_range('B1:E1', form.company_id.name, self.xxxxx)
        # ws.write('A%s' % 2, u'Địa chỉ:', )
        # ws.merge_range('B2:E2', address, self.xxxxx)

        row = 11
        # ws.write('B%s' % row, u'Chọn', self.table_header)
        ws.write('A%s' % row, u'STT', self.table_header)
        ws.write('B%s' % row, u'Ký hiệu mẫu hóa', self.table_header)
        ws.write('C%s' % row, u'Ký hiệu hoá đơn', self.table_header)
        ws.write('D%s' % row, u'Số hoá đơn', self.table_header)
        ws.write('E%s' % row, u'Ngày hóa đơn', self.table_header)
        if form.type_report == 'in':
            ws.write('F%s' % row, u'Tên người bán', self.table_header)
            ws.write('G%s' % row, u'Mã số thuế người bán', self.table_header)
        else:
            ws.write('F%s' % row, u'Tên người mua', self.table_header)
            ws.write('G%s' % row, u'Mã số thuế người mua', self.table_header)
        ws.write('H%s' % row, u'Mặt hàng', self.table_header)

        row = 12
        res_data = data
        if res_data and form.type_report == 'in':
            ws.merge_range('A8:B8', u'Người nộp thuế:', )
            ws.merge_range('C8:E8', form.company_id.name, )
            ws.write('A9:B9', u'Mã số thuế:', )
            ws.merge_range('C9:E9', form.company_id.vat, )
            ws.write('L10', u'Đồng tiền: VND', )

            ws.merge_range('A4:L4', u'BẢNG KÊ HOÁ ĐƠN, CHỨNG TỪ HÀNG HOÁ, DỊCH VỤ MUA VÀO', self.title)
            ws.merge_range('A6:L6', u'(Kèm theo tờ khai thuế GTGT theo mẫu số 01/GTGT)', self.center)
            ws.merge_range('A7:L7', u'Từ ngày: ' + unicode(
                datetime.datetime.strptime(form.start_date, '%Y-%m-%d').strftime('%d/%m/%Y'))
                           + u' Đến ngày: ' + unicode(
                datetime.datetime.strptime(form.end_date, '%Y-%m-%d').strftime('%d/%m/%Y')), self.center)
            ws.write('I%s' % 11, u'Doanh số mua chưa có thuế GTGT', self.table_header)
            ws.write('J%s' % 11, u'Thuế suất', self.table_header)
            ws.write('K%s' % 11, u'Thuế GTGT', self.table_header)
            ws.write('L%s' % 11, u'Ghi chú', self.table_header)
            partner_obj = self.env['res.partner']
            invoice_number = None
            thue_suat = None
            thue_gtgt = doanh_so = 0
            total_doanh_so = 0
            total_gtgt = 0
            # Table data
            row = 12
            check = False
            for i, line in enumerate(res_data):
                col = 0
                if i > 0 and res_data[i]['nhom'] == 3 and res_data[i - 1]['nhom'] == 1:
                    ws.merge_range(row, row, 1, 12, "", self.table_row_left)
                    row += 1
                if line['nhom'] in (1, 3):
                    if line['nhom'] == 3:
                        if check == True:
                            row += 1
                            check = False
                        ws.merge_range("A{row}:L{row}".format(row=row), line['stt'] or '', self.table_row_left)
                    else:
                        ws.merge_range("A{row}:L{row}".format(row=row), line['stt'] or '', self.table_row_left)
                        check = True
                else:
                    ws.write(row, col, line['stt'] or '', self.table_row_left)
                    ws.write(row, col + 1, line['mau_so'] or '', self.table_row_left)
                    ws.write(row, col + 2, line['ky_hieu'] or '', self.table_row_left)
                    ws.write(row, col + 3, line['invoice_number'] or '', self.table_row_left)
                    ws.write(row, col + 4, line['ngay_hd'] or '', self.table_row_left)
                    ten_nguoi_ban = line['ten_nguoi_ban'] or ''
                    partner_id = partner_obj.browse(line['partner_id'])
                    if not line['ten_nguoi_ban']:
                        partner_id = partner_obj.browse(line['partner_id'])
                        contacts = partner_id.child_ids.filtered(lambda x: x.type == 'invoice')
                        if len(contacts) > 0:
                            ten_nguoi_ban = contacts[0].name
                    ws.write(row, col + 5, partner_id.name or '', self.table_row_left)
                    ws.write(row, col + 6, line['mst'] or '', self.table_row_left)
                    ws.write(row, col + 7, line['mat_hang'] or '', self.table_row_left)
                    ws.write(row, col + 8, round(line['doanh_so'], 0) or '', self.table_row_right)
                    ws.write(row, col + 9, line['thue_suat'] or '', self.table_row_right)
                    ws.write(row, col + 10, round(line['thue_gtgt'], 0) or 0, self.table_row_right)
                    ws.write(row, col + 11, line['ghi_chu'] or '', self.table_row_left)
                row += 1
                if line['doanh_so']:
                    total_doanh_so += round(line['doanh_so'], 0) or 0
                if line['thue_gtgt']:
                    total_gtgt += round(line['thue_gtgt'], 0) or 0
            row += 1
            ws.merge_range("A{row}:E{row}".format(row=row),
                           u"Tổng giá trị HHDV mua vào phục vụ SXKD được khấu trừ thuế GTGT (**): ", self.xxxxx)
            ws.write("F{row}".format(row=row), total_doanh_so, self.table_row_right_bolds)
            ws.merge_range("A{row}:E{row}".format(row=row + 1),
                           u"Tổng số thuế GTGT của HHDV mua vào đủ điều kiện được khấu trừ (***):", self.xxxxx)
            ws.write("F{row}".format(row=row + 1), total_gtgt, self.table_row_right_bolds)

        if res_data and form.type_report == 'out':
            ws.merge_range('A8:B8', u'Người nộp thuế:', )
            ws.merge_range('C8:E8', form.company_id.name, )
            ws.write('A9:B9', u'Mã số thuế:', )
            ws.merge_range('C9:E9', form.company_id.vat, )
            ws.write('K10', u'Đồng tiền: VND', )

            ws.merge_range('A4:K4', u'BẢNG KÊ HOÁ ĐƠN, CHỨNG TỪ HÀNG HOÁ, DỊCH VỤ BÁN RA', self.title)
            ws.merge_range('A6:K6', u'(Kèm theo tờ khai thuế GTGT theo mẫu số 01/GTGT)', self.center)
            ws.merge_range('A7:K7', u'Từ ngày: ' + unicode(
                datetime.datetime.strptime(form.start_date, '%Y-%m-%d').strftime('%d/%m/%Y'))
                           + u' Đến ngày: ' + unicode(
                datetime.datetime.strptime(form.end_date, '%Y-%m-%d').strftime('%d/%m/%Y')), self.center)
            ws.write('I%s' % 11, u'Doanh thu chưa có thuế GTGT', self.table_header)
            ws.write('J%s' % 11, u'Thuế GTGT', self.table_header)
            ws.write('K%s' % 11, u'Ghi chú', self.table_header)
            partner_obj = self.env['res.partner']
            sum_thue_gtgt_0 = sum_thue_gtgt_5 = sum_thue_gtgt_10 = 0.0
            sum_doanh_so_0 = sum_doanh_so_5 = sum_doanh_so_10 = 0.0
            total_doanh_so = 0
            total_gtgt = 0

            # Table data
            check = False
            for i, line in enumerate(res_data):
                col = 0
                # if row == 158:
                #     a = 1
                if i > 0 and res_data[i]['nhom'] == 3 and res_data[i - 1]['nhom'] == 1:
                    ws.merge_range("A{row}:K{row}".format(row=row), line['stt'], self.table_row_left)
                    row += 1
                if line['nhom'] in (1, 3):
                    if line['nhom'] == 1:
                        ws.merge_range("A{row}:K{row}".format(row=row), line['stt'] or '', self.table_row_left_bold)
                    if line['nhom'] == 3:  # Tong
                        if res_data[i - 1]['nhom'] == 2 and i > 0:

                            if res_data[i - 1]['tax_gtgt'] == 0:
                                ws.merge_range("A{row}:H{row}".format(row=row), u"Tổng", self.table_row_left)
                                ws.write("I{row}".format(row=row), round(sum_doanh_so_0, 0), self.table_row_right_bold)
                                ws.write("J{row}".format(row=row), round(sum_thue_gtgt_0, 0), self.table_row_right_bold)
                                ws.write("K{row}".format(row=row), '', self.table_row_right)
                            if res_data[i - 1]['tax_gtgt'] == 5:
                                ws.merge_range("A{row}:H{row}".format(row=row), u"Tổng", self.table_row_left)
                                ws.write("I{row}".format(row=row), round(sum_doanh_so_5, 0), self.table_row_right_bold)
                                ws.write("J{row}".format(row=row), round(sum_thue_gtgt_5, 0), self.table_row_right_bold)
                                ws.write("K{row}".format(row=row), '', self.table_row_right)
                            if res_data[i - 1]['tax_gtgt'] == 10:
                                ws.merge_range("A{row}:H{row}".format(row=row), u"Tổng", self.table_row_left)
                                ws.write("I{row}".format(row=row), round(sum_doanh_so_10, 0), self.table_row_right_bold)
                                ws.write("J{row}".format(row=row), round(sum_thue_gtgt_10, 0),
                                         self.table_row_right_bold)
                                ws.write("K{row}".format(row=row), '', self.table_row_right)
                            row += 1
                else:
                    ws.write("A{row}".format(row=row), line['stt'] or '', self.table_row_left)
                    ws.write("B{row}".format(row=row), line['mau_so'] or '', self.table_row_left)
                    ws.write("C{row}".format(row=row), line['ky_hieu'] or '', self.table_row_left)
                    ws.write("D{row}".format(row=row), line['invoice_number'] or '', self.table_row_left)
                    ws.write("E{row}".format(row=row), line['ngay_hd'] or '', self.table_row_left)
                    ten_nguoi_ban = line['ten_nguoi_ban'] or ''
                    # if line['partner_id'] and line['partner_id'] != -1:
                    if line['ten_nguoi_ban']:
                        partner_id = partner_obj.browse(line['ten_nguoi_ban'])
                        # contacts = partner_id.child_ids.filtered(lambda x: x.type == 'invoice')
                        # if len(contacts) > 0:
                        #     ten_nguoi_ban = contacts[0].name
                    else:
                        partner_id = partner_obj.browse(line['partner_id'])
                    ws.write("F{row}".format(row=row), partner_id.name or '', self.table_row_left)
                    ws.write("G{row}".format(row=row), line['mst'] or '', self.table_row_left)
                    ws.write("H{row}".format(row=row), line['mat_hang'] or '', self.table_row_left)
                    ws.write("I{row}".format(row=row), round(line['doanh_so'], 0) or '', self.table_row_right)
                    ws.write("J{row}".format(row=row), round(line['thue_gtgt'], 0) or '', self.table_row_right)
                    ws.write("K{row}".format(row=row), line['ghi_chu'] or '', self.table_row_left)
                    if line['tax_gtgt'] == 0:
                        sum_thue_gtgt_0 += round(line['thue_gtgt'], 0) or 0.0
                        sum_doanh_so_0 += round(line['doanh_so'], 0) or 0.0
                    if line['tax_gtgt'] == 5:
                        sum_thue_gtgt_5 += round(line['thue_gtgt'], 0) or 0.0
                        sum_doanh_so_5 += round(line['doanh_so'], 0) or 0.0
                    if line['tax_gtgt'] == 10:
                        sum_thue_gtgt_10 += round(line['thue_gtgt'], 0) or 0.0
                        sum_doanh_so_10 += round(line['doanh_so'], 0) or 0.0
                row += 1
                total_doanh_so += round(line['doanh_so'], 0) or 0
                total_gtgt += round(line['thue_gtgt'], 0) or 0
            row += 1
            ws.merge_range("A{row}:E{row}".format(row=row),
                           u"Tổng doanh thu hàng hoá, dịch vụ bán ra chịu thuế GTGT (*): ",
                           )
            ws.write("F{row}".format(row=row), total_doanh_so, self.table_row_right_bolds)
            ws.merge_range("A{row}:E{row}".format(row=row + 1),
                           u"Tổng số thuế GTGT của hàng hóa, dịch vụ bán ra (**): %s",
                           )
            ws.write("F{row}".format(row=row + 1), total_gtgt, self.table_row_right_bolds)

    def generate_xlsx_report(self, wb, data, form):
        reports = {
            'report': self.write_tax_inout,
        }
        ws = wb.add_worksheet('Tax')
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
            'font_size': 15,
            'font_color': '#1357f5',
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

        self.center = wb.add_format({
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
            # 'bg_color': '#C6EFCE',
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

        self.table_row_right_bolds = wb.add_format({
            'text_wrap': 1,
            'align': 'right',
            'valign': 'vcenter',
            # 'bold': 1,
            # 'border': 1,
            'num_format': '#,##0.00',
            'font_name': 'Times New Roman',
        })
        args = {
            'start': form.start_date,
            'end': form.end_date,
            'company_id': form.company_id.id,
        }
        if form.type_report == 'in':
            report_data = self.get_data_from_query_in(args)
        else:
            report_data = self.get_data_from_query_out(args)
        reports['report'](ws, report_data, form)

    def get_data_from_query_in(self, kwargs):
        sql = self.get_query_in(kwargs)
        self.env.cr.execute(sql)
        data = self.env.cr.dictfetchall()
        return data

    def get_data_from_query_out(self, kwargs):
        sql = self.get_query_out(kwargs)
        self.env.cr.execute(sql)
        data = self.env.cr.dictfetchall()
        return data

    def get_query_in(self, kwargs):
        sql = """
        WITH tonghop AS (

            SELECT CAST(0 AS numeric) AS stt1, CAST('1. Hàng hoá, dịch vụ dùng riêng cho SXKD chịu thuế GTGT và sử dụng cho các hoạt động cung cấp hàng hoá, dịch vụ không kê khai, nộp thuế GTGT đủ điều kiện khấu trừ thuế' AS VARCHAR(200)) AS stt, CAST('' AS VARCHAR(200)) AS mau_so,
                CAST('' AS VARCHAR(200)) AS ky_hieu, CAST('' AS VARCHAR(200)) AS invoice_number,
                CAST (NULL AS date) AS ngay_hd, CAST('' AS VARCHAR(200)) AS ten_nguoi_ban, CAST('' AS VARCHAR(200)) AS mst, CAST('' AS VARCHAR(200)) AS mat_hang,
                0 AS doanh_so, CAST('' AS VARCHAR(200)) AS thue_suat, 0 AS thue_gtgt, CAST('' AS VARCHAR(200)) AS ghi_chu, 1 AS nhom
        ),
        tonghop2 AS (
                WITH tmp AS
                (
                SELECT inv.date_invoice as registration_date,at.name AS stt,
                CAST(template_invoice.template_symbol AS VARCHAR(200)) AS mau_so, symbol.invoice_symbol::char AS ky_hieu,
                CAST(inv.supplier_invoice_number AS VARCHAR(200)) AS invoice_number,
                CAST(inv.date_invoice AS date) AS ngay_hd, 
                LTRIM(RTRIM(CAST(inv.vat_partner AS VARCHAR(200)))) AS ten_nguoi_ban, CAST(inv.tax_code AS VARCHAR(200)) AS MST,
                case when inv.type = 'in_refund' then tax.x_base*(-1) else tax.x_base end AS doanh_so,
                case when at.name like '%5%' then '5%'
                when at.name like '%10%' then '10%'
                when at.name like '%0%' then '0%'
                when tax.name like '%Hàng mua không chịu thuế%' then 'Hàng mua không chịu thuế' end AS thue_suat,
                 --CASE WHEN inv_line.x_rounding_price_tax = 0 THEN inv_line.price_tax  ELSE  inv_line.x_rounding_price_tax END AS thue_gtgt,
                 case when inv.type = 'in_refund' then tax.amount*(-1) else tax.amount end as thue_gtgt,
                CAST('' AS VARCHAR(200)) AS ghi_chu, 2 AS nhom
                ,inv.partner_id as partner_id,
                (SELECT name from account_invoice_line where invoice_id = inv.id limit 1) as mat_hang
            FROM account_invoice_tax AS tax LEFT JOIN
                account_invoice AS inv ON tax.invoice_id = inv.id LEFT JOIN
	            --account_invoice_line inv_line ON inv.id = inv_line.invoice_id LEFT JOIN
                res_partner AS par ON inv.partner_id = par.id --LEFT JOIN
                --account_tax_code AS grouptax ON tax.base_code_id = grouptax.id
                left join account_tax at on at.id = tax.tax_id
                left join account_invoicel_template template_invoice on template_invoice.id = inv.template_symbol
                left join account_invoicel_symbol symbol on symbol.id = inv.invoice_symbol
            WHERE (inv.state = 'paid' or inv.state = 'open') AND  (inv.type = 'in_invoice' or inv.type = 'in_refund')
                AND inv.date_invoice BETWEEN '{start}' AND '{end}'
                AND tax.company_id = {company_id}



              union all
                select xtax.x_date_invoice as registration_date
                        ,tax.name AS stt,
                        CAST(xtax.x_invoice_symbol AS VARCHAR(200)) AS mau_so,
                        (xtax.x_invoice_symbol) AS ky_hieu,
                        LTRIM(RTRIM(CAST(avl.x_supplier_invoice_number AS VARCHAR(200)))) AS invoice_number,
                        CAST(xtax.x_registration_date AS date) AS ngay_hd,
                        LTRIM(RTRIM(CAST(xtax.x_partner_id AS VARCHAR(200)))) AS ten_nguoi_ban,
                        (CAST('' AS VARCHAR(200))) AS MST,
                        sum(xtax.base) AS doanh_so,
                        (case when tax.name like '%5%' then '5%'
                                        when tax.name like '%10%' then '10%'
                                        when tax.name like '%0%' then '0%'
                                        when tax.name like '%Hàng mua không chịu thuế%' then 'Hàng mua không chịu thuế' end) AS thue_suat,
                        sum(avl.x_rounding_price_tax) as thue_gtgt,
                        CAST('' AS VARCHAR(200)) AS ghi_chu, 2 AS nhom,
                        0 as partner_id,
                        LTRIM(RTRIM(avl.name)) as mat_hang
                        from x_account_voucher_tax xtax
                        join account_tax_account_voucher_line_rel rel on rel.account_voucher_line_id = xtax.voucher_line_id

                        left join account_voucher_line avl on avl.id = rel.account_voucher_line_id
                        left join account_voucher av on av.id = xtax.voucher_id
                        left join account_journal aj on aj.id = av.journal_id

                        join account_tax tax on tax.id = rel.account_tax_id
                        where av.voucher_type = 'purchase'
                        and av.state = 'posted'
			            and avl.company_id = {company_id}
                        and xtax.x_date_invoice BETWEEN '{start}' AND '{end}'
                        and (select count(id) from x_account_voucher_tax where voucher_id = av.id) > 0
                        group by av.id, registration_date, stt, mau_so, ky_hieu, invoice_number, ngay_hd, ten_nguoi_ban, mst,
                        thue_suat, ghi_chu, nhom, partner_id, mat_hang
                )

            SELECT CAST(ROW_NUMBER() OVER (ORDER BY tmp.registration_date) AS numeric) AS stt1,
            tmp.stt,tmp.mau_so,tmp.ky_hieu,tmp.invoice_number, tmp.doanh_so as doanh_so,
            tmp.ngay_hd,tmp.ten_nguoi_ban,tmp.MST,tmp.thue_suat,tmp.ghi_chu,tmp.nhom,tmp.partner_id,tmp.mat_hang,
            SUM(tmp.thue_gtgt) AS thue_gtgt
            FROM tmp
            GROUP BY tmp.registration_date,tmp.stt,tmp.mau_so,tmp.ky_hieu,tmp.invoice_number, tmp.doanh_so,
            tmp.ngay_hd,tmp.ten_nguoi_ban,tmp.MST,tmp.thue_suat,tmp.ghi_chu,tmp.nhom,tmp.partner_id,tmp.mat_hang

        ),

        tonghop3 AS (
            SELECT CAST(0 AS numeric) AS stt1, CAST('Tổng' AS VARCHAR(200)) AS stt, CAST('' AS VARCHAR(200)) AS mau_so,
                CAST('' AS VARCHAR(200)) AS ky_hieu, CAST('' AS VARCHAR(200)) AS invoice_number,
                CAST (NULL AS date) AS ngay_hd, CAST('' AS VARCHAR(200)) AS ten_nguoi_ban, CAST('' AS VARCHAR(200)) AS mst, CAST('' AS VARCHAR(200)) AS mat_hang,
                0 AS doanh_so, CAST('' AS VARCHAR(200)) AS thue_suat, 0 AS thue_gtgt, CAST('' AS VARCHAR(200)) AS ghi_chu, 3 AS nhom
            UNION ALL
            SELECT CAST(1 AS numeric) AS stt1, CAST('2. Hàng hoá, dịch vụ dùng chung cho SXKD chịu thuế và không chịu thuế đủ điều kiện khấu trừ thuế:' AS VARCHAR(200)) AS stt, CAST('' AS VARCHAR(200)) AS mau_so,
                CAST('' AS VARCHAR(200)) AS ky_hieu, CAST('' AS VARCHAR(200)) AS invoice_number,
                CAST (NULL AS date) AS ngay_hd, CAST('' AS VARCHAR(200)) AS ten_nguoi_ban, CAST('' AS VARCHAR(200)) AS mst, CAST('' AS VARCHAR(200)) AS mat_hang,
                0 AS doanh_so, CAST('' AS VARCHAR(200)) AS thue_suat, 0 AS thue_gtgt, CAST('' AS VARCHAR(200)) AS ghi_chu, 3 AS nhom
            UNION ALL
            SELECT CAST(2 AS numeric) AS stt1, CAST('' AS VARCHAR(200)) AS stt, CAST('' AS VARCHAR(200)) AS mau_so,
                CAST('' AS VARCHAR(200)) AS ky_hieu, CAST('' AS VARCHAR(200)) AS invoice_number,
                CAST (NULL AS date) AS ngay_hd, CAST('' AS VARCHAR(200)) AS ten_nguoi_ban, CAST('' AS VARCHAR(200)) AS mst, CAST('' AS VARCHAR(200)) AS mat_hang,
                0 AS doanh_so, CAST('' AS VARCHAR(200)) AS thue_suat, 0 AS thue_gtgt, CAST('' AS VARCHAR(200)) AS ghi_chu, 3 AS nhom
            UNION ALL
                SELECT CAST(3 AS numeric) AS stt1, CAST('Tổng' AS VARCHAR(200)) AS stt, CAST('' AS VARCHAR(200)) AS mau_so,
                CAST('' AS VARCHAR(200)) AS ky_hieu, CAST('' AS VARCHAR(200)) AS invoice_number,
                CAST (NULL AS date) AS ngay_hd, CAST('' AS VARCHAR(200)) AS ten_nguoi_ban, CAST('' AS VARCHAR(200)) AS mst, CAST('' AS VARCHAR(200)) AS mat_hang,
                0 AS doanh_so, CAST('' AS VARCHAR(200)) AS thue_suat, 0 AS thue_gtgt, CAST('' AS VARCHAR(200)) AS ghi_chu, 3 AS nhom
            UNION ALL
            SELECT CAST(4 AS numeric) AS stt1, CAST('3. Hàng hóa, dịch vụ dùng cho dự án đầu tư đủ điều kiện được khấu trừ thuế' AS VARCHAR(200)) AS stt, CAST('' AS VARCHAR(200)) AS mau_so,
                CAST('' AS VARCHAR(200)) AS ky_hieu, CAST('' AS VARCHAR(200)) AS invoice_number,
                CAST (NULL AS date) AS ngay_hd, CAST('' AS VARCHAR(200)) AS ten_nguoi_ban, CAST('' AS VARCHAR(200)) AS mst, CAST('' AS VARCHAR(200)) AS mat_hang,
                0 AS doanh_so, CAST('' AS VARCHAR(200)) AS thue_suat, 0 AS thue_gtgt, CAST('' AS VARCHAR(200)) AS ghi_chu, 3 AS nhom
            UNION ALL
                SELECT CAST(5 AS numeric) AS stt1, CAST('' AS VARCHAR(200)) AS stt, CAST('' AS VARCHAR(200)) AS mau_so,
                CAST('' AS VARCHAR(200)) AS ky_hieu, CAST('' AS VARCHAR(200)) AS invoice_number,
                CAST (NULL AS date) AS ngay_hd, CAST('' AS VARCHAR(200)) AS ten_nguoi_ban, CAST('' AS VARCHAR(200)) AS mst, CAST('' AS VARCHAR(200)) AS mat_hang,
                0 AS doanh_so, CAST('' AS VARCHAR(200)) AS thue_suat, 0 AS thue_gtgt, CAST('' AS VARCHAR(200)) AS ghi_chu, 3 AS nhom
            UNION ALL
            SELECT CAST(6 AS numeric) AS stt1, CAST('Tổng' AS VARCHAR(200)) AS stt, CAST('' AS VARCHAR(200)) AS mau_so,
                CAST('' AS VARCHAR(200)) AS ky_hieu, CAST('' AS VARCHAR(200)) AS invoice_number,
                CAST (NULL AS date) AS ngay_hd, CAST('' AS VARCHAR(200)) AS ten_nguoi_ban, CAST('' AS VARCHAR(200)) AS mst, CAST('' AS VARCHAR(200)) AS mat_hang,
                0 AS doanh_so, CAST('' AS VARCHAR(200)) AS thue_suat, 0 AS thue_gtgt, CAST('' AS VARCHAR(200)) AS ghi_chu, 3 AS nhom
        ),
        ketqua AS (
            SELECT stt1, stt, mau_so, ky_hieu, invoice_number, ngay_hd, ten_nguoi_ban, mst, mat_hang, doanh_so, thue_suat, thue_gtgt, ghi_chu, nhom
            ,-1 as partner_id
            FROM tonghop
            UNION ALL
            SELECT stt1, CAST(stt1 AS VARCHAR(5)) AS stt, mau_so, ky_hieu, invoice_number, ngay_hd, ten_nguoi_ban, mst, mat_hang, doanh_so, thue_suat, thue_gtgt, ghi_chu, nhom
            ,partner_id
            FROM tonghop2
            UNION ALL
            SELECT stt1, stt, mau_so, ky_hieu, invoice_number, ngay_hd, ten_nguoi_ban, mst, mat_hang, doanh_so, thue_suat, thue_gtgt, ghi_chu, nhom
            ,-1 as partner_id
            FROM tonghop3
        )
        SELECT stt, mau_so, ky_hieu, invoice_number, to_char(ngay_hd, 'DD/MM/YYYY') AS ngay_hd, ten_nguoi_ban, mst, mat_hang, doanh_so, thue_suat, thue_gtgt, ghi_chu, nhom, partner_id  FROM ketqua
        ORDER BY nhom, stt1
        """.format(**kwargs)
        return sql

    def get_query_out(self, kwargs):
        sql = """
            WITH tonghop AS (
                        Select table1.*, CAST(ROW_NUMBER() OVER (PARTITION BY stt ORDER BY ngay_hd) AS numeric) AS stt1 FROM (
                                SELECT --inv.date_invoice as registration_date,
                                at.name AS stt,
                            CAST(mau.template_symbol AS VARCHAR(200)) AS mau_so, CAST(kyhieu.invoice_symbol AS VARCHAR(200)) AS ky_hieu,
                            CAST(inv.supplier_invoice_number AS VARCHAR(200)) AS invoice_number,
                            CAST(inv.date_invoice AS date) AS ngay_hd, 
                            inv.partner_id AS ten_nguoi_ban, CAST(partner.vat AS VARCHAR(200)) AS MST,
                    (SELECT name from account_invoice_line where invoice_id = inv.id limit 1) as mat_hang,
                            case when inv.type = 'out_refund' then tax.x_base*(-1) else tax.x_base end AS doanh_so,
                    CAST('' AS VARCHAR(200)) AS thue_suat,
            
                             --CASE WHEN inv_line.x_rounding_price_tax = 0 THEN inv_line.price_tax  ELSE  inv_line.x_rounding_price_tax END AS thue_gtgt,
                             case when inv.type = 'in_refund' then tax.amount*(-1) else tax.amount end as thue_gtgt,
                            CAST('' AS VARCHAR(200)) AS ghi_chu, 2 AS nhom, tax_group.sequence AS sequence
                            ,inv.partner_id as partner_id,
                            case when at.name like '%5%' then 5
                            when at.name like '%10%' then 10
                            when at.name like '%0%' then 0 end AS tax_gtgt
                        FROM account_invoice_tax AS tax LEFT JOIN
                            account_invoice AS inv ON tax.invoice_id = inv.id LEFT JOIN
                            --account_invoice_line inv_line ON inv.id = inv_line.invoice_id LEFT JOIN
                            res_partner AS par ON inv.partner_id = par.id --LEFT JOIN
                            --account_tax_code AS grouptax ON tax.base_code_id = grouptax.id
                            left join account_tax at on at.id = tax.tax_id
                            left join account_tax_group tax_group on tax_group.id = at.tax_group_id
                            left join res_partner partner on partner.id = inv.partner_id
                            left join account_invoicel_template mau on mau.id = inv.template_symbol
                            left join account_invoicel_symbol kyhieu on kyhieu.id = inv.invoice_symbol
                        WHERE (inv.state = 'paid' or inv.state = 'open') AND  (inv.type = 'out_invoice' or inv.type = 'out_refund')
                            AND inv.date_invoice BETWEEN '{start}' AND '{end}'
                            AND inv.company_id = '{company_id}'
                                union all
                                select --xtax.x_date_invoice as registration_date,
                                    tax.name AS stt,
                                    xtax.x_invoice_symbol AS mau_so,
                                    xtax.x_invoice_symbol AS ky_hieu,
                                    avl.x_supplier_invoice_number AS invoice_number,
                                    CAST(xtax.x_registration_date AS date) AS ngay_hd,
                                    xtax.x_partner_id AS ten_nguoi_ban,
                                    (CAST(partner.vat AS VARCHAR(200))) AS MST,
                        LTRIM(RTRIM(avl.name)) as mat_hang,
            
                                    sum(xtax.base) AS doanh_so,
                                    CAST('' AS VARCHAR(200)) AS thue_suat,
            
                                    sum(avl.x_rounding_price_tax) as thue_gtgt,
                                    CAST('' AS VARCHAR(200)) AS ghi_chu, 2 AS nhom, tax_group.sequence AS sequence,
                                    0 as partner_id,
                                    (case when xtax.name like '%5%' then 5
                                                    when xtax.name like '%10%' then 10
                                                    when xtax.name like '%0%' then 0 end) AS tax_gtgt
            
                                    from x_account_voucher_tax xtax
                                    join account_tax_account_voucher_line_rel rel on rel.account_voucher_line_id = xtax.voucher_line_id
            
                                    left join account_voucher_line avl on avl.id = rel.account_voucher_line_id
                                    left join account_voucher av on av.id = xtax.voucher_id
                                    left join account_journal aj on aj.id = av.journal_id
                                    left join res_partner partner on partner.id = xtax.x_partner_id
            
                                    join account_tax tax on tax.id = rel.account_tax_id
                                    left join account_tax_group tax_group on tax_group.id = tax.tax_group_id
                                    where av.voucher_type = 'sale'
                                    and av.state = 'posted'
                        and avl.company_id = '{company_id}'
                                    and xtax.x_date_invoice BETWEEN '{start}' AND '{end}'
                                    and (select count(id) from x_account_voucher_tax where voucher_id = av.id) > 0
                                    group by av.id, stt, mau_so, ky_hieu, invoice_number, ngay_hd, ten_nguoi_ban, mst,
                                    tax_gtgt, ghi_chu, nhom, partner_id, mat_hang, tax_group.sequence
                                    ) table1
                    ),
            
            
                    tonghop2 AS (
                        SELECT CAST(NULL AS numeric) AS stt1, CONCAT(CAST(tax_group.sequence AS VARCHAR(5)) , '.', ' ', tax_group.name) AS stt, CAST('' AS VARCHAR(200)) AS mau_so,
                            CAST('' AS VARCHAR(200)) AS ky_hieu, CAST('' AS VARCHAR(200)) AS invoice_number,
                            CAST (NULL AS date) AS ngay_hd, 0 AS ten_nguoi_ban, CAST('' AS VARCHAR(200)) AS mst, CAST('' AS VARCHAR(200)) AS mat_hang,
                            0 AS doanh_so, CAST('' AS VARCHAR(200)) AS thue_suat, 0 AS thue_gtgt, CAST('' AS VARCHAR(200)) AS ghi_chu, 1 AS nhom, tax_group.sequence
                            ,-1 as partner_id
                            FROM account_tax tax
                            left join account_tax_group tax_group on tax_group.id = tax.tax_group_id
                            WHERE type_tax_use = 'sale'
            
                            AND company_id = '{company_id}'
                    ),
            
                    tonghop3 AS (
                        SELECT CAST(NULL AS numeric) AS stt1, CONCAT(CAST('Tổng' AS VARCHAR(5))) AS stt, CAST('' AS VARCHAR(200)) AS mau_so,
                            CAST('' AS VARCHAR(200)) AS ky_hieu, CAST('' AS VARCHAR(200)) AS invoice_number,
                            CAST (NULL AS date) AS ngay_hd, 0 AS ten_nguoi_ban, CAST('' AS VARCHAR(200)) AS mst, CAST('' AS VARCHAR(200)) AS mat_hang,
                            0 AS doanh_so, CAST('' AS VARCHAR(200)) AS thue_suat, 0 AS thue_gtgt, CAST('' AS VARCHAR(200)) AS ghi_chu, 3 AS nhom, tax_group.sequence
                            ,-1 as partner_id
                            FROM account_tax tax
                            left join account_tax_group tax_group on tax_group.id = tax.tax_group_id
                            WHERE type_tax_use = 'sale'
            
                            AND company_id = '{company_id}'
                    ),
            
                    ketqua AS (
                        SELECT stt1, CAST(stt1 AS VARCHAR(5)) AS stt, mau_so, ky_hieu, invoice_number, ngay_hd, ten_nguoi_ban, mst, mat_hang, doanh_so, thue_suat, thue_gtgt, ghi_chu, nhom, sequence
                        ,partner_id,tax_gtgt
                        FROM tonghop
                        UNION ALL
                        SELECT stt1, stt, mau_so, ky_hieu, invoice_number, ngay_hd, ten_nguoi_ban, mst, mat_hang, doanh_so, thue_suat, thue_gtgt, ghi_chu, nhom, sequence
                        ,partner_id,-1 as tax_gtgt
                        FROM tonghop2
                        UNION ALL
                        SELECT stt1, stt, mau_so, ky_hieu, invoice_number, ngay_hd, ten_nguoi_ban, mst, mat_hang, doanh_so, thue_suat, thue_gtgt, ghi_chu, nhom, sequence
                        ,partner_id,-1 tax_gtgt
                        FROM tonghop3
                    )
            
                    SELECT stt, mau_so, ky_hieu, invoice_number, to_char(ngay_hd, 'DD/MM/YYYY') AS ngay_hd, ten_nguoi_ban, mst, mat_hang, doanh_so, thue_gtgt, ghi_chu, nhom,partner_id,tax_gtgt FROM ketqua
                    ORDER BY sequence, nhom, stt1


        """.format(**kwargs)
        return sql


TaxInOutReport('report.btek_tax_report.tax_in_out_report', 'tax.in.out.report')