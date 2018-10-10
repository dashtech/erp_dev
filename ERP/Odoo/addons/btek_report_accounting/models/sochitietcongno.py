#!/usr/bin/python
# -*- encoding: utf-8 -*-
# ANHTT
from odoo import api, fields, models, _, tools
import datetime
import time


class SoChiTietCongNo(models.TransientModel):
    _name = 'so.chi.tiet.congno'

    @api.model
    def _getdate(self):
        return datetime.date(datetime.date.today().year, 1, 1)

    @api.model
    def _gettoday(self):
        return datetime.date.today()

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    result_selection = fields.Selection([('customer', 'Receivable Accounts'),
                                         ('supplier', 'Payable Accounts'),
                                         ('customer_supplier', 'Receivable and Payable Accounts')
                                         ], string="Partner's", required=True, default='customer')
    #
    # type_account = fields.Selection([('receivable', 'Receivable Accounts'),
    #                                      ('payable', 'Payable Accounts'),
    #                                      ], string=u"Loại tài khoản", required=True)
    start_date = fields.Date(default=_getdate,required=True)
    end_date = fields.Date(default=_gettoday,required=True)

    company_id = fields.Many2one('res.company', required=True, default=_get_company)
    type_entries = fields.Selection([('filter_posted', 'All Post Entries'), ('filter_all', 'All Entries')], "Type",
                                    default='filter_posted', required=True)
    # account_account_id = fields.Many2one('account.account',
    #                                      string="Accounts")
    account_ids = fields.Many2many(
        'account.account', 'so_chi_tiet_congno_rel',
        'so_ct_id', 'account_id', string="Accounts")

    # @api.onchange('type_account')
    # def onchange_type_account(self):
    #     a = 1

    @api.onchange('account_ids', 'result_selection')
    def onchange_type(self):
        if self.result_selection == 'customer':
            return {'domain': {'account_ids': [('user_type_id.type', '=', 'receivable')]}}
        if self.result_selection == 'supplier':
            return {'domain': {'account_ids': [('user_type_id.type', '=', 'payable')]}}
        else:
            return {'domain': {'account_ids': [('user_type_id.type', 'in', ('receivable','payable'))]}}

    def get_account_ids(self):
        account_list = []
        if self.account_ids:
            for account_id in self.account_ids:
                account_list.extend(account_id.child_ids.ids or [0])
                account_list.append(account_id.id)
        else:
            if self.result_selection == 'customer':
                account_list = self.env['account.account'].search(
                    [('user_type_id.type', '=', 'receivable'),
                     ('company_id', '=', self.company_id.id)]).ids or [0, 0]
            if self.result_selection == 'supplier':
                account_list = self.env['account.account'].search(
                    [('user_type_id.type', '=', 'payable'),
                     ('company_id', '=', self.company_id.id)]).ids or [0, 0]
            if self.result_selection == 'customer_supplier':
                account_list = self.env['account.account'].search(
                    [('user_type_id.type', 'in', ('receivable', 'payable')),
                     ('company_id', '=', self.company_id.id)]).ids or [0, 0]
        if len(account_list) == 1:
            account_list.append(0)
        return account_list

    def get_data_from_query(self):
        account_list = self.get_account_ids()
        args = {
            'start': self.start_date,
            'end': self.end_date,
            'type': self.type_entries,
            'account_ids': tuple(account_list),
            'company_id': self.company_id.id,
            'date_daunam': time.strftime('%Y-01-01'),
        }

        sql = self.get_query(args)
        self.env.cr.execute(sql)
        data = self.env.cr.dictfetchall()

        return data

    def get_query(self, kwargs):
        sql = """
        SELECT *, Case when tab.dauky >= 0 then tab.dauky ELSE 0 END  as nodauky,
        Case when tab.dauky < 0 then tab.dauky ELSE 0 END as codauky,
        case when tab.dauky + tab.debit - tab.credit > 0 then tab.dauky + tab.debit - tab.credit else 0 end as nocuoiky,
        case when tab.dauky + tab.debit - tab.credit < 0 then tab.dauky + tab.debit - tab.credit else 0 end as cocuoiky
        FROM
        (
        SELECT max(aml.id) as id, aa.code as code,
            rp.id as partner_id, rp.name as name, rp.code as ma_kh ,
            (select COALESCE(sum(debit-credit),0) as dauky from account_move_line left join account_move on account_move.id = account_move_line.move_id
                        where account_move.date < '{start}' and account_move_line.account_id = aa.id
                        and account_move_line.partner_id = rp.id
                    ),
            (select COALESCE(sum(debit),0) as debit from account_move_line left join account_move on account_move.id = account_move_line.move_id
                        where '{start}' <= account_move.date and account_move.date <= '{end}' and account_move_line.account_id = aa.id
                        and account_move_line.partner_id = rp.id
                    ),
            (select COALESCE(sum(credit),0) as credit from account_move_line left join account_move on account_move.id = account_move_line.move_id
                        where '{start}' <= account_move.date and account_move.date <= '{end}' and account_move_line.account_id = aa.id
                        and account_move_line.partner_id = rp.id
                    )
            from account_move_line aml
                left join res_partner rp on rp.id = aml.partner_id
                left join account_account aa on aa.id = aml.account_id
                left join account_move am on am.id = aml.move_id
                where (CASE WHEN '{type}' = 'filter_posted' THEN am.state in ('posted') ELSE am.state in  ('posted','draft') END)
                     and aa.id in {account_ids} and am.company_id = {company_id}
                group by rp.id,rp.name, rp.code, aa.code, aa.id
            ) as tab
        WhERE tab.id is not null
        order by tab.code, tab.name
        """.format(**kwargs)

        return sql

    @api.multi
    def action_print(self):
        return self.env['report'].get_action(
            self, 'btek_report_accounting.sochitiet_report')

    @api.multi
    def preview_excel(self):
        datas = {'ids': self.ids}
        datas['model'] = self._name

        report_name = 'btek_report_accounting.sochitiet_report'
        res = self.env['ir.actions.report.xml'
        ].preview_xlsx_report(report_name, self._ids, datas)
        return res

    @api.multi
    def view_report(self):
        data = self.get_data_from_query()
        balance = {}
        ids = []
        for row in data:
            key = u'{},{}'.format(row['partner_id'], row['code'])
            balance[key] = row
            ids.append(row['id'])

        action_obj = \
            self.env.ref(
                'btek_report_accounting.res_partner_so_chi_tiet_cong_no_action')
        action = action_obj.read([])[0]
        action['context'] = {
            'balance': balance,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'type_entries': self.type_entries,
            'account_ids': self.get_account_ids(),
            'wizard_id': self[0].id
        }
        action['domain'] = [('id', 'in', ids)]

        return action

from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
class Sochitietcongnoreport(ReportXlsx):
    _name = 'report.btek_report_accounting.sochitiet_report'

    def write_sochitietcongno(self, ws, data, form):
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
        address = u''
        if form.company_id.street: address = form.company_id.street
        if form.company_id.street2: address = address + ', ' + unicode(form.company_id.street2)
        if form.company_id.city: address = address + ', ' + unicode(form.company_id.city)
        ws.write('A%s' % 1, u'Đơn vị báo cáo:', )
        ws.merge_range('B1:E1', form.company_id.name, self.xxxxx)
        ws.write('A%s' % 2, u'Địa chỉ:', )
        ws.merge_range('B2:E2', address, self.xxxxx)
        ws.merge_range('A4:I4', u'SỔ CHI TIẾT CÔNG NỢ', self.title)
        ws.merge_range('A6:I6', u'Từ ngày: ' + unicode(datetime.datetime.strptime(form.start_date, '%Y-%m-%d').strftime('%d/%m/%Y'))
                       + u' Đến ngày: ' + unicode(datetime.datetime.strptime(form.end_date, '%Y-%m-%d').strftime('%d/%m/%Y')), self.header)

        row = 8
        # ws.write('B%s' % row, u'Chọn', self.table_header)
        ws.write('A%s' % row, u'Mã khách hàng', self.table_header)
        ws.write('B%s' % row, u'Tên khách hàng', self.table_header)
        ws.write('C%s' % row, u'Tài khoản', self.table_header)
        ws.write('D%s' % row, u'Dư nợ đầu kỳ', self.table_header)
        ws.write('E%s' % row, u'Dư có đầu kỳ', self.table_header)
        ws.write('F%s' % row, u'Ps Nợ', self.table_header)
        ws.write('G%s' % row, u'Ps Có', self.table_header)
        ws.write('H%s' % row, u'Dư nợ cuối kỳ', self.table_header)
        ws.write('I%s' % row, u'Dư có cuối kỳ', self.table_header)

        row = 10
        sum_nodau = sum_codau = sum_psno = sum_psco = sum_nocuoi = sum_cocuoi = 0
        if data:
            for r in data:
                if r['nodauky'] != 0 or (r['codauky']) != 0 or (r['debit']) != 0 or (r['credit']) != 0 or r['nocuoiky'] != 0 or r['cocuoiky'] != 0:
                    # ws.write("B{row}".format(row=row), 'True', self.table_row_left)
                    ws.write("A{row}".format(row=row), r['ma_kh'] or '', self.table_row_left)
                    ws.write("B{row}".format(row=row), r['name'] or '', self.table_row_left)
                    ws.write("C{row}".format(row=row), r['code'] or '', self.table_row_left)
                    ws.write("D{row}".format(row=row), abs(r['nodauky']) or '', self.table_row_right)
                    ws.write("E{row}".format(row=row), abs(r['codauky']) or '', self.table_row_right)
                    ws.write("F{row}".format(row=row), abs(r['debit']) or '', self.table_row_right)
                    ws.write("G{row}".format(row=row), abs(r['credit']) or '', self.table_row_right)
                    ws.write("H{row}".format(row=row), abs(r['nocuoiky']) or '', self.table_row_right)
                    ws.write("I{row}".format(row=row), abs(r['cocuoiky']) or '', self.table_row_right)

                    if r['nodauky']: sum_nodau += abs(r['nodauky'])
                    if r['codauky']: sum_codau += abs(r['codauky'])
                    if r['debit']: sum_psno += abs(r['debit'])
                    if r['credit']: sum_psco += abs(r['credit'])
                    if r['nocuoiky']: sum_nocuoi += abs(r['nocuoiky'])
                    if r['cocuoiky']: sum_cocuoi += abs(r['cocuoiky'])

                    row = row + 1
            l = row
            row = 9

            # ws.write("B{row}".format(row=row), 'False', self.table_row_left_bold)
            ws.write("A{row}".format(row=row), '', self.table_row_left)
            ws.write("B{row}".format(row=row), '', self.table_row_left)
            ws.write("C{row}".format(row=row), u'Tổng cộng:' or '', self.table_row_left_bold)
            ws.write("D{row}".format(row=row), sum_nodau, self.table_row_right_bold)
            ws.write("E{row}".format(row=row), sum_codau, self.table_row_right_bold)
            ws.write("F{row}".format(row=row), sum_psno, self.table_row_right_bold)
            ws.write("G{row}".format(row=row), sum_psco, self.table_row_right_bold)
            ws.write("H{row}".format(row=row), sum_nocuoi, self.table_row_right_bold)
            ws.write("I{row}".format(row=row), sum_cocuoi, self.table_row_right_bold)

    def generate_xlsx_report(self, wb, data, form):
        reports = {
            'report': self.write_sochitietcongno,
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

        report_data = form.get_data_from_query()
        reports['report'](ws, report_data, form)

Sochitietcongnoreport('report.btek_report_accounting.sochitiet_report', 'so.chi.tiet.congno')


class ResPartnerSoChiTietCongNo(models.Model):
    _name = 'res.partner.so.chi.tiet.cong.no'
    _auto = False

    name = fields.Char('Customer name')
    code = fields.Char('Account')
    ma_kh = fields.Char('Customer code')
    partner_id = fields.Many2one('res.partner', 'Partner')
    nodauky = fields.Float(compute='_compute_balance',
                           string='Start debit')
    dauky = fields.Float(compute='_compute_balance')
    cocuoiky = fields.Float(compute='_compute_balance',
                            string='End credit')
    credit = fields.Float(compute='_compute_balance',
                          string='Period credit')
    codauky = fields.Float(compute='_compute_balance',
                           string='Start credit')
    debit = fields.Float(compute='_compute_balance',
                         string='Period debit')
    nocuoiky = fields.Float(compute='_compute_balance',
                            string='End debit')
    wizard_id = fields.Many2one('so.chi.tiet.congno',
                                compute='_compute_balance')

    @api.multi
    def _compute_balance(self):
        balance = self.env.context.get('balance', False)
        if not balance:
            return

        for p in self:
            key = u'{},{}'.format(p.partner_id.id, p.code)
            p_balance = balance.get(key) or {}
            for f in ['nodauky', 'dauky', 'cocuoiky', 'credit',
                      'codauky', 'debit', 'nocuoiky']:
                setattr(p, f, p_balance.get(f, 0) or 0)
            p.wizard_id = self.env.context.get('wizard_id', False)

    @api.multi
    def open_move_line_action(self):
        wizard_ids = \
            self.env['so.chi.tiet.congno'].search(
                [('create_uid', '=', self.env.user.id)],
                limit=1,
                order='create_date desc'
            )
        wizard_id = wizard_ids and wizard_ids[0] or False

        action_obj = \
            self.env.ref(
                'btek_report_accounting.open_res_partner_so_chi_tiet_cong_no_action')
        action = action_obj.read([])[0]

        # start_date = self.env.context.get('start_date', False)
        # end_date = self.env.context.get('end_date', False)
        # type_entries = self.env.context.get('type_entries', False)
        # account_ids = self.env.context.get('account_ids', False)

        start_date = wizard_id and wizard_id.start_date or False
        end_date = wizard_id and wizard_id.end_date or False
        type_entries = wizard_id and wizard_id.type_entries or False
        account_ids = wizard_id and wizard_id.get_account_ids() or False

        domain = [('company_id', '=', self.env.user.company_id.id),
                  ('account_id', 'in', account_ids),
                  ('partner_id', '=', self.partner_id.id)]
        if type_entries == 'filter_posted':
            domain.append(
                ('move_id.state', '=', 'posted')
            )
        if start_date:
            domain.append(
                ('move_id.date', '>=', start_date)
            )
        if end_date:
            domain.append(
                ('move_id.date', '<=', end_date)
            )

        action['domain'] = domain
        return action

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
          CREATE or REPLACE VIEW {} as (
            select max(aml.id) as id,
            rp.id as partner_id,
            rp.name as name,
            rp.code as ma_kh,
            aa.code as code
            from account_move_line aml
                left join res_partner rp on rp.id = aml.partner_id
                left join account_account aa on aa.id = aml.account_id
                left join account_account_type t on aa.user_type_id = t.id
                left join account_move am on am.id = aml.move_id
                where
                     t.type in ('receivable', 'payable')
                group by rp.id, aa.id
          )""".format(self._table))


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    def open_move_action(self):
        action_obj = self.env.ref('account.action_move_journal_line')
        action = action_obj.read([])[0]

        action['res_id'] = self.move_id.id
        action['view_mode'] = 'form'
        action['views'] = [(False, u'form')]

        # action['target'] = 'new'
        return action
