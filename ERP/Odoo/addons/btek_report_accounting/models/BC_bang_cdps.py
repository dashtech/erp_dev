# -*- coding: utf-8 -*-
from xlrd import sheet

from odoo import api, fields, models, _
import xlwt
from xlwt import Formula
from xlsxwriter.workbook import Workbook
import datetime
import base64
import cStringIO
from  calendar import monthrange
from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx


class btek_bang_can_doi_ps(models.TransientModel):
    _name = 'bang.can.doi.phat.sinh'

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

    company_id = fields.Many2one('res.company', required=True, default=_get_company)
    type_entries = fields.Selection([('filter_posted', 'All Post Entries'), ('filter_all', 'All Entries')], "Type",
                                    default='filter_posted', required=True)

    display_account = fields.Selection([('all', 'All'), ('movement', 'With movements'),
                                        ('not_zero', 'With balance is not equal to 0'), ],
                                       string='Display Accounts', required=True, default='movement')

    def process_balance(self, balance_dict):
        account_s = self.env['account.account'].search([])
        account_code_dict = \
            dict((account.id, account.code) for account in account_s)

        for account_id in balance_dict:
            credit = balance_dict[account_id]['credit'] or 0
            debit = balance_dict[account_id]['debit'] or 0

            account_code = account_code_dict.get(account_id, '')
            if not account_code:
                continue

            if account_code == '131':
                continue

            if account_code.startswith('1311') \
                    or account_code.startswith('3312'):
                balance_dict[account_id]['debit'] = debit - credit
                balance_dict[account_id]['credit'] = 0
                continue

            if account_code.startswith('1312') \
                    or account_code.startswith('3311'):
                balance_dict[account_id]['credit'] = credit - debit
                balance_dict[account_id]['debit'] = 0
                continue

            prefix = account_code[0]

            if prefix in ('1', '2'):
                balance_dict[account_id]['debit'] = debit - credit
                balance_dict[account_id]['credit'] = 0
                continue

            if prefix in ('3', '4'):
                balance_dict[account_id]['debit'] = 0
                balance_dict[account_id]['credit'] = credit - debit

    @api.multi
    def get_data(self):
        start_date = self[0].start_date
        end_date = self[0].end_date
        type_entries = self[0].type_entries
        company_id = self[0].company_id.id

        # query calculate start, period, end - credit, debit
        start_period_where_clause = """
          am.date < '{}'
        """.format(start_date)
        period_where_clause = """
          am.date >= '{}'
         and am.date <= '{}'
        """.format(start_date, end_date)
        end_period_where_clause = """
          am.date <= '{}'
        """.format(end_date)

        post_where_clause = ''
        if type_entries == 'filter_posted':
            post_where_clause = " and am.state = 'posted'"

        querry = """
                    select ml.account_id as id,
                        sum(ml.credit) as credit,
                        sum(ml.debit) as debit
                    from account_move_line as ml
                        left join account_move as am
                        on am.id = ml.move_id
                    where {}
                    {}
                    and ml.company_id = {}
                    group by ml.account_id
                """

        start_querry = querry.format(
            start_period_where_clause,
            post_where_clause,
            company_id)
        period_querry = querry.format(
            period_where_clause,
            post_where_clause,
            company_id)
        end_querry = querry.format(
            end_period_where_clause,
            post_where_clause,
            company_id)

        # calculate start,period, end - credit, debit
        self.env.cr.execute(start_querry)
        querry_result = self.env.cr.dictfetchall()
        start_dict = dict((row['id'], row) for row in querry_result)

        self.env.cr.execute(period_querry)
        querry_result = self.env.cr.dictfetchall()
        period_dict = dict((row['id'], row) for row in querry_result)

        self.env.cr.execute(end_querry)
        querry_result = self.env.cr.dictfetchall()
        end_dict = dict((row['id'], row) for row in querry_result)

        # account.account tree
        root_account_tree = self.get_account_tree()

        # list account, index(parent, child level)
        account_list, index_dict = \
            self.get_account_list(root_account_tree)

        # phát sinh start, period, end từng account.account
        incurred_account_dict = {}

        self.process_balance(start_dict)
        self.process_balance(end_dict)

        incurred_type_dict = {
            'start': start_dict,
            'period': period_dict,
            'end': end_dict
        }

        for incurred_type in ['start', 'period', 'end']:
            incurred_dict = incurred_type_dict[incurred_type]
            for type in ['credit', 'debit']:
                for root_account in root_account_tree.keys():
                    self.set_incurred(
                        root_account, incurred_account_dict,
                        incurred_dict, incurred_type,
                        type=type)

        return account_list, incurred_account_dict, index_dict

    def get_account_tree(self):
        view_account_type = \
            self.env.ref('account_parent.data_account_type_view')

        domain = [('parent_id', '=', False),
                  ('user_type_id', '=', view_account_type.id)]
        root_account_s = self.env['account.account'].with_context(
            show_parent_account=True).search(domain)

        root_account_tree = {}

        for root_account in root_account_s:
            childs = self.get_child(
                root_account)

            root_account_tree[root_account] = childs
        return root_account_tree

    def get_child(self, account):
        child_ids = account.child_ids
        if not child_ids:
            return {}

        childs = {}

        for child in child_ids:
            child_child = self.get_child(child)
            childs[child] = child_child

        return childs

    def get_account_list(self, root_account_tree):
        def add_child_child(account_list, index_dict, child, index):
            child_ids = child.child_ids

            index += 1

            index_dict[child] = index

            if not child_ids:
                return

            sorted_child_ids = \
                sorted(child_ids, key=lambda a: a.code)

            for child_id in sorted_child_ids:
                account_list.append(child_id)
                add_child_child(account_list, index_dict, child_id, index)

        account_list = []
        index_dict = {}

        root_account_list = root_account_tree.keys()
        sorted_root_account_list = \
            sorted(root_account_list, key=lambda a: a.code)

        for root_account in sorted_root_account_list:
            index_dict[root_account] = 0
            account_list.append(root_account)
            add_child_child(account_list, index_dict, root_account, index =0)

        return account_list, index_dict

    def set_incurred(
            self, account, incurred_account_dict,
            incurred_dict, incurred_type, type='credit'):

        if not incurred_account_dict.get(account, False):
            incurred_account_dict[account] = {}

        if not incurred_account_dict[account].get(incurred_type, False):
            incurred_account_dict[account][incurred_type] = {}

        # if incurred_account_dict[account][incurred_type].get(type, False):
        #     incurred_account_dict[account][incurred_type][type]

        child_ids = account.child_ids
        if not child_ids:
            incurred = incurred_dict.get(account.id, {}).get(type, 0)
            incurred_account_dict[account][
                incurred_type][type] = incurred

            return True

        incurred = 0
        for child_id in child_ids:
            self.set_incurred(
                child_id, incurred_account_dict,
                incurred_dict, incurred_type, type)

            incurred += incurred_account_dict[child_id][
                incurred_type][type]

        incurred_account_dict[account][
            incurred_type][type] = incurred

        return True

    @api.multi
    def action_print(self):
        return self.env['report'].get_action(self, 'btek_report_accounting.bangcandoiphatsinh_report')

    @api.multi
    def action_view(self):
        datas = {'ids': self.ids}
        datas['model'] = 'bang.can.doi.phat.sinh'

        report_name = 'btek_report_accounting.bangcandoiphatsinh_report'
        res = self.env['ir.actions.report.xml'
        ].preview_xlsx_report(report_name, self._ids, datas)
        return res

class Bangcandoiphatsinhreport(ReportXlsx):
    _name = 'report.btek_report_accounting.bangcandoiphatsinh_report'

    def write_bangcd(self, ws, data, form):
        # Header
        address = u''
        if form.company_id.street: address = form.company_id.street
        if form.company_id.street2: address = address + ', ' + unicode(form.company_id.street2)
        if form.company_id.city: address = address + ', ' + unicode(form.company_id.city)
        ws.write('A%s' % 1, u'Đơn vị báo cáo:', )
        ws.merge_range('B1:E1', form.company_id.name, self.xxxxx)
        ws.write('A%s' % 2, u'Địa chỉ:', )
        ws.merge_range('B2:E2', address, self.xxxxx)
        ws.merge_range('B3:J4', u'BẢNG CÂN ĐỐI PHÁT SINH CÁC TÀI KHOẢN', self.title)
        ws.merge_range('B5:J5', u'Từ ngày: ' + unicode(datetime.datetime.strptime(form.start_date, '%Y-%m-%d').strftime('%d/%m/%Y'))
                       + u' Đến ngày: ' + unicode(datetime.datetime.strptime(form.end_date, '%Y-%m-%d').strftime('%d/%m/%Y')), self.header)

        # row = 8
        # # ws.write('B%s' % row, u'Chọn', self.table_header)
        # ws.write('B%s' % row, u'Mã khách hàng', self.table_header)
        # ws.write('C%s' % row, u'Tên khách hàng', self.table_header)
        # ws.write('D%s' % row, u'Dư nợ đầu kỳ', self.table_header)
        # ws.write('E%s' % row, u'Dư có đầu kỳ', self.table_header)
        # ws.write('F%s' % row, u'Ps Nợ', self.table_header)
        # ws.write('G%s' % row, u'Ps Có', self.table_header)
        # ws.write('H%s' % row, u'Dư nợ cuối kỳ', self.table_header)
        # ws.write('I%s' % row, u'Dư có cuối kỳ', self.table_header)
        #
        # row = 10
        # if data:
        #     sum_nodau = sum_codau = sum_psno = sum_psco = sum_nocuoi = sum_cocuoi = 0
        #     for r in data:
        #         # ws.write("B{row}".format(row=row), 'True', self.table_row_left)
        #         ws.write("B{row}".format(row=row), r['ma_kh'] or '', self.table_row_left)
        #         ws.write("C{row}".format(row=row), r['name'] or '', self.table_row_left)
        #         ws.write("D{row}".format(row=row), r['nodauky'] or '', self.table_row_right)
        #         ws.write("E{row}".format(row=row), r['codauky'] or '', self.table_row_right)
        #         ws.write("F{row}".format(row=row), r['debit'] or '', self.table_row_right)
        #         ws.write("G{row}".format(row=row), r['credit'] or '', self.table_row_right)
        #         ws.write("H{row}".format(row=row), r['nocuoiky'] or '', self.table_row_right)
        #         ws.write("I{row}".format(row=row), r['cocuoiky'] or '', self.table_row_right)
        #
        #         if r['nodauky']: sum_nodau =+ r['nodauky']
        #         if r['codauky']: sum_codau =+ r['codauky']
        #         if r['debit']: sum_psno =+ r['debit']
        #         if r['credit']: sum_psco =+ r['credit']
        #         if r['nocuoiky']: sum_nocuoi =+ r['nocuoiky']
        #         if r['cocuoiky']: sum_cocuoi =+ r['cocuoiky']
        #         row = row + 1
        #     row = 9
        #     # ws.write("B{row}".format(row=row), 'False', self.table_row_left_bold)
        #     ws.write("B{row}".format(row=row), '', self.table_row_left)
        #     ws.write("C{row}".format(row=row), u'Tổng cộng:' or '', self.table_row_left_bold)
        #     ws.write("D{row}".format(row=row), sum_nodau or '', self.table_row_right_bold)
        #     ws.write("E{row}".format(row=row), sum_codau or '', self.table_row_right_bold)
        #     ws.write("F{row}".format(row=row), sum_psno or '', self.table_row_right_bold)
        #     ws.write("G{row}".format(row=row), sum_psco or '', self.table_row_right_bold)
        #     ws.write("H{row}".format(row=row), sum_nocuoi or '', self.table_row_right_bold)
        #     ws.write("I{row}".format(row=row), sum_cocuoi or '', self.table_row_right_bold)


    def generate_xlsx_report(self, wb, data, form):
        account_list, incurred_account_dict, \
        index_dict = form.get_data()
        display_account = form.display_account
        reports = {
            'report': self.write_bangcd,
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
            'font_size': 20,
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
            'bg_color': '#C6EFCE',
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

        ws.set_column('A:A', 14)
        ws.set_column('B:B', 45)

        self.write_bangcd(ws, data, form)

        row_pos = 7

        ws.merge_range(
            'A{row_pos}:A{row_pos_1}'.format(
                row_pos=row_pos,row_pos_1=row_pos + 1),
            u'Tài khoản',
            self.table_header)

        ws.merge_range(
            'B{row_pos}:B{row_pos_1}'.format(
                row_pos=row_pos, row_pos_1=row_pos + 1),
            u'Tên tài khoản',
            self.table_header)

        ws.merge_range(
            'C{row_pos}:F{row_pos}'.format(
                row_pos=row_pos),
            u'Dư đầu kỳ',
            self.table_header)

        ws.merge_range(
            'C{row_pos}:D{row_pos}'.format(
                row_pos=row_pos + 1),
            u'Nợ',
            self.table_header)

        ws.merge_range(
            'E{row_pos}:F{row_pos}'.format(
                row_pos=row_pos + 1),
            u'Có',
            self.table_header)

        ws.merge_range(
            'G{row_pos}:J{row_pos}'.format(
                row_pos=row_pos),
            u'Phát sinh',
            self.table_header)

        ws.merge_range(
            'G{row_pos}:H{row_pos}'.format(
                row_pos=row_pos + 1),
            u'Nợ',
            self.table_header)

        ws.merge_range(
            'I{row_pos}:J{row_pos}'.format(
                row_pos=row_pos + 1),
            u'Có',
            self.table_header)

        ws.merge_range(
            'K{row_pos}:N{row_pos}'.format(
                row_pos=row_pos),
            u'Dư cuối kỳ',
            self.table_header)

        ws.merge_range(
            'K{row_pos}:L{row_pos}'.format(
                row_pos=row_pos + 1),
            u'Nợ',
            self.table_header)

        ws.merge_range(
            'M{row_pos}:N{row_pos}'.format(
                row_pos=row_pos + 1),
            u'Có',
            self.table_header)

        row_pos += 2

        ws.freeze_panes(row_pos - 1, 15)

        def write_a_row(self, ws, code, name, start, period,
                        end, row_pos, index, type):
            left_type = self.table_row_left
            right_type = self.table_row_right
            if type == 'view':
                left_type = self.table_row_left_bold
                right_type = self.table_row_right_bold

            # if index:
            #     for i in range(0, index):
            #         name = '      ' + name

            ws.write(
                row_pos - 1, 0,
                code, left_type)

            ws.write(
                row_pos - 1, 1,
                name, left_type)

            ws.merge_range(
                'C{row_pos}:D{row_pos}'.format(
                    row_pos=row_pos),
                start.get('debit', 0),
                right_type)

            ws.merge_range(
                'E{row_pos}:F{row_pos}'.format(
                    row_pos=row_pos),
                start.get('credit', 0),
                right_type)

            ws.merge_range(
                'G{row_pos}:H{row_pos}'.format(
                    row_pos=row_pos),
                period.get('debit', 0),
                right_type)

            ws.merge_range(
                'I{row_pos}:J{row_pos}'.format(
                    row_pos=row_pos),
                period.get('credit', 0),
                right_type)

            ws.merge_range(
                'K{row_pos}:L{row_pos}'.format(
                    row_pos=row_pos),
                end.get('debit', 0),
                right_type)

            ws.merge_range(
                'M{row_pos}:N{row_pos}'.format(
                    row_pos=row_pos),
                end.get('credit', 0),
                right_type)

            row_pos += 1
            return row_pos

        for account in account_list:
            index = index_dict.get(account, 0)

            code = account.code
            name = account.name
            type = account.user_type_id.type
            
            incurred_account = incurred_account_dict.get(account, {})
            start = incurred_account.get('start', {})
            period = incurred_account.get('period', {})
            end = incurred_account.get('end', {})

            period_credit = period.get('credit', 0)
            period_debit = period.get('debit', 0)

            start_credit = start.get('credit', 0)
            start_debit = start.get('debit', 0)

            if display_account == 'not_zero' \
                    and period_credit + start_credit \
                            == period_debit + start_debit:
                continue

            if display_account == 'movement' \
                    and not period_debit \
                    and not period_credit \
                    and not start_credit \
                    and not start_debit:
                continue

            row_pos = write_a_row(
                self, ws, code, name, start, period,
                end, row_pos, index, type)

        # import time
        # args = {
        #     'start': form.start_date,
        #     'end': form.end_date,
        #     'type': form.type_entries,
        #     'company_id': form.company_id.id,
        #     'date_daunam': time.strftime('%Y-01-01'),
        #     'display_account': form.display_account,
        #     }
        # report_data = self.get_data_from_query(args)
        # reports['report'](ws, report_data, form)

    # def get_data_from_query(self, kwargs):
    #     sql = self.get_query(kwargs)
    #     # self.env.cr.execute(sql)
    #     # data = self.env.cr.dictfetchall()
    #     return sql
    #
    # def _get_accounts(self, accounts, display_account):
    #     """ compute the balance, debit and credit for the provided accounts
    #         :Arguments:
    #             `accounts`: list of accounts record,
    #             `display_account`: it's used to display either all accounts or those accounts which balance is > 0
    #         :Returns a list of dictionary of Accounts with following key and value
    #             `name`: Account name,
    #             `code`: Account code,
    #             `credit`: total amount of credit,
    #             `debit`: total amount of debit,
    #             `balance`: total amount of balance,
    #     """
    #
    #     account_result = {}
    #     # Prepare sql query base on selected parameters from wizard
    #     tables, where_clause, where_params = self.env['account.move.line']._query_get()
    #     tables = tables.replace('"','')
    #     if not tables:
    #         tables = 'account_move_line'
    #     wheres = [""]
    #     if where_clause.strip():
    #         wheres.append(where_clause.strip())
    #     filters = " AND ".join(wheres)
    #     # compute the balance, debit and credit for the provided accounts
    #     request = ("SELECT account_id AS id, SUM(debit) AS debit, SUM(credit) AS credit, (SUM(debit) - SUM(credit)) AS balance" +\
    #                " FROM " + tables + " WHERE account_id IN %s " + filters + " GROUP BY account_id")
    #     params = (tuple(accounts.ids),) + tuple(where_params)
    #     self.env.cr.execute(request, params)
    #     for row in self.env.cr.dictfetchall():
    #         account_result[row.pop('id')] = row
    #
    #     account_res = []
    #     for account in accounts:
    #         res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
    #         currency = account.currency_id and account.currency_id or account.company_id.currency_id
    #         res['code'] = account.code
    #         res['name'] = account.name
    #         res['id'] = account.id
    #         if account.id in account_result.keys():
    #             res['debit'] = account_result[account.id].get('debit')
    #             res['credit'] = account_result[account.id].get('credit')
    #             res['balance'] = account_result[account.id].get('balance')
    #         if display_account == 'all':
    #             account_res.append(res)
    #         if display_account == 'not_zero' and not currency.is_zero(res['balance']):
    #             account_res.append(res)
    #         if display_account == 'movement' and (not currency.is_zero(res['debit']) or not currency.is_zero(res['credit'])):
    #             account_res.append(res)
    #     return account_res

    # def get_query(self, kwargs):
    #
    #     str_filter = " OR (l.account_id = C.id and am.state='posted' and l.date < '" + kwargs['start']
    #                  # + "' and per.fiscalyear_id in (%s))" % (fiscalyear_clause)
    #
    #     # obj_move = self.env['account.move.line']
    #     query = str('l.state <> "draft" AND l.move_id IN (SELECT id FROM account_move WHERE account_move.state = %(state)s) AND l.move_id IN (SELECT id FROM account_move WHERE date >= %(date_from)s AND date <= %(date_to)s) AND l.journal_id IN %(journal_ids)s AND l.account_id IN %(child_idss')
    #     where_query = query
    #     journal = self.env['account.journal']
    #     journal_ids = journal.search([]).ids
    #     account = self.env['account.account'].search([])
    #     account_ids = self._get_accounts(account, kwargs['display_account'])
    #     account_ids = [x['id'] for x in account_ids]
    #     sql = """
    #         SELECT
    #             id,
    #             code,
    #             name,
    #             level,
    #             SUM(opening_debit) as opening_debit,
    #             SUM(opening_credit) as opening_credit,
    #             SUM(debit) as debit,
    #             SUM(credit) as credit,
    #             ((SUM(debit) - SUM(credit)) + (SUM(opening_debit) - SUM(opening_credit))) as balance
    #         FROM
    #         (SELECT P.id, P.code, P.name, 2 as level,
    #             CASE WHEN (SELECT SUM(debit)
    #             FROM account_move_line l
    #             JOIN account_move am ON (am.id=l.move_id)
    #             WHERE
    #             (l.account_id = C.id and am.state='posted' and l.date < '2017-01-01')) IS NULL
    #         THEN 0 ELSE (SELECT SUM(debit)
    #             FROM account_move_line l
    #             JOIN account_move am ON (am.id=l.move_id)
    #             WHERE (l.account_id = C.id and am.state='posted' and l.date < '2017-01-01')) END AS opening_debit,
    #         CASE WHEN (SELECT SUM(credit)
    #             FROM account_move_line l
    #             JOIN account_move am ON (am.id=l.move_id)
    #
    #             WHERE (l.account_id = C.id and am.state='posted' and l.date < '2017-01-01')) IS NULL
    #         THEN 0 ELSE (SELECT SUM(credit)
    #             FROM account_move_line l
    #             JOIN account_move am ON (am.id=l.move_id)
    #             WHERE (l.account_id = C.id and am.state='posted' and l.date < '2017-01-01')) END AS opening_credit,
    #             CASE WHEN (SELECT SUM(debit)
    #                 FROM account_move_line l
    #                 JOIN account_move am ON (am.id=l.move_id)
    #                 WHERE am.state <> 'draft'
    #                 AND l.move_id IN (SELECT id FROM account_move WHERE account_move.state = 'posted')
    #                 AND l.move_id IN (SELECT id FROM account_move WHERE date >= '2017-01-01' AND date <= '2017-12-31')
    #                 AND l.journal_id IN {journal_ids}
    #                 AND l.account_id IN {account_ids}
    #                 AND l.account_id = C.id
    #                 AND am.state='posted') IS NULL
    #             THEN 0 ELSE (SELECT SUM(debit)
    #                 FROM account_move_line l
    #                 JOIN account_move am ON (am.id=l.move_id)
    #                 WHERE am.state <> 'draft'
    #                 AND l.move_id IN (SELECT id FROM account_move WHERE account_move.state = 'posted')
    #                 AND l.move_id IN (SELECT id FROM account_move WHERE date >= '2017-01-01' AND date <= '2017-12-31')
    #                 AND l.journal_id IN {journal_ids}
    #                 AND l.account_id IN {account_ids}
    #                 AND l.account_id = C.id
    #                 AND am.state='posted')
    #                 END AS debit,
    #             CASE WHEN (SELECT SUM(credit)
    #                 FROM account_move_line l
    #                 JOIN account_move am ON (am.id=l.move_id)
    #                 WHERE am.state <> 'draft'
    #                 AND l.move_id IN (SELECT id FROM account_move WHERE account_move.state = 'posted')
    #                 AND l.move_id IN (SELECT id FROM account_move WHERE date >= '2017-01-01'
    #                 AND date <= '2017-12-31')
    #                 AND l.journal_id IN {journal_ids}
    #                 AND l.account_id IN {account_ids}
    #                 AND l.account_id = C.id
    #                 AND am.state='posted') IS NULL
    #             THEN 0 ELSE (SELECT SUM(credit)
    #                 FROM account_move_line l
    #                 JOIN account_move am ON (am.id=l.move_id)
    #                 WHERE am.state <> 'draft'
    #                 AND l.move_id IN (SELECT id FROM account_move WHERE account_move.state = 'posted')
    #                 AND l.move_id IN (SELECT id FROM account_move WHERE date >= '2017-01-01'
    #                 AND date <= '2017-12-31')
    #                 AND l.journal_id IN {journal_ids}
    #                 AND l.account_id IN {account_ids}
    #                 AND l.account_id = C.id
    #                 AND am.state='posted')
    #                 END AS credit
    #         FROM account_account P, account_account C
    #         WHERE P.parent_left <= C.parent_left
    #         AND P.parent_right >= C.parent_right
    #         --AND P.level >= 2
    #         AND ((C.id IN (SELECT account_id
    #                 FROM account_move_line l
    #                 JOIN account_move am ON (am.id=l.move_id)
    #                 --JOIN account_period per ON (per.id=l.period_id)
    #                 WHERE am.state <> 'draft'
    #                 AND l.move_id IN (SELECT id FROM account_move WHERE account_move.state = 'posted')
    #                 AND l.move_id IN (SELECT id FROM account_move WHERE date >= '2017-01-01' AND date <= '2017-12-31')
    #                 AND l.journal_id IN {journal_ids}
    #                 AND l.account_id IN {account_ids}
    #                 AND am.state='posted')
    #                 OR (P.id IN (SELECT account_id
    #                 FROM account_move_line l
    #                 JOIN account_move am ON (am.id=l.move_id)
    #                 WHERE am.state <> 'draft'
    #                 AND l.move_id IN (SELECT id FROM account_move WHERE account_move.state = 'posted')
    #                 AND l.move_id IN (SELECT id FROM account_move WHERE date >= '2017-01-01' AND date <= '2017-12-31')
    #                 AND l.journal_id IN {journal_ids}
    #                 AND l.account_id IN {account_ids}
    #                 AND am.state='posted'))))) AS A
    #         GROUP BY A.id, A.code, A.name, A.level
    #         ORDER BY A.code
    #
    #     """.format(journal_ids=tuple(journal_ids), account_ids=tuple(account_ids))
    #     self.env.cr.execute(sql)
    #     res_lines = self.env.cr.dictfetchall()
    #     total_opening_debit = 0
    #     total_opening_credit = 0
    #     total_debit = 0
    #     total_credit = 0
    #     total_balance_debit = 0
    #     total_balance_credit = 0
    #     for item in res_lines:
    #         if item['level'] == 2:
    #             total_opening_debit += item['opening_debit']
    #             total_opening_credit += item['opening_credit']
    #             total_debit += item['debit']
    #             total_credit += item['credit']
    #             if item['balance'] > 0:
    #                 total_balance_debit += item['balance']
    #             elif item['balance'] < 0:
    #                 total_balance_credit += abs(item['balance'])
    #     res_lines.append({
    #         'code': False,
    #         'total_opening_debit': total_opening_debit,
    #         'total_opening_credit': total_opening_credit,
    #         'total_debit': total_debit,
    #         'total_credit': total_credit,
    #         'total_balance_debit': total_balance_debit,
    #         'total_balance_credit': total_balance_credit,
    #     })
    #     return res_lines

Bangcandoiphatsinhreport('report.btek_report_accounting.bangcandoiphatsinh_report', 'bang.can.doi.phat.sinh')

