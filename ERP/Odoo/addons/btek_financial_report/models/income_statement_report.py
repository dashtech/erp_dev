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
from odoo.exceptions import UserError
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
from dateutil.relativedelta import relativedelta


class btek_income_statement(models.Model):
    _name = "to.income.statement"
    _inherit = "to.account.common.report"
    _description = "Income Statement Report"

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    @api.model
    def _get_date_from(self):
        return datetime.date(datetime.date.today().year, datetime.date.today().month, 1)

    date_from = fields.Date(default=_get_date_from)
    date_to = fields.Date(default=fields.Date.today)
    res_company_id = fields.Many2one('res.company', required=True, default=_get_company)
    data = fields.Binary('File', readonly=True)
    name = fields.Char('Filename', readonly=True)

    @api.model
    @api.onchange('date_to')
    def onchange_end_date(self):
        if self.date_from > self.date_to:
            self.date_to = self.date_from

    @api.model
    def __get_value(self, item, where_query):
        included_account_ids = item._get_included_account_ids()
        counterpart_account_ids = item._get_counterpart_accounts_ids()
        if included_account_ids and not counterpart_account_ids:
            sql = """
               SELECT SUM(%s) FROM account_move_line l
               WHERE account_id IN (%s)
               AND %s
               """ % (item.to_balance_type == 'cr' and 'credit' or 'debit', included_account_ids, where_query)
        elif included_account_ids and counterpart_account_ids:
            sql = """
               SELECT SUM(%s) FROM account_move_line l
               WHERE account_id IN (%s)
               AND move_id IN (SELECT move_id FROM account_move_line WHERE account_id in(%s))
               AND %s
               """ % (
            item.to_balance_type == 'cr' and 'credit' or 'debit', included_account_ids, counterpart_account_ids,
            where_query)
        if not included_account_ids:
            raise UserError(_(u'Lỗi: Chỉ tiêu "{}" cấu hình thiếu!').format(item.name))
        if sql:
            self._cr.execute(sql)
        return self._cr.fetchone()[0] or 0

    @api.model
    def _get_previous_value(self, item, date_from):
        value = 0
        if item.type == 'sum':
            for r in item.children_ids:
                value += self._get_previous_value(r, date_from)
        else:
            start_period = datetime.datetime((datetime.date.today() - relativedelta(years=1)).year, 1, 1)
            where_query = "date < date('%s') and date >= date('%s')"%(date_from, start_period)
            value = self.__get_value(item, where_query)
        if value == 0:
            return value
        else:
            return value * item.sign

    @api.model
    def _get_current_value(self, item, date_from, date_to):
        value = 0
        if item.type == 'sum':
            for r in item.children_ids:
                value += self._get_current_value(r, date_from, date_to)
        else:
            obj_move = self.env['account.move.line']
            where_query = "date <= date('%s') and date >= date('%s')"%(date_to, date_from)
            value = self.__get_value(item, where_query)

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
        res_line = []
        to_decision = data['form']['to_decision']
        to_report_type = data['form']['to_report_type']
        fs_config_obj = self.env['account.financial.report']
        date_from = data['form']['date_from']
        date_to = data['form']['date_to']
        fs_config = fs_config_obj.search(
            [('to_financial_statement', '=', to_report_type), ('to_decision', '=', to_decision)])
        for item in fs_config:
            if date_from and date_to:
                current_value = self._get_current_value(item, date_from, date_to)
                previous_value = self._get_previous_value(item, date_from)
                res_line.append({
                    'name': item.name,
                    'code': item.to_code,
                    'notes': item.to_notes,
                    'level': bool(item.style_overwrite) and item.style_overwrite or item.level,
                    'current_value': current_value if item.to_code in ('10', '20', '30', '40', '50', '60') else abs(
                        current_value),
                    'previous_value': previous_value if item.to_code in ('10', '20', '30', '40', '50', '60') else abs(
                        previous_value),
                })

        return res_line

    def print_excel(self):
        return self.env['report'].get_action(self, 'btek_financial_report.is_report')

    @api.multi
    def preview_excel(self):
        datas = {'ids': self.ids}
        datas['model'] = self._name

        report_name = 'btek_financial_report.is_report'
        res = self.env['ir.actions.report.xml'
        ].preview_xlsx_report(report_name, self._ids, datas)
        return res


class IncomeStatementReport(ReportXlsx):
    _name = 'report.btek_financial_report.is_report'

    def write_is_report(self, ws, data, form):
        ws.set_column(0, 0, 70)  # Chỉ tiêu
        ws.set_column(1, 1, 8)  # Mã
        ws.set_column(2, 2, 15)  # Thuyết minh
        ws.set_column(3, 3, 20)  # Số năm nay
        ws.set_column(4, 4, 20)  # Số năm trước

        address = ''
        if form.res_company_id.street: address = form.res_company_id.street
        if form.res_company_id.street2: address = address + ', ' + form.res_company_id.street2
        if form.res_company_id.city: address = address + ', ' + form.res_company_id.city
        if form.res_company_id.country_id.name: address = address + ', ' + form.res_company_id.country_id.name
        mst = ''
        if form.res_company_id.vat:
            mst = form.res_company_id.vat

        start = form.date_from
        end = form.date_to

        # Header
        ws.merge_range('A1:A5', u'Đơn vị báo cáo: ' + unicode(form.res_company_id.name) + u'\nĐịa chỉ: ' +
                       unicode(address) + u'\nMST: ' +
                       mst , self.header_report_style)
        ws.merge_range("D1:E4", u"Mẫu B02-DN\n" + u"(Ban hành theo TT số 200/2014/TT-BTC\n" + u"Ngày 22/12/2014 của Bộ tài chính)", self.header_report_style)
        string_lable = u'BÁO CÁO KẾT QUẢ HOẠT ĐỘNG KINH DOANH'
        ws.merge_range("B6:D7", string_lable, self.title_report_style)
        if start and end:
            start_view = datetime.datetime.strptime(start, '%Y-%m-%d').strftime('%d/%m/%Y').decode('unicode-escape')
            end_view = datetime.datetime.strptime(end, '%Y-%m-%d').strftime('%d/%m/%Y').decode('unicode-escape')
            ws.merge_range("B8:D8", u" Từ ngày: " + start_view + u" đến ngày: " + end_view + u"", self.row_italic_left)
        ws.write('E9', u'Đơn vị tính: ' + form.res_company_id.currency_id.name, self.row_italic_right)
        row_num = 10
        ws.write('A{row_num}'.format(row_num=row_num), u'Chỉ tiêu', self.table_header)
        ws.write('B{row_num}'.format(row_num=row_num), u'Mã', self.table_header)
        ws.write('C{row_num}'.format(row_num=row_num), u'Thuyết minh', self.table_header)
        ws.write('D{row_num}'.format(row_num=row_num), u'Số năm nay', self.table_header)
        ws.write('E{row_num}'.format(row_num=row_num), u'Số năm trước', self.table_header)

        row_num += 1
        ws.write('A{row_num}'.format(row_num=row_num), u'A', self.table_header)
        ws.write('B{row_num}'.format(row_num=row_num), u'B', self.table_header)
        ws.write('C{row_num}'.format(row_num=row_num), u'C', self.table_header)
        ws.write('D{row_num}'.format(row_num=row_num), u'1', self.table_header)
        ws.write('E{row_num}'.format(row_num=row_num), u'2', self.table_header)

        row_num += 1
        if data:
            for line in data:
                if line['code'] in ['10', '20', '30', '40', '50', '60']:
                    left_style = self.row_default_left_bold
                    default_style = self.row_default_bold
                    money_style = self.row_default_right_money_bold
                else:
                    left_style = self.row_default_left
                    default_style = self.row_default
                    money_style = self.row_default_right_money
                notes = line['notes'] or ''
                ws.write("A{row}".format(row=row_num), line['name'], left_style)
                ws.write("B{row}".format(row=row_num), line['code'], default_style)
                ws.write("C{row}".format(row=row_num), notes, default_style)

                # current_value = line['current_value']
                current_value = str('{:,.2f}'.format(line['current_value'])).replace('.', '*').replace(',', '.').replace(
                    '*', ',')
                if line['current_value'] < 0:
                    current_value = line['current_value'] * (-1)
                    current_value = str('{:,.2f}'.format(current_value))
                    current_value = current_value.replace('.', '*').replace(',', '.').replace('*', ',')
                    current_value = '(' + current_value + ')'
                    # current_value = '(' + current_value.replace('.','*').replace(',','.').replace('*',',') + ')'
                ws.write("D{row}".format(row=row_num), current_value, money_style)

                # previous_value = line['previous_value']
                previous_value = str('{:,.2f}'.format(line['previous_value'])).replace('.', '*').replace(',', '.').replace(
                    '*', ',')
                if line['previous_value'] < 0:
                    previous_value = line['previous_value'] * (-1)
                    previous_value = str('{:,.2f}'.format(previous_value))
                    previous_value = previous_value.replace('.', '*').replace(',', '.').replace('*', ',')
                    previous_value = '(' + previous_value + ')'
                ws.write("E{row}".format(row=row_num), previous_value, money_style)
                row_num += 1

            row_num += 1
            ws.write('A{row}'.format(row=row_num + 1), u'Người lập biểu', self.row_footer_bold)
            ws.write('A{row}'.format(row=row_num + 2), u'(Ký, họ tên)', self.row_italic)
            ws.merge_range('B{row}:C{row}'.format(row=row_num + 1), u'Kế toán trưởng', self.row_footer_bold)
            ws.merge_range('B{row}:C{row}'.format(row=row_num + 2), u'(Ký, họ tên)', self.row_italic)
            ws.merge_range('D{row}:E{row}'.format(row=row_num), u'Lập ngày ..... tháng..... năm .....', self.row_italic)
            ws.merge_range('D{row}:E{row}'.format(row=row_num + 1), u'Giám đốc', self.row_footer_bold)
            ws.merge_range('D{row}:E{row}'.format(row=row_num + 2), u'(Ký, họ tên, đóng dấu)', self.row_italic)

    def generate_xlsx_report(self, wb, data, form):
        reports = {
            'report': self.write_is_report,
        }
        ws = wb.add_worksheet('Income Statement Report')
        wb.formats[0].font_name = 'Times New Roman'
        wb.formats[0].font_size = 12
        ws.set_paper(9)
        ws.set_margins(left=0.28, right=0.28, top=0.5, bottom=0.5)
        ws.fit_to_pages(1, 0)  # -- 1 page wide and as long as necessary.
        ws.set_portrait()
        ws.repeat_rows(10, 11)  # Repeat the first two rows.

        #         Style
        self.title_report_style = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_name': 'Times New Roman',
            'font_size': 15,
        })
        self.header_report_style = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'align': 'left',
            'valign': 'vcenter',
            'font_name': 'Times New Roman',
            'font_size': 12,
        })
        self.table_header = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'fg_color': '#d8d8d8',
            'font_name': 'Times New Roman',
        })
        self.row_default = wb.add_format({
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'font_name': 'Times New Roman',
        })
        self.row_default_bold = wb.add_format({
            'text_wrap': 1,
            'bold': 1,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'font_name': 'Times New Roman',
        })
        self.row_default_left = wb.add_format({
            'text_wrap': 1,
            'align': 'left',
            'valign': 'vcenter',
            'border': 1,
            'font_name': 'Times New Roman',
        })
        self.row_default_left_bold = wb.add_format({
            'text_wrap': 1,
            'bold': 1,
            'align': 'left',
            'valign': 'vcenter',
            'border': 1,
            'font_name': 'Times New Roman',
        })
        self.row_default_right_qty = wb.add_format({
            'text_wrap': 1,
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
            'font_name': 'Times New Roman',
            'num_format': '#,##0',
        })
        self.row_default_right_money = wb.add_format({
            'text_wrap': 1,
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
            'font_name': 'Times New Roman',
            'num_format': '#,##0.00',
        })
        self.row_default_right_money_bold = wb.add_format({
            'text_wrap': 1,
            'align': 'right',
            'valign': 'vcenter',
            'bold': 1,
            'border': 1,
            'font_name': 'Times New Roman',
            'num_format': '#,##0.00',
        })
        self.row_last_total = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
            'font_name': 'Times New Roman',
            'font_size': 12,
            'num_format': '#,##0.00',
        })
        self.row_footer_default = wb.add_format({
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_name': 'Times New Roman',
        })
        self.row_footer_bold = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_name': 'Times New Roman',
        })
        self.row_italic = wb.add_format({
            'italic': 1,
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            'font_name': 'Times New Roman',
        })
        self.title_bold = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'align': 'left',
            'valign': 'vcenter',
            'font_name': 'Times New Roman',
        })
        self.right_header = wb.add_format({
            'bold': 0,
            'text_wrap': 1,
            'align': 'left',
            'valign': 'top',
            'font_name': 'Times New Roman',
        })
        self.row_italic_left = wb.add_format({
            'italic': 1,
            'text_wrap': 1,
            'align': 'left',
            'valign': 'vcenter',
            'font_name': 'Times New Roman',
        })
        self.row_italic_right = wb.add_format({
            'italic': 1,
            'text_wrap': 1,
            'align': 'right',
            'valign': 'vcenter',
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




IncomeStatementReport('report.btek_financial_report.is_report', 'to.income.statement')
