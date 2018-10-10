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
from dateutil.relativedelta import relativedelta


class btek_balance_sheet(models.TransientModel):
    _name = "to.balance.sheet"
    _inherit = "to.account.common.report"
    _description = "Balance Sheet Report"

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    res_company_id = fields.Many2one('res.company', required=True, default=_get_company)
    data = fields.Binary('File', readonly=True)
    name = fields.Char('Filename', readonly=True)
    # chart_account_id = fields.Many2one('account.account',string='Account Account', required=True)


    @api.model
    @api.onchange('date_to')
    def onchange_end_date(self):
        if self.date_from > self.date_to:
            self.date_to = self.date_from

    @api.model
    def _get_opening_balance(self, opening_time, account_id):
        if opening_time:
            # KhanhTD Yeu cau tru di 1 nam tai chinh
            year = opening_time
            opening_time = str(int(year[:4]) - 1) + ('-01-01')
            close_time = str(int(year[:4]) - 1) + ('-12-31')
        sql = """
            SELECT 
                SUM(((SELECT SUM(debit)
                    FROM account_move_line l
                    JOIN account_move am ON (am.id=l.move_id)
                    WHERE l.account_id = C.id AND am.state='posted'
                    AND am.date BETWEEN '%s'::date AND '%s'::date
                    )
                -
                (SELECT SUM(credit)
                    FROM account_move_line l
                    JOIN account_move am ON (am.id=l.move_id)
                    WHERE l.account_id = C.id AND am.state='posted'
                    AND am.date BETWEEN '%s'::date AND '%s'::date
                    )
                    )) AS opening_balance
            FROM account_account P, account_account C
            WHERE P.parent_left <= C.parent_left
            AND P.parent_right >= C.parent_right            
            AND ((C.id IN (SELECT account_id 
                    FROM account_move_line l
                    JOIN account_move am ON (am.id=l.move_id)
                    WHERE am.state='posted' AND am.date BETWEEN '%s'::date AND '%s'::date))
                 OR (P.id IN (SELECT account_id 
                    FROM account_move_line l
                    JOIN account_move am ON (am.id=l.move_id)
                    WHERE  am.state='posted' AND am.date BETWEEN '%s'::date AND '%s'::date)))
            AND P.id IN (%s)
            """ % (opening_time, close_time, opening_time, close_time, opening_time, close_time, opening_time, close_time, account_id)
        self._cr.execute(sql)
        res = self._cr.fetchone()[0] or 0
        return res

    @api.model
    def _get_previous_value(self, item, data):
        value = 0
        account_obj = self.env['account.account']
        # chart_of_account = account_obj.browse(data['form']['chart_account_id'])
        company_id = self.env.user.company_id.id

        if item.type == 'sum':
            for children in item.children_ids:
                value += self._get_previous_value(children, data)
        else:
            for included_account_id in item.to_included_accounts:
                if included_account_id.account_id:
                    res = self._get_opening_balance(data['form']['date_from'],
                                                    included_account_id.account_id.id)
                    if item.to_code == '421' or item.to_code == '412' or item.to_code == '416' or item.to_code == '417' or item.to_code == '421a' or item.to_code == '421b':
                        if res < 0:
                            value += abs(res)
                        elif res > 0:
                            value += res * -1
                    else:
                        if item.to_balance_type == 'db':
                            if res > 0:
                                value += res
                        elif item.to_balance_type == 'cr':
                            if res < 0:
                                value += abs(res)
            if item.to_code == '241':
                account_22942 = account_obj.search(
                    [('code', '=', '22942'), ('company_id', '=', company_id)])
                if account_22942:
                    opening_account_22942 = self._get_opening_balance(data['form']['date_from'],
                                                                      account_22942.id)
                    if opening_account_22942 < 0:
                        value += opening_account_22942
            if item.to_code == '263':
                account_22943 = account_obj.search(
                    [('code', '=', '22943'), ('company_id', '=', company_id)])
                if account_22943:
                    opening_account_22943 = self._get_opening_balance(data['form']['date_from'],
                                                                      account_22943.id)
                    if opening_account_22943 < 0:
                        value += opening_account_22943
            if item.to_code == '338':
                account_34312 = account_obj.search(
                    [('code', '=', '34312'), ('company_id', '=', company_id)])
                if account_34312:
                    opening_account_34312 = self._get_opening_balance(data['form']['date_from'],
                                                                      account_34312.id)
                    if opening_account_34312 > 0:
                        value -= opening_account_34312
            if item.to_code == '431':
                account_461 = account_obj.search(
                    [('code', '=', '461'), ('company_id', '=', company_id)])
                if account_461:
                    opening_account_461 = self._get_opening_balance(data['form']['date_from'],
                                                                    account_461.id)
                    if opening_account_461 < 0:
                        value += abs(opening_account_461)
                account_161 = account_obj.search(
                    [('code', '=', '161'), ('company_id', '=', company_id)])
                if account_161:
                    opening_account_161 = self._get_opening_balance(data['form']['date_from'],
                                                                    account_161.id)
                    if opening_account_161 > 0:
                        value -= opening_account_461

        if value == 0:
            return value
        else:
            return value * item.sign

    @api.model
    def _get_current_value(self, item, data):
        fs_filter = 'filter_date'
        account_obj = self.env['account.account']
        # chart_of_account = account_obj.browse(data['form']['chart_account_id'])
        company_id = self.env.user.company_id.id

        value = 0
        if item.type == 'sum':
            for children in item.children_ids:
                value += self._get_current_value(children, data)
        else:
            for account in account_obj.browse([x.account_id.id for x in item.to_included_accounts]):
                if account.id:
                    opening_balance = 0
                    for acc in account.get_report_children_account_ids():
                        opening_balance += account_obj._report_opening_balance_for_type(acc, data, item.to_balance_type)
                    if item.to_code == '421' or item.to_code == '412' or item.to_code == '416' or item.to_code == '417' or item.to_code == '421a' or item.to_code == '421b':
                        if opening_balance < 0:
                            value += abs(opening_balance)
                        elif opening_balance > 0:
                            value += (opening_balance) * -1
                    else:
                        if item.to_balance_type == 'db':
                            if opening_balance > 0:
                                value += opening_balance
                        elif item.to_balance_type == 'cr':
                            if opening_balance < 0:
                                value += abs(opening_balance)
                        elif item.to_balance_type == 'bl':
                            value += opening_balance

            if item.to_code == '338':
                account_34312 = account_obj.search(
                    [('code', '=', '34312'), ('company_id', '=', company_id)])
                if account_34312:
                    opening_balance_34312 = 0
                    for acc in account_34312.get_report_children_account_ids():
                        opening_balance_34312 += account_obj._report_opening_balance_for_type(acc, data,item.to_balance_type)
                    if opening_balance_34312 > 0:
                        value -= opening_balance_34312
            if item.to_code == '241':
                account_22942 = account_obj.search(
                    [('code', '=', '22942'), ('company_id', '=', company_id)])
                if account_22942:
                    opening_balance_22942 = account_obj._report_opening_balance_for_type(account_22942[0], data,item.to_balance_type)
                    if opening_balance_22942 < 0:
                        value += opening_balance_22942
            if item.to_code == '263':
                account_22943 = account_obj.search(
                    [('code', '=', '22943'), ('company_id', '=', company_id)])
                if account_22943:
                    opening_balance_22943 = account_obj._report_opening_balance_for_type(account_22943[0], data, data,item.to_balance_type)
                    if opening_balance_22943 < 0:
                        value += opening_balance_22943
            if item.to_code == '431':
                account_461 = account_obj.search([('code', '=', '461'), ('company_id', '=', company_id)])
                if account_461:
                    balance_461 = account_obj._report_opening_balance_for_type(account_461[0], data, data, 'bl')
                    if balance_461 < 0:
                        value += abs(balance_461)
                account_161 = account_obj.search(
                    [('code', '=', '161'), ('company_id', '=', company_id)])
                if account_161:
                    balance_161 = account_obj._report_opening_balance_for_type(account_161[0], data, data, 'bl')
                    if balance_161 > 0:
                        value -= balance_161

        if value == 0:
            return value
        else:
            return value * item.sign

    @api.model
    def lines(self, data):
        """
        Return records of account.financial.report
        :param dict data: data of report wizard form
        """
        self = self.with_context(data['form'].get('used_context', {}))
        res_line = []
        to_decision = data['form']['to_decision']
        to_report_type = data['form']['to_report_type']
        fs_config_obj = self.env['account.financial.report']
        fs_config = fs_config_obj.search(
            [('to_financial_statement', '=', to_report_type), ('to_decision', '=', to_decision)])
        for item in fs_config:
            current_value = self._get_current_value(item, data)
            previous_value = self._get_previous_value(item, data)
            res_line.append({
                'name': item.name,
                'code': item.to_code,
                'notes': item.to_notes,
                'level': bool(item.style_overwrite) and item.style_overwrite or item.level,
                'current_value': current_value,
                'previous_value': previous_value,
            })
        return res_line


    def print_excel(self):
        return self.env['report'].get_action(self, 'btek_financial_report.bs_report')

    @api.multi
    def preview_excel(self):
        datas = {'ids': self.ids}
        datas['model'] = self._name

        report_name = 'btek_financial_report.bs_report'
        res = self.env['ir.actions.report.xml'
        ].preview_xlsx_report(report_name, self._ids, datas)
        return res


class BalanceSheetReport(ReportXlsx):
    _name = 'report.btek_financial_report.bs_report'

    def write_bs_report(self, ws, data, form):
        ws.set_column(0, 0, 14)  # Ma TK
        ws.set_column(1, 1, 10)
        ws.set_column(2, 2, 30)  # Dien giai
        ws.set_column(3, 3, 10)  # Name
        ws.set_column(4, 4, 8)  # Ma so
        ws.set_column(5, 5, 13)  # Thuyet minh
        ws.set_column(6, 6, 12)  # nam nay
        ws.set_column(7, 7, 10)  # Co
        ws.set_column(8, 8, 12)  # nam truoc
        ws.set_column(9, 9, 10)  # Co

        address = ''
        if form.res_company_id.street: address = form.res_company_id.street
        if form.res_company_id.street2: address = address + ', ' + form.res_company_id.street2
        if form.res_company_id.city: address = address + ', ' + form.res_company_id.city
        if form.res_company_id.country_id.name: address = address + ', ' + form.res_company_id.country_id.name
        mst = form.res_company_id.vat

        start = form.date_from
        end = form.date_to

        # Header
        ws.write("A1", u'Đơn vị báo cáo :', )
        ws.write("A2", u'Địa chỉ :', )
        ws.write("A4", u'MST :', )
        ws.merge_range("B1:E1", unicode(form.res_company_id.name) or '', self.bold)
        ws.merge_range("B2:E3", unicode(address) or '', self.bold)
        ws.merge_range("B4:C4", mst or '', self.bold)
        ws.set_row(5, 28)
        ws.merge_range("A6:J6", u"BẢNG CÂN ĐỐI KẾ TOÁN", self.title)
        ws.set_row(7, 18)  # Set the height of Row 1 to 20.
        ws.set_row(8, 18)
        ws.set_row(9, 18)
        ws.set_row(10, 22)
        ws.set_row(11, 22)
        ws.set_row(12, 22)
        if start and end:
            start_view = datetime.datetime.strptime(start, '%Y-%m-%d').strftime('%d/%m/%Y').decode('unicode-escape')
            end_view = datetime.datetime.strptime(end, '%Y-%m-%d').strftime('%d/%m/%Y').decode('unicode-escape')
            ws.merge_range("A7:J7", u" Từ ngày: " + start_view + u" đến ngày: " + end_view + u"", self.italic)
        ws.merge_range("I8:J8", u'Đơn vị tính: ' + form.res_company_id.currency_id.name, self.italic)
        row_num = 9

        ws.merge_range("A{row}:D{row}".format(row=row_num), u'Chỉ tiêu', self.table_header)
        ws.write('E{row_num}'.format(row_num=row_num), u'Mã', self.table_header)
        ws.write('F{row_num}'.format(row_num=row_num), u'Thuyết minh', self.table_header)
        ws.merge_range("G{row}:H{row}".format(row=row_num), u'Số năm nay', self.table_header)
        ws.merge_range("I{row}:J{row}".format(row=row_num), u'Số năm trước', self.table_header)

        row_num += 1
        ws.merge_range("A{row}:D{row}".format(row=row_num), u'A', self.table_header)
        ws.write('E{row_num}'.format(row_num=row_num), u'B', self.table_header)
        ws.write('F{row_num}'.format(row_num=row_num), u'C', self.table_header)
        ws.merge_range("G{row}:H{row}".format(row=row_num), u'1', self.table_header)
        ws.merge_range("I{row}:J{row}".format(row=row_num), u'2', self.table_header)

        row_num += 1
        if data:
            for r in data:
                if r['level'] == 3:
                    if len(r['name']) > 65:
                        ws.set_row(row_num - 1, 40)
                        ws.merge_range("A{row}:D{row}".format(row=row_num), r['name'] or '', self.table_row_left_bold)
                    else:
                        ws.set_row(row_num - 1, 24)
                        ws.merge_range("A{row}:D{row}".format(row=row_num), r['name'] or '', self.table_row_left_bold)
                    ws.write("E{row}".format(row=row_num), r['code'] or '', self.table_row_center_bold)
                    ws.write("F{row}".format(row=row_num), r['notes'] or '', self.table_row_center_bold)
                    ws.merge_range("G{row}:H{row}".format(row=row_num), r['current_value'] < 0 and (
                '( ' + '{:20,.2f}'.format(-r['current_value']) + ' )') or (r['current_value'] or 0.0),
                                   self.table_row_right_bold)
                    ws.merge_range("I{row}:J{row}".format(row=row_num), r['previous_value'] < 0 and (
                '( ' + '{:20,.2f}'.format(-r['current_value']) + ' )') or (r['previous_value'] or 0.0),
                                   self.table_row_right_bold)
                else:
                    ws.merge_range("A{row}:D{row}".format(row=row_num), r['name'] or '', self.row_left)
                    ws.write("E{row}".format(row=row_num), r['code'] or '', self.row_center)
                    ws.write("F{row}".format(row=row_num), r['notes'] or '', self.row_center)
                    ws.merge_range("G{row}:H{row}".format(row=row_num), r['current_value'] < 0 and (
                    '( ' + '{:20,.2f}'.format(-r['current_value']) + ' )') or (r['current_value'] or 0.0), self.row_right)
                    ws.merge_range("I{row}:J{row}".format(row=row_num), r['previous_value'] < 0 and (
                    '( ' + '{:20,.2f}'.format(-r['current_value']) + ' )') or (r['previous_value'] or 0.0), self.row_right)
                row_num += 1

        row_num += 1
        ws.merge_range('A{row}:B{row}'.format(row=row_num + 1), u'Người lập biểu', self.row_center_footer)
        ws.merge_range('A{row}:B{row}'.format(row=row_num + 2), u'(Ký, họ tên)', self.italic)
        ws.merge_range('C{row}:F{row}'.format(row=row_num + 1), u'Kế toán trưởng', self.row_center_footer)
        ws.merge_range('C{row}:F{row}'.format(row=row_num + 2), u'(Ký, họ tên)', self.italic)
        ws.merge_range('G{row}:I{row}'.format(row=row_num), u'Lập ngày ..... tháng..... năm .....', self.italic)
        ws.merge_range('G{row}:I{row}'.format(row=row_num + 1), u'Giám đốc', self.row_center_footer)
        ws.merge_range('G{row}:I{row}'.format(row=row_num + 2), u'(Ký, họ tên, đóng dấu)', self.italic)

    def generate_xlsx_report(self, wb, data, form):
        reports = {
            'report': self.write_bs_report,
        }
        ws = wb.add_worksheet('Balance Sheet Report')
        wb.formats[0].font_name = 'Times New Roman'
        wb.formats[0].font_size = 12
        ws.set_paper(9)
        ws.set_margins(left=0.28, right=0.28, top=0.5, bottom=0.5)
        ws.fit_to_pages(1, 0)  # -- 1 page wide and as long as necessary.
        ws.set_portrait()
        ws.repeat_rows(10, 11)  # Repeat the first two rows.

        #         Style
        self.bold_right_big = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'align': 'right',
            'valign': 'vcenter',
            'font_name': 'Times New Roman',
        })
        self.bold = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'valign': 'vcenter',
            'font_name': 'Times New Roman',
        })
        self.right = wb.add_format({
            'text_wrap': 1,
            'align': 'right',
            'text_wrap': 1,
            'valign': 'vcenter',
            'num_format': '#,##0.00',
            'font_name': 'Times New Roman',
        })
        self.footer_bold = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'align': 'left',
            'valign': 'vcenter',
            'num_format': '#,##0',
            'font_name': 'Times New Roman',
        })
        self.center = wb.add_format({
            'text_wrap': 1,
            'align': 'center',
            'text_wrap': 1,
            'valign': 'vcenter',
            'font_name': 'Times New Roman',
        })
        self.center_bold = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'align': 'center',
            'text_wrap': 1,
            'valign': 'vcenter',
            'font_name': 'Times New Roman',
        })
        self.title = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_size': 22,
            'font_name': 'Times New Roman',
        })
        self.left = wb.add_format({
            'text_wrap': 1,
            'align': 'left',
            'text_wrap': 1,
            'valign': 'vcenter',
            'font_name': 'Times New Roman',
        })

        self.italic = wb.add_format({
            'italic': 1,
            'text_wrap': 1,
            'align': 'left',
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_name': 'Times New Roman',
        })

        self.table_header = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'fg_color': '#d8d8d8',
            'font_name': 'Times New Roman',
        })

        self.table_row_center = wb.add_format({
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'font_name': 'Times New Roman',
        })

        self.table_row_left = wb.add_format({
            'text_wrap': 1,
            'font_size': 14,
            'align': 'left',
            'valign': 'vcenter',
            'border': 1,
            'font_name': 'Times New Roman',
        })

        self.table_row_right = wb.add_format({
            'text_wrap': 1,
            'border': 1,
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
            'num_format': '#,##0',
            'font_name': 'Times New Roman',
        })

        self.row_center = wb.add_format({
            'text_wrap': 1,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter',
            'font_name': 'Times New Roman',
        })
        self.row_center.set_right(1)
        self.row_center.set_bottom(1)

        self.row_left = wb.add_format({
            'text_wrap': 1,
            'border': 1,
            'font_size': 14,
            'align': 'left',
            'valign': 'vcenter',
            'font_name': 'Times New Roman',
        })
        self.row_left.set_right(1)
        self.row_left.set_left(1)
        self.row_left.set_bottom(1)

        self.row_left_bold = wb.add_format({
            'text_wrap': 1,
            'bold': 1,
            'border': 1,
            'align': 'left',
            'valign': 'vcenter',
            'font_name': 'Times New Roman',
        })
        self.row_left_bold.set_right(1)
        self.row_left_bold.set_left(1)
        self.row_left_bold.set_bottom(4)

        self.row_left_italic = wb.add_format({
            'text_wrap': 1,
            'border': 1,
            'italic': 1,
            'align': 'left',
            'valign': 'vcenter',
            'font_name': 'Times New Roman',
        })
        self.row_left_italic.set_right(1)
        self.row_left_italic.set_left(1)
        self.row_left_italic.set_bottom(4)

        self.row_center_boldleft = wb.add_format({
            'text_wrap': 1,
            'align': 'left',
            'valign': 'vcenter',
            'font_name': 'Times New Roman',
        })
        self.row_center_boldleft.set_right(1)
        self.row_center_boldleft.set_left(1)
        self.row_center_boldleft.set_bottom(4)

        self.row_center_footer = wb.add_format({
            'text_wrap': 1,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter',
            'font_name': 'Times New Roman',
        })

        self.row_right = wb.add_format({
            'text_wrap': 1,
            'border': 1,
            'font_size': 14,
            'align': 'right',
            'valign': 'vcenter',
            'num_format': '#,##0.00',
            'font_name': 'Times New Roman',
        })

        self.row_right.set_right(1)
        self.row_right.set_left(1)
        self.row_right.set_bottom(1)

        self.table_row_right_bold = wb.add_format({
            'text_wrap': 1,
            'bold': 1,
            'border': 1,
            'font_size': 14,
            'align': 'right',
            'valign': 'vcenter',
            'num_format': '#,##0.00',
            'font_name': 'Times New Roman',
        })
        self.table_row_right_bold.set_right(1)
        self.table_row_right_bold.set_left(1)
        self.table_row_right_bold.set_bottom(1)

        self.table_row_center_bold = wb.add_format({
            'text_wrap': 1,
            'bold': 1,
            'border': 1,
            'font_size': 14,
            'align': 'center',
            'valign': 'vcenter',
            'num_format': '#,##0',
            'font_name': 'Times New Roman',
        })
        self.table_row_center_bold.set_right(1)
        self.table_row_center_bold.set_left(1)
        self.table_row_center_bold.set_bottom(1)

        self.table_row_left_bold = wb.add_format({
            'text_wrap': 1,
            'bold': 1,
            'border': 1,
            'font_size': 14,
            'align': 'left',
            'valign': 'vcenter',
            'num_format': '#,##0',
            'font_name': 'Times New Roman',
        })

        args = {
            'start': form.date_from,
            'end': form.date_to,
            'company_id': form.res_company_id.id,
        }
        report_data = self.get_data(form)
        reports['report'](ws, report_data, form)

    def get_data(self, form):
        data = {}
        data['ids'] = form.env.context.get('active_ids', [])
        data['model'] = form.env.context.get('active_model', 'ir.ui.menu')
        data['form'] = form.read(['date_from', 'date_to', 'journal_ids',
                                  'target_move', 'to_report_type', 'to_decision'])[0]
        used_context = form._build_contexts(data)
        data['form']['used_context'] = dict(used_context, lang=form.env.context.get('lang', 'en_US'))
        rp_data = form.lines(data)
        return rp_data


BalanceSheetReport('report.btek_financial_report.bs_report', 'to.balance.sheet')
