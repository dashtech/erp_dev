# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import AccessDenied, UserError
import odoo.addons.decimal_precision as dp
import datetime


class closing_entry_config(models.Model):
    _name = 'closing.entry.configs'
    _description = 'Closing Entry Configuration'
    _order = 'sequence'

    @api.one
    @api.depends('origin_account_code', 'forward_account_code')
    def _get_account_id(self):
        origin_accounts = \
            self.env['account.account'].with_context(
                show_parent_account=True).search(
                [('code', '=', self.origin_account_code)]
            )

        # if not origin_accounts:
        #     raise UserError(('No Account! Cannot find account code in chart of account of your company!'))
        forward_account_id = \
            self.env['account.account'].with_context(
                show_parent_account=True).search(
                [('code', '=', self.forward_account_code)]
            )
        # if not forward_account_id:
        #     raise UserError(('No Account! Cannot find account code in chart of account of your company!'))
        origin_account_id = origin_accounts and origin_accounts[0].id or False

        self.origin_account_id = origin_account_id
        self.forward_account_id = \
            forward_account_id and forward_account_id[0].id or False

    name = fields.Char(string="Entry Name", required=True, translate=True)
    code = fields.Char(string="Entry Code", translate=True)
    forward_type = fields.Selection([('cr_db', 'Credit -> Debit'), ('db_cr', 'Debit -> Credit'), (('mix', 'Mixed'))],
                                    string="Forward Type")
    origin_account_code = fields.Char(string="Origin Account", requird=True)
    forward_account_code = fields.Char(string="Forward Account", requird=True)
    origin_account_id = fields.Many2one('account.account', store=True, compute='_get_account_id',
                                        string="Origin Account")
    forward_account_id = fields.Many2one('account.account', store=True, compute='_get_account_id',
                                         string="Forward Account")
    profit_loss = fields.Boolean(string="Profit/Loss")
    sequence = fields.Integer(string="Sequence", size=100)
    company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env.user.company_id)


class closing_entry_line(models.Model):
    _name = 'closing.entry.line'
    _description = 'Closing Entry Line'

    closing_entry_id = fields.Many2one('closing.entry', string="Closing Entry")
    name = fields.Char(string="Name", required=True)
    account_id = fields.Many2one('account.account', string="Account", required=True)
    debit = fields.Float(string="Debit")
    credit = fields.Float(string="Credit")
    company_id = fields.Many2one('res.company', related='closing_entry_id.company_id', store=True,
                                 readonly=1, requied=True)
    x_group = fields.Integer('Group Account')


class closing_entry(models.Model):
    _name = 'closing.entry'
    _description = 'Closing Entry'
    _inherit = ['mail.thread']

    name = fields.Char(string="Entry Name", required=True, readonly=True, states={'draft': [('readonly', False)]})
    journal_id = fields.Many2one('account.journal', string="Journal", required=True,
                                 readonly=True, states={'draft': [('readonly', False)]})
    start_date = fields.Date(string="Start date", required=True,default=lambda self: datetime.date.today(),
                                    states={'draft': [('readonly', False)]})
    end_date = fields.Date(string="End date", required=True,default=lambda self: datetime.date.today(),
                                 states={'draft': [('readonly', False)]})
    date = fields.Date(string="Date", required=True, default=lambda self: datetime.date.today(),
                       readonly=True, states={'draft': [('readonly', False)]})
    reference = fields.Char(string="Reference", readonly=True, states={'draft': [('readonly', False)]})
    state = fields.Selection(
        [('draft', 'Draft'), ('confirm', 'Confirmed'), ('post', 'Posted'), ('cancel', 'Cancelled')],
        string="Status", default='draft', readonly=True)
    closing_entry_line = fields.One2many('closing.entry.line', 'closing_entry_id', string="Journal Items",
                                         readonly=True)
    account_move_id = fields.Many2one('account.move', string="Journal Entry", readonly=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, default=lambda self: self.env.user.company_id,
                                 readonly=True, states={'draft': [('readonly', False)]})

    @api.multi
    def action_confirm(self):
        closing_entry_line = self.env['closing.entry.line']
        # fiscalperiod_obj = self.env['account.period']
        # periods = fiscalperiod_obj.build_ctx_periods(self.period_from_id.id, self.period_to_id.id)
        closing_entry_config_obj = self.env['closing.entry.configs']
        closing_entry_config = closing_entry_config_obj.search([('profit_loss', '=', False)], order="sequence asc")
        closing_entry_config_pl = closing_entry_config_obj.search([('profit_loss', '=', True)])
        group_account = 1
        for item in self:
            sum_debit = 0
            sum_credit = 0
            for config in closing_entry_config:
                balance = 0
                self._cr.execute('''
                    SELECT SUM(aml.debit - aml.credit) FROM account_move_line aml
                    INNER JOIN account_move am ON am.id = aml.move_id
                    WHERE aml.account_id = {account}
                    AND am.state ='posted'
                '''.format(account=config.origin_account_id.id))
                balance = self._cr.fetchone()[0] or 0
                closing_entry_config_level_1 = closing_entry_config_obj.search(
                    [('profit_loss', '=', False), ('forward_account_id', '=', config.origin_account_id.id),
                     ('sequence', '<', config.sequence)], order="sequence asc")
                if len(closing_entry_config_level_1):
                    for config_level_1 in closing_entry_config_level_1:
                        self._cr.execute('''
                            SELECT SUM(aml.debit - aml.credit) FROM account_move_line aml
                            INNER JOIN account_move am ON am.id = aml.move_id
                            WHERE aml.account_id = {account}
                            AND am.state ='posted'
                        '''.format(account=config_level_1.origin_account_id.id))
                        balance_level_1 = self._cr.fetchone()[0] or 0
                        balance += balance_level_1
                if config.forward_type == 'db_cr':
                    if balance != 0:
                        closing_entry_line.create({
                            'closing_entry_id': item.id,
                            'name': config.name,
                            'account_id': config.origin_account_id.id,
                            'debit': abs(balance),
                            'credit': 0,
                            'x_group': group_account,
                        })
                        closing_entry_line.create({
                            'closing_entry_id': item.id,
                            'name': config.name,
                            'account_id': config.forward_account_id.id,
                            'debit': 0,
                            'credit': abs(balance),
                            'x_group': group_account,
                        })
                        group_account += 1
                elif config.forward_type == 'cr_db':
                    if balance != 0:
                        closing_entry_line.create({
                            'closing_entry_id': item.id,
                            'name': config.name,
                            'account_id': config.origin_account_id.id,
                            'debit': 0,
                            'credit': abs(balance),
                            'x_group': group_account,
                        })
                        closing_entry_line.create({
                            'closing_entry_id': item.id,
                            'name': config.name,
                            'account_id': config.forward_account_id.id,
                            'debit': abs(balance),
                            'credit': 0,
                            'x_group': group_account,
                        })
                        group_account += 1

            for pl in closing_entry_config_pl:
                self._cr.execute('''
                    SELECT SUM(debit) FROM closing_entry_line 
                    WHERE account_id = {account}
                    AND closing_entry_id = {close}
                '''.format(account=pl.origin_account_id.id, close=item.id))
                sum_debit = self._cr.fetchone()[0] or 0

                self._cr.execute('''
                    SELECT SUM(credit) FROM closing_entry_line 
                    WHERE account_id = {account}
                    AND closing_entry_id = {close}
                '''.format(account=pl.origin_account_id.id, close=item.id))
                sum_credit = self._cr.fetchone()[0] or 0

                if sum_debit > sum_credit:
                    closing_entry_line.create({
                        'closing_entry_id': item.id,
                        'name': pl.name,
                        'account_id': pl.origin_account_id.id,
                        'debit': 0,
                        'credit': sum_debit - sum_credit,
                        'x_group': group_account,
                    })
                    closing_entry_line.create({
                        'closing_entry_id': item.id,
                        'name': pl.name,
                        'account_id': pl.forward_account_id.id,
                        'debit': sum_debit - sum_credit,
                        'credit': 0,
                        'x_group': group_account,
                    })
                    group_account += 1
                elif sum_debit < sum_credit:
                    closing_entry_line.create({
                        'closing_entry_id': item.id,
                        'name': pl.name,
                        'account_id': pl.origin_account_id.id,
                        'debit': sum_credit - sum_debit,
                        'credit': 0,
                        'x_group': group_account,
                    })
                    closing_entry_line.create({
                        'closing_entry_id': item.id,
                        'name': pl.name,
                        'account_id': pl.forward_account_id.id,
                        'debit': 0,
                        'credit': sum_credit - sum_debit,
                        'x_group': group_account,
                    })
                    group_account += 1

        if not self.closing_entry_line:
            raise UserError(('Warning!, There are not any closing entries to forward!. You should choose an other period from or period to.'))
        self.message_post(body=("Closing entry confirmed"))
        return self.write({'state': 'confirm'})

    @api.multi
    def action_post(self):
        move_obj = self.env['account.move']
        values = {}
        accounts = []
        move_line = []
        for item in self:
            for line in item.closing_entry_line:
                int = str(line.x_group) or None
                move_line.append((0, 0, {
                    'name': line.name,
                    'account_id': line.account_id.id,
                    'debit': line.debit,
                    'credit': line.credit,
                    'x_account_groups': int,
                }))
                if line.account_id.user_type_id.analytic_policy == 'always':
                    accounts.append(line.account_id.id)
                    line.account_id.user_type_id.analytic_policy = 'optional'
            values = {
                'journal_id': item.journal_id.id,
                'reference': item.reference,
                'date': item.date,
                'line_ids': move_line,
                'company_id': item.company_id.id,
            }
            move = move_obj.create(values)
            if move:
                move.post()
                accounts = list(set(accounts))
                if accounts:
                    for a in self.env['account.account'].browse(accounts):
                        a.user_type_id.analytic_policy == 'always'
                self.message_post(body=("Closing entry posted"))
                return self.write({'state': 'post', 'account_move_id': move.id})
        return False

    @api.multi
    def action_cancel(self):
        for item in self:
            for line in self.closing_entry_line:
                line.unlink()
            if item.account_move_id:
                item.account_move_id.button_cancel()
                item.account_move_id.unlink()
        self.message_post(body=("Closing entry cancelled"))
        return self.write({'state': 'cancel'})

    @api.multi
    def action_draft(self):
        return self.write({'state': 'draft'})

    @api.multi
    def unlink(self):
        for item in self:
            if item.state not in ('draft', 'cancel'):
                raise UserError(('You cannot delete an entry which is not draft or cancelled. You should cancel it instead.'))
        return super(closing_entry, self).unlink()