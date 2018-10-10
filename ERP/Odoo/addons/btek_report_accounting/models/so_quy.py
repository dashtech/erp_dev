#!/usr/bin/python
# -*- encoding: utf-8 -*-
# ANHTT
from odoo import api, fields, models, _, tools
import datetime
import time


# class Account_account(models.Model):
#     _inherit = 'account.account'
#
#     @api.model
#     def name_search(self, name='', args=None, operator='ilike', limit=100):
#         if self._context.get('tienmat', False):
#         args.append(['is_copy', '!=', True])
#         res = super(Account_account, self).name_search(name=name, args=args, operator=operator, limit=limit)
#         return res

class SoQuyS07DN(models.TransientModel):
    _name = 'so.quy.s07'

    @api.model
    def _getdate(self):
        import datetime
        return datetime.date(datetime.date.today().year, 1, 1)

    @api.model
    def _gettoday(self):
        import datetime
        return datetime.date.today()

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    @api.onchange('account_account_id')
    def onchange_account_account(self):
        key = '112%'
        if self.type_report == 'tienmat':
            key = '111%'

        return {
            'domain': {
                'account_account_id': [('code', '=ilike', key)]
            }
        }


    start_date = fields.Date(default=_getdate, required=True)
    end_date = fields.Date(default=_gettoday, required=True)

    company_id = fields.Many2one('res.company', required=True, default=_get_company)
    type_entries = fields.Selection([('filter_posted', 'All Post Entries'), ('filter_all', 'All Entries')], "Type",
                                    default='filter_posted', required=True)
    account_account_id = fields.Many2one('account.account',
                                         string="Accounts", required=True)
    type_report = fields.Selection([('tienmat', 'tienmat'), ('tiengui', 'tiengui')], required=1)

    # @api.onchange('type_account')
    # def onchange_type_account(self):
    #     a = 1

    @api.model
    def get_child_ids(self, account):
        sub_account_s = self.env['account.account'].with_context(
            {'show_parent_account': True}).search([('id', 'child_of', [account.id])])
        return sub_account_s.ids

    def get_account_ids(self):
        account_ids = []
        if self.account_account_id:
            account_id_s = self.get_child_ids(self.account_account_id)
            account_ids.extend(account_id_s)
        if len(account_ids) == 1:
            account_ids.append(0)
        return account_ids

    @api.multi
    def get_data_from_query_so_quy(self):
        account_ids = self.get_account_ids()
        args = {
            'start': self.start_date,
            'end': self.end_date,
            'type': self.type_entries,
            'account_ids': tuple(account_ids),
            'company_id': self.company_id.id,
            'date_daunam': time.strftime('%Y-01-01'),
            }

        sql = self.get_query(args)
        self.env.cr.execute(sql)
        data = self.env.cr.dictfetchall()
        opening = self.get_openingbalance(args)
        data = {'data': data, 'open': opening}
        return data

    def get_openingbalance(self, kwargs):
        sql_sodudauki = """
                        SELECT SUM(debit) debit, SUM(credit) AS credit
                        FROM account_move_line aml
                        LEFT JOIN account_account aa ON aa.id = aml.account_id
                        LEFT JOIN account_move am ON am.id = aml.move_id
                        WHERE am.company_id = {company_id}
                        AND CASE WHEN '{type}' = 'filter_posted' THEN am.state in ('posted') ELSE am.state IN ('posted','draft') END
                        AND aa.id IN {account_ids}
                        AND (am.date < '{start}')
                            """.format(**kwargs)
        self.env.cr.execute(sql_sodudauki)
        res = self.env.cr.dictfetchone()
        return res

    def get_query(self, kwargs):
        sql = """
                SELECT aml.id, aml.move_id, to_char(am.date,'dd/mm/YYYY') date,
                am.name chungtu,
                av.recipient_pay
                nguoinhannguoinop,
                CASE
                    WHEN aml.statement_id IS NOT NULL THEN ''
                    ELSE rp.name
                END khachhang,
                aml.name as diengiai,
                SUM(aml.debit) debit,
                SUM(aml.credit) credit
                FROM account_move_line aml
                INNER JOIN account_move am ON aml.move_id = am.id
                LEFT JOIN account_bank_statement abs ON abs.id = aml.statement_id
                LEFT JOIN res_partner rp ON rp.id = aml.partner_id
                LEFT JOIN account_voucher av ON av.move_id = am.id
                LEFT JOIN product_product pp ON pp.id = aml.product_id
                WHERE am.company_id = {company_id}
                AND CASE WHEN '{type}' = 'filter_posted' THEN am.state IN ('posted') ELSE am.state IN ('posted','draft') END
                AND '{start}' <= am.date and am.date <= '{end}'
                AND aml.account_id IN {account_ids}
                GROUP BY aml.id, aml.move_id, am.date, chungtu, nguoinhannguoinop, khachhang, diengiai
                ORDER BY am.date, debit DESC, chungtu
        """.format(**kwargs)
        return sql

    @api.multi
    def action_print(self):
        return self.env['report'].get_action(
            self, 'btek_report_accounting.soquys07_report')

    @api.multi
    def preview_excel(self):
        datas = {'ids': self.ids}
        datas['model'] = self._name

        report_name = 'btek_report_accounting.soquys07_report'
        res = self.env['ir.actions.report.xml'
        ].preview_xlsx_report(report_name, self._ids, datas)
        return res

    @api.multi
    def view_report(self):
        action_obj = \
            self.env.ref(
                'btek_report_accounting.account_move_line_so_quy_s07_action')
        action = action_obj.read([])[0]

        account_ids = self.get_account_ids()

        domain = [('company_id', '=', self.company_id.id),
                  ('date', '>=', self.start_date),
                  ('date', '<=', self.end_date),
                  ('account_id', 'in', account_ids)]

        if self.type_entries == 'filter_posted':
            domain.append(
                ('state', '=', 'posted')
            )

        args = {
            'start': self.start_date,
            'end': self.end_date,
            'type': self.type_entries,
            'account_ids': tuple(account_ids),
            'company_id': self.company_id.id,
            'date_daunam': time.strftime('%Y-01-01'),
        }

        opening = self.get_openingbalance(args)
        dauky = (opening['debit'] or 0) - (opening['credit'] or 0)

        action['domain'] = domain
        action['context'] = {'start_balance': dauky}

        if self.type_report == 'tiengui':
            action['name'] = _('Bank book')

        return action

from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
class SoQuyS07(ReportXlsx):
    _name = 'report.btek_report_accounting.soquys07_report'

    def write_soquy(self, ws, data, form):
        ws.set_column(0, 0, 15)
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
        ws.set_column(0, 0, 11)  # ngay
        ws.set_column(1, 1, 17)
        ws.set_column(2, 2, 20)
        ws.set_column(3, 3, 20)
        ws.set_column(4, 4, 30)
        ws.set_column(5, 5, 16)
        ws.set_column(6, 5, 16)
        ws.set_column(7, 5, 16)

        address = u''
        if form.company_id.street: address = form.company_id.street
        if form.company_id.street2: address = address + ', ' + unicode(form.company_id.street2)
        if form.company_id.city: address = address + ', ' + unicode(form.company_id.city)

        ws.merge_range("A1:E1", unicode(form.company_id.name), self.xxxxx)
        ws.merge_range("A2:E2", unicode(address), self.xxxxx)
        ws.merge_range("A3:C3", u'Mã số thuế: ' + unicode(form.company_id.street or ''), self.xxxxx)
        ws.merge_range("F1:H1", u'Mẫu S07-DN', self.center)
        ws.merge_range("F2:H2", u'(Ban hành theo TT số 200/2014/TT-BTC', self.center)
        ws.merge_range("F3:H3", u'Ngày 22/12/2014 của Bộ tài chính)', self.center)

        if form.type_report == 'tienmat':
            ws.merge_range("D5:E5", u"TIỀN MẶT", self.title)
        else:
            ws.merge_range("D5:E5", u"TIỀN GỬI", self.title)
        ws.merge_range("D6:E6", u"Tài khoản: " + form.account_account_id.code + ' - ' + form.account_account_id.name,
                       self.center)

        start_view = datetime.datetime.strptime(form.start_date, '%Y-%m-%d').strftime('%d/%m/%Y').decode('unicode-escape')
        end_view = datetime.datetime.strptime(form.end_date, '%Y-%m-%d').strftime('%d/%m/%Y').decode('unicode-escape')
        ws.merge_range("A7:H7", u" Từ ngày: " + start_view + u" đến ngày: " + end_view + u"", self.center)

        ws.merge_range("A9:B9", u"Chứng từ", self.table_header)
        ws.merge_range("C9:C10", u'Người nhận/nộp tiền', self.table_header)
        ws.merge_range("D9:D10", u'Khách hàng', self.table_header)
        ws.merge_range("E9:E10", u'Diễn giải', self.table_header)
        ws.merge_range("F9:G9", u'Số phát sinh', self.table_header)
        ws.merge_range("H9:H10", u'Số dư', self.table_header)

        ws.write("A10", u'Ngày', self.table_header)
        ws.write("B10", u'Số', self.table_header)
        ws.write("F10", u'Nợ', self.table_header)
        ws.write("G10", u'Có', self.table_header)

        opening = data['open']

        row = 11
        ws.write("A{row}".format(row=row), '', self.row_date_default)
        ws.write("B{row}".format(row=row), '', self.table_row_left)
        ws.write("C{row}".format(row=row), '', self.table_row_left)
        ws.write("D{row}".format(row=row), '', self.table_row_left)
        ws.write("E{row}".format(row=row), u'Số dư đầu kỳ :', self.table_header)
        if opening:
            dauky = (opening['debit'] or 0) - (opening['credit'] or 0)
            if dauky >= 0:
                ws.write("F{row}".format(row=row), dauky, self.table_header_right)
                ws.write("G{row}".format(row=row), 0, self.table_header_right)
            else:
                ws.write("F{row}".format(row=row), 0, self.table_header_right)
                ws.write("G{row}".format(row=row), -dauky, self.table_header_right)
        else:
            ws.write("F{row}".format(row=row), '', self.table_header_right)
            ws.write("G{row}".format(row=row), '', self.table_header_right)
        ws.write("H{row}".format(row=row), "=F{row}-G{row}".format(row=row), self.table_header_right)
        row += 1

        start_row = row
        data_line = data['data']
        if data_line:
            for r in data_line:
                if r['date']:
                    date = datetime.datetime.strptime(r['date'], '%d/%m/%Y')
                    ws.write("A{row}".format(row=row), r['date'] or '', self.row_date_default)
                else:
                    ws.write("A{row}".format(row=row), '', self.row_date_default)

                ws.write("B{row}".format(row=row), r['chungtu'] or '', self.table_row_left)
                ws.write("C{row}".format(row=row), r['nguoinhannguoinop'] or '', self.table_row_left)
                ws.write("D{row}".format(row=row), r['khachhang'] or '', self.table_row_left)
                ws.write("E{row}".format(row=row), r['diengiai'] or '', self.table_row_left)
                ws.write("F{row}".format(row=row), r['debit'] or '', self.table_row_right)
                ws.write("G{row}".format(row=row), r['credit'] or '', self.table_row_right)
                ws.write("H{row}".format(row=row), "=H{row1}+F{row2}-G{row2}".format(row1=row - 1, row2=row),
                         self.table_row_right)
                row += 1

            ws.write("E{row}".format(row=row), u'Tổng phát sinh :', self.table_row_left_bold)
            ws.write("F{row}".format(row=row), "=SUM(F{row1}:F{row2})".format(row1=start_row, row2=row - 1),
                          self.table_header_right)
            ws.write("G{row}".format(row=row), "=SUM(G{row1}:G{row2})".format(row1=start_row, row2=row - 1),
                          self.table_header_right)
            ws.write("H{row}".format(row=row), '=H{row}'.format(row=row - 1), self.table_header_right)


    def generate_xlsx_report(self, wb, data, form):
        reports = {
            'report': self.write_soquy,
        }
        ws = wb.add_worksheet('Sochitietcongno')
        wb.formats[0].font_name = 'Times New Roman'
        wb.formats[0].font_size = 11
        ws.set_paper(9)
        ws.center_horizontally()
        ws.set_margins(left=0.28, right=0.28, top=0.5, bottom=0.5)
        ws.fit_to_pages(1, 0)
        ws.set_landscape()
        ws.fit_to_pages(1, 1)

        # args = {
        #     'from_date': form.from_date,
        #     'to_date': form.to_date,
        #     'material_type': form.material_type,
        #     'plant_description': form.plant_description,
        # }
        # report_data = self.get_data_from_query(args)

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
        self.table_header_right = wb.add_format({
            'bold': 1,
            'text_wrap': 1,
            'align': 'right',
            'valign': 'vcenter',
            'border': 1,
            'font_name': 'Times New Roman',
            'num_format': '#,##0',
        })
        self.row_date_default = wb.add_format({
            'text_wrap': 1,
            'align': 'center',
            'valign': 'vcenter',
            'border': 1,
            'font_name': 'Times New Roman',
            'font_size': 11
        })

        self.table_row_left = wb.add_format(
            {'text_wrap': 1, 'align': 'left', 'valign': 'vcenter', 'border': 1, 'num_format': '#,##0',
             'font_name': 'Times New Roman', })

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

        report_data = form.get_data_from_query_so_quy()
        reports['report'](ws, report_data, form)

SoQuyS07('report.btek_report_accounting.soquys07_report', 'so.quy.s07')


class account_move_line_so_quy_s07(models.Model):
    _name = 'account.move.line.so.quy.s07'
    _auto = False
    _order = 'date, debit DESC, chungtu'

    def get_state_selection(self):
        user = self.env.user
        import_object = self.env['account.move']. \
            with_context(lang=user.partner_id.lang)
        field = import_object._fields['state']
        selection = field.selection
        return selection

    date = fields.Date()
    chungtu = fields.Char('Number')
    nguoinhannguoinop = fields.Char('Receiver/payers')
    khachhang = fields.Char('Customer')
    diengiai = fields.Char('Explain')
    debit = fields.Float()
    credit = fields.Float()
    company_id = fields.Many2one('res.company', 'Company')
    account_id = fields.Many2one('account.account', 'Account')
    move_id = fields.Many2one('account.move', 'Move')
    state = fields.Selection(selection=lambda s:s.get_state_selection())
    balance = fields.Float(compute='_compute_balance')


    @api.multi
    def _compute_balance(self):
        start_balance = self.env.context.get('start_balance', 0)

        line_s = self.search_read(
            [('id', 'in', self._ids)],
        ['debit','credit','khachhang'],
        order='date, debit DESC, chungtu')

        balance_dict = {}

        for line in line_s:
            debit = line['debit'] or 0
            credit = line['credit'] or 0
            balance = start_balance + debit - credit
            balance_dict[line['id']] = balance

            start_balance = balance

        for l in self:
            l.balance = balance_dict.get(l.id, 0)

    @api.multi
    def open_move_action(self):
        move_id = self.move_id.id
        action_obj = \
            self.env.ref(
                'btek_report_accounting.open_account_move_line_so_quy_s07_action')
        action = action_obj.read([])[0]

        action['res_id'] = move_id
        return action

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
              CREATE or REPLACE VIEW {} as (
                SELECT aml.id, aml.move_id,
                 am.company_id, am.state, am.date,
                 aml.account_id,
                am.name chungtu,
                av.recipient_pay
                nguoinhannguoinop,
                CASE
                    WHEN aml.statement_id IS NOT NULL THEN ''
                    ELSE rp.name
                END khachhang,
                aml.name as diengiai,
                SUM(aml.debit) debit,
                SUM(aml.credit) credit

                FROM account_move_line aml
                INNER JOIN account_move am ON aml.move_id = am.id
                LEFT JOIN account_bank_statement abs ON abs.id = aml.statement_id
                LEFT JOIN res_partner rp ON rp.id = aml.partner_id
                LEFT JOIN account_voucher av ON av.move_id = am.id
                LEFT JOIN product_product pp ON pp.id = aml.product_id
                LEFT JOIN account_account aa ON aa.id = aml.account_id

                WHERE aa.code ilike '112%' or aa.code ilike '111%'

                GROUP BY aml.id, aml.move_id,
                 am.company_id, am.state, am.date,
                 aml.account_id, am.date, chungtu,
                 nguoinhannguoinop, khachhang, diengiai
                ORDER BY am.date, debit DESC, chungtu
              )""".format(self._table))

