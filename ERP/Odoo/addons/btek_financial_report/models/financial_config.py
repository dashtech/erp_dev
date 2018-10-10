# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
import datetime
from odoo import SUPERUSER_ID
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx


class btek_financial_statement_account_code(models.Model):
    _name = 'to.financial.statement.account.code'
    _description = 'Financial Statement Account Code'

    @api.multi
    @api.depends('name', 'company_id')
    def _get_account_id(self):
        account_obj = self.env['account.account'].with_context(
            show_parent_account=True, show_all=True)
        for item in self:
            if item.account_id:
                continue

            if not item.name or not item.company_id:
                continue

            accounts = account_obj.search(
                [('code', '=', item.name),
                 ('company_id', '=', item.company_id.id)])

            if accounts:
                item.account_id = accounts[0].id

    @api.multi
    def _set_account_id(self):
        if self.account_id:
            self.name = self.account_id.code

    @api.multi
    @api.onchange('account_id')
    def _onchange_account_id(self):
        if self.account_id:
            self.name = self.account_id.code
            self.company_id = self.env.user.company_id.id

    name = fields.Char(string="code", required=True)
    account_id = fields.Many2one('account.account', store=True,
                                 compute='_get_account_id', inverse='_set_account_id',
                                 string="Account")
    company_id = fields.Many2one('res.company', string="Công ty",
                                 default=1, required=True)

    @api.multi
    def name_get(self):
        res = []
        if self.env.user.id == SUPERUSER_ID:
            for item in self:
                short_name = item.company_id and u'({})'.format(item.company_id.short_name) or ''
                res.append(
                    (item.id, u'{}{}'.format(item.name, short_name))
                )
            return res

        for item in self:
            res.append(
                (item.id, item.name)
            )
        return res

class btek_financial_statement_config(models.Model):
    _inherit = 'account.financial.report'
    _order = 'sequence'

    @api.model
    def get_child_ids(self, account):
        res = [account.id]
        if not account.child_ids:
            return res
        for child in account.child_ids:
            res.extend(self.get_child_ids(child))
        return res

    @api.model
    def _get_included_account_ids(self):
        included_account_ids = []
        for included_accounts in self.to_included_accounts:
            for item in included_accounts.account_id:
                account_ids = self.get_child_ids(item)
                included_account_ids.extend(account_ids)
        if len(included_account_ids) == 1:
            included_account_ids.append(0)

        return (','.join([str(x) for x in included_account_ids])) or False

    @api.model
    def _get_counterpart_accounts_ids(self):
        counterpart_accounts_ids = []
        for counterpart_accounts in self.to_counterpart_accounts:
            for item in counterpart_accounts.account_id:
                account_ids = self.get_child_ids(item)
                counterpart_accounts_ids.extend(account_ids)
        if len(counterpart_accounts_ids) == 1:
            counterpart_accounts_ids.append(0)
        return (','.join([str(x) for x in counterpart_accounts_ids])) or False

    @api.model
    def _get_excluded_accounts_ids(self):
        excluded_accounts_ids = []
        for excluded_accounts in self.to_excluded_accounts:
            for item in excluded_accounts.account_id:
                account_ids = self.get_child_ids(item)
                excluded_accounts_ids.extend(account_ids)
        if len(excluded_accounts_ids) == 1:
            excluded_accounts_ids.append(0)
        return (','.join([str(x) for x in excluded_accounts_ids])) or False

    # @api.one
    # @api.depends('to_included_accounts', 'to_excluded_accounts', 'to_counterpart_accounts')
    # def _get_value(self):
    #     self.to_current_value = self._get_current_value()
    #     self.to_previous_value = self._get_previous_value()

    to_code = fields.Char(string="Code")
    to_notes = fields.Char(string="Notes")
    to_balance_type = fields.Selection([
        ('db', 'Debit'),
        ('cr', 'Credit'),
        ('bl', 'Balance'),
        ('op', 'Cash Flow Opening'),
    ], string="Balance Type")
    to_included_accounts = fields.Many2many('to.financial.statement.account.code',
                                            'to_fs_included_account', 'to_fs_id', 'to_fs_code_id',
                                            string="Included Accounts")
    to_excluded_accounts = fields.Many2many('to.financial.statement.account.code',
                                            'to_fs_excluded_account', 'to_fs_id', 'to_fs_code_id',
                                            string="Excluded Accounts")
    to_counterpart_accounts = fields.Many2many('to.financial.statement.account.code',
                                               'to_fs_counterpart_account', 'to_fs_id', 'to_fs_code_id',
                                               string="Counterpart Accounts")
    to_financial_statement = fields.Selection([
        ('balance_sheet', 'Balance Sheet'),
        ('income_statement', 'Income Statement'),
        ('cash_flow', 'Cash Flow'),
    ], string="Financial Statement")
    to_decision = fields.Selection([
        ('tt200', '200/2014/TT-BTC'),
    ], string="Decision / Circular")
    to_report_type = fields.Selection([
        ('account_balance', 'Account Balance Sheet'),
        ('balance_sheet', 'Balance Sheet'),
        ('income_statement', 'Income Statement'),
        ('cash_flow', 'Cash Flow Statement'),
        ('tax_output', 'Tax Output'),
        ('tax_input', 'Tax Input'),
        ('fs_notes', 'Notes of The Financial Statement'),
    ], string="Report Type", required=True, default='account_balance')

class Export_account_account(models.Model):
    _name= "btek.export.account"

    name = fields.Char(size=64)

    def account_account(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        return self.env['report'].get_action(active_ids, 'export_excel_account')

class Export_excel_account(ReportXlsx):

    _name='report.export_excel_account'

    def generate_xlsx_report(self, workbook, data, partners):

        lst_total = []

        worksheet = workbook.add_worksheet(_('Payslip'))
        worksheet.set_column(0, 0, 15)
        worksheet.set_column(1, 1, 60)
        worksheet.set_column(2, 2, 40)

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

        worksheet.write('A1', u'Tài khoản', title)
        worksheet.write('B1', u'Tên tài khoản', title)
        worksheet.write('C1', u'Loại', title)

        row = row+1

        for partner in partners:
            lst_field = []
            record = self.env['account.account'].browse(partner.id)
            lst_field.append(record.code or '')
            lst_field.append(record.name or '')
            lst_field.append(record.user_type_id.name or '')
            lst_total.append(lst_field)
        for total in lst_total:
            worksheet.write(row, 0, total[0], content_left)
            worksheet.write(row, 1, total[1], content_left)
            worksheet.write(row, 2, total[2], content_left)
            row += 1

Export_excel_account('report.export_excel_account','btek.export.account')