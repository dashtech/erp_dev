# -*- coding: utf-8 -*-

from odoo import api, fields, models

class to_account_common_report(models.Model):
    _name = 'to.account.common.report'
    _inherit = 'account.common.report'

    to_decision = fields.Selection(
                                   [
                                    ('tt200', '200/2014/TT-BTC')
                                    ],
                                   'Decision / Circular',
                                   default='tt200',
                                   required=True
                                   )

    to_report_type = fields.Selection([
        ('account_balance', 'Account Balance Sheet'),
        ('balance_sheet', 'Balance Sheet'),
        ('income_statement', 'Income Statement'),
        ('cash_flow', 'Cash Flow Statement'),
        ('tax_output', 'Tax Output'),
        ('tax_input', 'Tax Input'),
        ('fs_notes', 'Notes of The Financial Statement'),
    ], string="Report Type", required=True, default='account_balance')