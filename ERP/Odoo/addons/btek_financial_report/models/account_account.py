# -*- coding: utf-8 -*-
##############################################################################
#
#    @package to_vn_legal_financial_reports TO Vietnam Legal Financial Reports for Odoo 8.0
#    @copyright Copyright (C) 2015 T.V.T Marine Automation (aka TVTMA). All rights reserved.#
#    @license http://www.gnu.org/licenses GNU Affero General Public License version 3 or later; see LICENSE.txt
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import models, api
import datetime
from  calendar import monthrange
from dateutil.relativedelta import relativedelta

SUPERUSER_ID = 1


class account_account(models.Model):
    _inherit = 'account.account'

    @api.model
    def _report_opening_balance(self, account, data):
        move_state = ['draft', 'posted']
        if data['form'].get('target_move', 'all') == 'posted':
            move_state = ['posted', '']
        account = int(account)
        sum_balance = 0
        sql = """
                SELECT sum(debit) - sum(credit) as tot_balance
                    FROM account_move_line l
                    JOIN account_move am ON (am.id = l.move_id)
                    WHERE (l.account_id = %s)
                    AND (am.state IN %s)
                    AND (am.date < date('%s'))
            """ % (account, tuple(move_state), data['form']['date_from'])
        self._cr.execute(sql)
        sum_balance += self._cr.fetchone()[0] or 0.0

        return sum_balance

    @api.model
    def _report_opening_balance_op(self, account, data):
        move_state = ['draft', 'posted']
        if data['form'].get('target_move', 'all') == 'posted':
            move_state = ['posted', '']
        account = int(account)
        sum_balance = 0
        start = str(int(data['form']['date_from'][:4])-1)+'-01-01'
        end =   str(int(data['form']['date_from'][:4])-1)+'-12-31'
        sql = """
                SELECT sum(debit) - sum(credit) as tot_balance
                    FROM account_move_line l
                    JOIN account_move am ON (am.id = l.move_id)
                    WHERE (l.account_id = %s)
                    AND (am.state IN %s)
                    AND am.date BETWEEN '%s'::date AND '%s'::date
            """ % (account, tuple(move_state), start, end)
        self._cr.execute(sql)
        sum_balance += self._cr.fetchone()[0] or 0.0

        return sum_balance

    @api.model
    def _report_opening_balance_for_type(self, account, data, type):
        move_state = ['draft', 'posted']
        if data['form'].get('target_move', 'all') == 'posted':
            move_state = ['posted', '']
        account = int(account)
        if type == 'db':
            colum = 'sum(debit)'
        if type == 'cr':
            colum = 'sum(credit)'
        if type == 'bl':
            colum = 'sum(debit) - sum(credit)'
        sum_balance = 0
        sql = """
                SELECT %s as tot_balance
                    FROM account_move_line l
                    JOIN account_move am ON (am.id = l.move_id)
                    WHERE (l.account_id = %s)
                    AND (am.state IN %s)
                    AND am.date BETWEEN '%s'::date AND '%s'::date
            """ % (colum, account, tuple(move_state), data['form']['date_from'], data['form']['date_to'])
        self._cr.execute(sql)
        sum_balance += self._cr.fetchone()[0] or 0.0

        return sum_balance
