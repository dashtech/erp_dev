# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
import xlwt
from xlwt import Formula
from xlsxwriter.workbook import Workbook
import datetime
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
from odoo.exceptions import UserError
from odoo import tools


class btek_account_account(models.Model):
    _inherit = 'account.account'

    def _get_children_and_consol(self):
        # this function search for all the children and all consolidated children (recursively) of the given account ids
        ids2 = self.search([('parent_id', 'child_of', self.id)])._ids
        ids3 = []
        # for rec in self.browse(ids2):
        #     for child in rec.child_consol_ids:
        #         ids3.append(child.id)
        # if ids3:
        #     ids3 = self._get_children_and_consol(ids3)
        # + ids3
        return ids2

    # Anhtt : Tạm thời tạo hàm mới cho bc
    def _get_children_and_consol_report(self):
        # this function search for all the children and all consolidated children (recursively) of the given account ids
        ids2 = self.search([('parent_id', 'child_of', self.ids)]).ids
        ids3 = []
        # for rec in self.browse(ids2):
        #     for child in rec.child_consol_ids:
        #         ids3.append(child.id)
        # if ids3:
        #     ids3 = self._get_children_and_consol(ids3)
        # + ids3
        return ids2

    @api.model
    def get_report_children_account(self):
        """
        This method return all children of an account. If there are not any children, return the account
        """
        res = []
        ids_acc = self._get_children_and_consol()
        for child_account in self.browse(ids_acc):
            res.append(child_account)
        if not res:
            return [self]
        return res

    @api.model
    def get_report_children_account_ids(self):
        """
        This method return all children of an account. If there are not any children, return the account
        """
        res = []
        ids_acc = self._get_children_and_consol_report()
        for child_account in self.browse(ids_acc):
            res.append(child_account.id)
        if not res:
            return [self]
        return res


class bc_so_cttk(models.TransientModel):
    _name = "bc.so.cttk"
    _description = "Create Report"

    @api.model
    def _get_company(self):
        return self.env.user.company_id

    @api.model
    def _default_currency(self):
        return self.env.user.company_id.currency_id.id

    @api.model
    def _getdate(self):
        return datetime.date(datetime.date.today().year, 1, 1)

    @api.model
    def _gettoday(self):
        return datetime.date.today()

    partner_id = fields.Many2one('res.partner')
    start_date = fields.Date(string='start date', default=_getdate)
    end_date = fields.Date(string='end date', default=_gettoday)
    res_company_id = fields.Many2one('res.company', required=True, default=_get_company)
    # account_account_id = fields.Many2one('account.account',
    #                                      string="Accounts",
    #                                      required=True)
    account_ids = fields.Many2many(
        'account.account', 'bc_so_cttk_account_rel',
        'bc_id', 'account_id', string="Accounts",
        required=True)
    data = fields.Binary('File', readonly=True)
    name = fields.Char('Filename', readonly=True)

    # currency_id = fields.Many2one('res.currency', string='Currency', required=True, default=_default_currency)

    @api.model
    @api.onchange('end_date')
    def onchange_end_date(self):
        if self.start_date > self.end_date:
            self.end_date = self.start_date

    @api.multi
    def get_account_similar(self, accounts):
        account_code_list = accounts.mapped('code')
        # account_code_list = [accounts.code]

        similar = '(' + u'|'.join(account_code_list) + ')%'
        return similar

    @api.multi
    def get_open_balance(self, company_id, accounts,
                         start, end, partner):
        similar = self.get_account_similar(accounts)

        partner_id = 0
        if partner:
            partner_id = partner.id
        # if len(account_id) == 1:
        #     account_id.append(0)
        sql_sodudauki = """
                         SELECT (sum(debit) - sum(credit)) as sodudauki  from account_move_line aml
                             left join res_partner rp on rp.id = aml.partner_id
                             left join account_account aa on aa.id = aml.account_id
                             left join account_move am on am.id = aml.move_id
                            left join account_journal aj on am.journal_id = aj.id
                            where am.date < '%s'
                                  and aa.code similar to '%s'
                                  and am.company_id = %d and
                                  (CASE WHEN %d <> 0 THEN aml.partner_id = %d ELSE 1 = 1 END)
                             """ % (start, similar,
                                    company_id, partner_id, partner_id)
        self.env.cr.execute(sql_sodudauki)
        res = self.env.cr.fetchone()[0] or 0

        return res

    def get_data_from_query(self, kwargs, form):
        def get_parent_code(code, code_list):
            for c in code_list:
                if code.startswith(c):
                    return c
            return False

        sql = self.get_query(kwargs)

        self.env.cr.execute(sql)
        data = self.env.cr.dictfetchall()

        res = dict((account.code, []) for account in form.account_ids)
        for row in data:
            code = row['code']
            c = get_parent_code(code, res.keys())
            if not c:
                continue

            if not res.get(c, False):
                res[c] = []
            res[c].append(row)

        balance_dict = {}

        for code in res.keys():
            accounts = form.env['account.account'].search(
                [('code', '=', code)])
            get_open_balance = self.get_open_balance(
                form.res_company_id.id, accounts,
                form.start_date, form.end_date, form.partner_id)

            balance_dict[code] = get_open_balance

        return res, balance_dict

    def get_query(self, kwargs):
        sql = """
                SELECT * FROM (
                        SELECT A.id, B.code, B.ngaychungtu, B.sochungtu,
                               B.ngayhoadon,B.supplier_invoice_number,
                               B.doituong,A.taikhoan,
                               CASE WHEN A.credit < B.credit_1 THEN A.credit ELSE B.credit_1 END as credit,
                               CASE WHEN A.debit < B.debit_1 THEN A.debit ELSE B.debit_1 END as debit,
                               --A.credit, B.credit_1, A.debit , B.debit_1,
                               A.diengiai,A.move_id, A.x_account_groups,B.x_account_groups
                        FROM
                        (select
                                    aml.id, to_char(am.date,'dd/mm/YYYY') as ngaychungtu,
                                    am.name as sochungtu,
                                    --to_char(ai.registration_date,'dd/mm/YYYY') as ngayhoadon,
                                    (CASE WHEN ai.date_invoice is not null THEN to_char(ai.date_invoice,'dd/mm/YYYY') ELSE to_char(am.date,'dd/mm/YYYY') END) as ngayhoadon,
                                    --ai.supplier_invoice_number,
                                    (CASE WHEN ai.supplier_invoice_number is not null THEN ai.supplier_invoice_number ELSE am.ref END) as supplier_invoice_number,
                                    rp.name as doituong,
                                    --av.name as diengiai,
                                    aa.code as taikhoan,
                                    aml.debit credit, aml.credit debit,
                                    concat_ws('; ',aml.name
                                    , pt.name, am.name) diengiai, aml.move_id, aml.x_account_groups

                                    from account_move_line aml
                                    JOIN account_move am on am.id = aml.move_id
                                    left join product_product pp on pp.id = aml.product_id
                                    left join product_template pt on pp.product_tmpl_id = pt.id
                                    LEFT JOIN res_partner rp on rp.id = aml.partner_id
                                    LEFT JOIN account_account aa on aa.id = aml.account_id
                                    LEFT JOIN account_invoice ai on ai.move_id = am.id
                                    Left join account_journal aj on am.journal_id = aj.id
                                    WHERE
                                        am.id in (
                                            select distinct move_id from account_move_line aml
                                            left join account_move am on am.id = aml.move_id
                                            left join account_account aa on aa.id = aml.account_id
                                            Left join account_journal aj on am.journal_id = aj.id
                                            where aa.code similar to '{similar}' and (aj.type != 'situation' )
                                            and '{start}' <= am.date::date and am.date::date <= '{end}'
                                            and am.company_id = {company_id}
                                            order by move_id
                                        ) and
                                        '{start}' <= am.date and am.date <= '{end}'

                                        and aa.code not similar to '{similar}'
                                    order by am.date, aml.move_id) A
                                    LEFT JOIN
                                    (select aml.id,
                                            aa.code,
                                            to_char(am.date,'dd/mm/YYYY') as ngaychungtu,
                                            am.name as sochungtu,
                                            --to_char(ai.registration_date,'dd/mm/YYYY') as ngayhoadon,
                                            (CASE WHEN ai.date_invoice is not null THEN to_char(ai.date_invoice,'dd/mm/YYYY') ELSE to_char(am.date,'dd/mm/YYYY') END) as ngayhoadon,
                                            --ai.supplier_invoice_number,
                                            (CASE WHEN ai.supplier_invoice_number is not null THEN ai.supplier_invoice_number ELSE am.ref END) as supplier_invoice_number,
                                            rp.name as doituong,
                                            --av.name as diengiai,
                                            aa.code as taikhoan,
                                            aml.debit debit_1, aml.credit credit_1,
                                            concat_ws('; ',aml.name
                                            , pt.name, am.name) diengiai, aml.move_id, aml.x_account_groups

                                            from account_move_line aml
                                            JOIN account_move am on am.id = aml.move_id
                                            left join product_product pp on pp.id = aml.product_id
                                            left join product_template pt on pp.product_tmpl_id = pt.id
                                            LEFT JOIN res_partner rp on rp.id = aml.partner_id
                                            LEFT JOIN account_account aa on aa.id = aml.account_id
                                            LEFT JOIN account_invoice ai on ai.move_id = am.id
                                            Left join account_journal aj on am.journal_id = aj.id
                                            WHERE
                                                (CASE WHEN {partner_id} <> 0 THEN aml.partner_id = {partner_id} ELSE 1 = 1 END) and
                                                am.id in (
                                                    select distinct move_id from account_move_line aml
                                                    left join account_move am on am.id = aml.move_id
                                                    Left join account_journal aj on am.journal_id = aj.id
                                                    left join account_account aa on aa.id = aml.account_id
                                                    where aa.code similar to '{similar}' and (aj.type != 'situation' )
                                                    and '{start}' <= am.date::date and am.date::date <= '{end}'
                                                    and am.company_id = {company_id}
                                                    order by move_id
                                                ) and
                                                '{start}' <= am.date and am.date <= '{end}'

                                                and aa.code similar to '{similar}'
                                            order by am.date, aml.move_id) B
                                         ON A.move_id = B.move_id AND ((A.x_account_groups is NULL AND A.x_account_groups is NULL) OR A.x_account_groups=B.x_account_groups)
                                        WHERE  ((A.credit + B.credit_1) <> 0 AND (A.debit + B.debit_1) = 0) OR ((A.credit + B.credit_1) = 0 AND (A.debit + B.debit_1) <> 0) AND (credit + debit) <> 0 ) A_B
                                        WHERE (credit + debit) <> 0
                       """.format(**kwargs)
        return sql

    # def _get_data_doi_ung(self, company_id, account_ids, start, end, partner):
    #     partner_id = 0
    #     if partner:
    #         partner_id = partner.id
    #     if len(account_ids) == 1:
    #         account_ids.append(0)
    #
    #         """.format(start=start, end=end, company_id=company_id,
    #                    account_ids=tuple(account_ids), partner_id=partner_id)
    #     self.env.cr.execute(sql)
    #     return self.env.cr.dictfetchall()

    def action_print_doi_ung(self):
        return self.env['report'].get_action(
            self, 'btek_report_accounting.sochitiettk_report')

    @api.multi
    def preview_excel(self):
        datas = {'ids': self.ids}
        datas['model'] = self._name

        report_name = 'btek_report_accounting.sochitiettk_report'
        res = self.env['ir.actions.report.xml'
        ].preview_xlsx_report(report_name, self._ids, datas)
        return res

    @api.multi
    def view_report(self):
        action_obj = self.env.ref('btek_report_accounting.account_move_line_so_cttk_action')
        action = action_obj.read([])[0]

        form = self
        accounts = form.account_ids
        similar = self.get_account_similar(accounts)

        partner_id = 0
        if form.partner_id:
            partner_id = form.partner_id.id

        args = {
            'start': form.start_date,
            'end': form.end_date,
            'company_id': form.res_company_id.id,
            'similar': similar,
            'partner_id': partner_id,
        }

        res, balance_dict = \
            self.get_data_from_query(
                args, form)

        ml_ids = []
        balance = {}
        for c in res.keys():
            for row in res[c]:
                if not row['id'] or row['id'] in ml_ids:
                    continue
                ml_ids.append(row['id'])
                balance[row['id']] = row

        action['domain'] = [('id', 'in', ml_ids)]
        action['context'] = {'balance': balance}

        return action


class Sochitiettaikhoanreport(ReportXlsx):
    _name = 'report.btek_report_accounting.sochitiettk_report'

    def write_sochitiettaikhoan(self, ws, datas, form):
        ws.set_column(0, 0, 13)
        ws.set_column(1, 1, 22)
        ws.set_column(2, 2, 13)
        ws.set_column(3, 3, 17)
        ws.set_column(4, 4, 35)
        ws.set_column(5, 5, 35)
        ws.set_column(6, 6, 16)
        ws.set_column(7, 7, 16)
        ws.set_column(8, 8, 16)
        ws.set_column(9, 9, 15)
        ws.set_column(10, 10, 15)
        ws.set_column(11, 11, 15)
        ws.set_column(12, 12, 15)
        ws.set_column(13, 13, 15)
        ws.set_column(14, 14, 15)
        ws.set_row(7, 40)

        address = ''
        if form.res_company_id.street: address = form.res_company_id.street
        if form.res_company_id.street2: address = address + ', ' + form.res_company_id.street2
        if form.res_company_id.city: address = address + ', ' + form.res_company_id.city
        if form.res_company_id.country_id.name: address = address + ', ' + form.res_company_id.country_id.name
        mst = form.res_company_id.vat

        start = form.start_date
        end = form.end_date

        # if form.account_account_id:
        #     account_ids = form.account_account_id.child_ids.ids or [0]
        #     account_ids.append(form.account_account_id.id)
        # if len(account_ids) == 1: account_ids.append(0)

        accounts = form.account_ids

        # get_open_balance = self.get_open_balance(
        #     form.res_company_id.id, accounts,
        #     start, end, form.partner_id)

        # if get_open_balance['sodudauki'] == None:
        #     get_open_balance['sodudauki'] = 0

        # Header
        ws.write("A1", u'Đơn vị báo cáo :', )
        ws.write("A2", u'Địa chỉ :', )
        ws.write("A4", u'MST :', )
        ws.merge_range("B1:E1", unicode(form.res_company_id.name) or '', self.bold)
        ws.merge_range("B2:E3", unicode(address) or '', self.bold)
        ws.merge_range("B4:C4", mst or '', self.bold)

        string_lable = u"SỔ CHI TIẾT TÀI KHOẢN"
        ws.merge_range("D5:F5", string_lable, self.title)

        account_name_get = []
        for account in accounts:
            account_name_get.append(
                u'{} - {}'.format(account.code, account.name)
            )
        account_code_name = u','.join(account_name_get)

        ws.merge_range("D6:F6",
                       u"Tài khoản : {}".format(account_code_name),
                       self.text_center)
        if start and end:
            start_view = datetime.datetime.strptime(start, '%Y-%m-%d').strftime('%d/%m/%Y').decode('unicode-escape')
            end_view = datetime.datetime.strptime(end, '%Y-%m-%d').strftime('%d/%m/%Y').decode('unicode-escape')
            ws.merge_range("D7:F7", u" Từ ngày: " + start_view + u" đến ngày: " + end_view + u"", self.text_center)

        # Header Table

        ws.merge_range("A9:D9", u"Chứng từ", self.table_header)
        ws.merge_range("E9:E10", u"Đối tượng", self.table_header)
        ws.merge_range("F9:F10", u"Diễn giải", self.table_header)
        ws.merge_range("G9:G10", u"Tài khoản đối ứng", self.table_header)
        ws.merge_range("H9:H10", u"Phát sinh nợ", self.table_header)
        ws.merge_range("I9:I10", u"Phát sinh có", self.table_header)
        ws.write("A10", u"Ngày", self.table_header)
        ws.write("B10", u"Số chứng từ", self.table_header)
        ws.write("C10", u"Ngày hóa đơn", self.table_header)
        ws.write("D10", u"Số hóa đơn", self.table_header)


        account_dict,balance_dict = datas
        row = 11

        if not account_dict.keys():
            return

        for account in accounts:
            sum_debit = 0
            sum_credit = 0

            data = account_dict.get(account.code, [])

            if not data:
                continue

            balance = balance_dict.get(account.code, 0)

            ws.merge_range("A{}:B{}".format(row, row),
                           u"Tài khoản: {}".format(account.code),
                           self.table_header)

            if balance > 0:
                ws.write("G{}".format(row), u"Dư nợ đầu kỳ:",
                         self.table_header)
                ws.write("H{}".format(row), balance,
                         self.table_row_right)
            if balance < 0:
                ws.write("G{}".format(row), u"Dư có đầu kỳ:",
                         self.table_header)
                ws.write("I{}".format(row), balance * -1,
                         self.table_row_right)
            if balance == 0:
                ws.write("G{}".format(row), u"Dư đầu kỳ:",
                         self.table_header)
                ws.write("H{}".format(row), 0,
                         self.table_row_right)

            row += 1

            for r in data:
                sum_debit += r['debit']
                sum_credit += r['credit']
                ws.write("A{row}".format(row=row), r['ngaychungtu'] or '', self.center)
                ws.write("B{row}".format(row=row), r['sochungtu'] or '', self.table_row_left)
                ws.write("C{row}".format(row=row), r['ngayhoadon'] or '', self.center)
                ws.write("D{row}".format(row=row), r['supplier_invoice_number'] or '', self.table_row_left)
                ws.write("E{row}".format(row=row), r['doituong'] or '', self.table_row_left)
                ws.write("F{row}".format(row=row), r['diengiai'] or '', self.table_row_left)
                ws.write("G{row}".format(row=row), r['taikhoan'] or '', self.table_row_left)
                ws.write("H{row}".format(row=row), r['debit'] or 0, self.table_row_right)
                ws.write("I{row}".format(row=row), r['credit'] or 0, self.table_row_right)
                row += 1
            ws.write("G{row}".format(row=row), u"Phát sinh trong kỳ", self.bold)
            ws.write("H{row}".format(row=row), sum_debit, self.table_row_right)
            ws.write("I{row}".format(row=row), sum_credit, self.table_row_right)

            row += 1
            ws.write("G{row}".format(row=row), u"Số dư cuối kỳ", self.bold)
            close_balance = balance + sum_debit - sum_credit

            if close_balance < 0:
                close_balance = '({})'.format(
                    '{:0,.2f}'.format(-close_balance))

            ws.write("H{row}".format(row=row), close_balance,
                     self.table_row_right)
            ws.write("I{row}".format(row=row), '',
                     self.table_row_right)

            row += 1

            # if close_balance >= 0:
            #     ws.write("H{row}".format(row=row + 1), close_balance, self.table_row_right)
            #     ws.write("I{row}".format(row=row + 1), '', self.table_row_right)
            # else:
            #     ws.write("H{row}".format(row=row + 1), '', self.table_row_right)
            #     ws.write("I{row}".format(row=row + 1), close_balance * -1, self.table_row_right)

    def generate_xlsx_report(self, wb, data, form):
        reports = {
            'report': self.write_sochitiettaikhoan,
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
        # if form.account_account_id:
        #     account_ids = form.account_account_id.child_ids.ids or [0]
        #     account_ids.append(form.account_account_id.id)
        # if len(account_ids) == 1: account_ids.append(0)

        accounts = form.account_ids
        similar = form.get_account_similar(accounts)

        partner_id = 0
        if form.partner_id:
            partner_id = form.partner_id.id

        args = {
            'start': form.start_date,
            'end': form.end_date,
            'company_id': form.res_company_id.id,
            'similar': similar,
            'partner_id': partner_id,
        }
        report_data = form.get_data_from_query(args, form)
        reports['report'](ws, report_data, form)


Sochitiettaikhoanreport('report.btek_report_accounting.sochitiettk_report', 'bc.so.cttk')


class account_move_line_so_cttk(models.Model):
    _name = 'account.move.line.so.cttk'
    _auto = False

    ngaychungtu = fields.Date('Voucher date') #am.date
    name = fields.Char('Voucher number') #am.name
    ngayhoadon = fields.Date('Invoice date') #ai.date_invoice or am.date
    supplier_invoice_number = fields.Char('Invoice number') # ai.supplier_invoice_number or am.ref
    doituong = fields.Many2one('res.partner', 'Partner') # aml.partner_id
    move_id = fields.Many2one('account.move', 'Move')
    diengiai = fields.Char('Explain', compute='_compute_A') # A.diengiai
    taikhoan = fields.Char('Account', compute='_compute_A') # A.taikhoan
    debit = fields.Float('Debit', compute='_compute_A') # A.debit
    credit = fields.Float('Credit', compute='_compute_A') # A.credit

    @api.multi
    def _compute_A(self):
        balance = self.env.context.get('balance', False)
        if not balance:
            return

        for line in self:
            for f in ['diengiai', 'taikhoan', 'debit', 'credit']:
                setattr(line, f, balance.get(str(line.id), {}).get(f, False))

    @api.model_cr
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW {} as (
                select ml.id, ml.move_id,
                am.date as ngaychungtu,
                am.name,
                case when ai.date_invoice is not null
                then ai.date_invoice else am.date end as ngayhoadon,
                case when ai.supplier_invoice_number is not null then
                ai.supplier_invoice_number else am.ref end as supplier_invoice_number,
                ml.partner_id as doituong
                FROM account_move_line as ml
                  left join account_move as am on am.id = ml.move_id
                  left join account_invoice as ai on ai.move_id = am.id
                )""".format(self._table))

    @api.model
    def open_move_action(self):
        action_obj = self.env.ref('btek_report_accounting.open_account_move_so_cttk_action')
        action = action_obj.read([])[0]
        action['res_id'] = self.move_id.id
        return action

