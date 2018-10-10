# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from datetime import datetime, date
from calendar import monthrange


class PaymentInsuranceDetail(models.Model):
    _name = 'payment.insurance.detail'

    descript = fields.Char()
    account = fields.Many2one('account.account', required=True)
    amount = fields.Float()
    payment_id = fields.Many2one('payment.insurance')
    state_ = fields.Selection(related='payment_id.state', store=True)


class PaymentInsurance(models.Model):
    _name = 'payment.insurance'

    company_id = fields.Many2one('res.company', required=True,
                                 default=lambda self: self.env.user.company_id.id, string='Company')
    name = fields.Char(compute='_compute_name', store=True)
    journal_id = fields.Many2one('account.journal', 'Salary Journal',)
    date_payment = fields.Date()
    note = fields.Char()
    descript = fields.Char()
    month = fields.Selection([
        ('1', 'January'), ('2', 'February'), ('3', 'March'), ('4', 'April'), ('5', 'May'),
        ('6', 'June'), ('7', 'July'), ('8', 'August'), ('9', 'September'), ('10', 'October'),
        ('11', 'November'), ('12', 'December')], default=str(datetime.today().month))
    year = fields.Char(default=str(datetime.today().year))
    amount_total = fields.Float(compute='_compute_amount')
    detail_ids = fields.One2many('payment.insurance.detail', 'payment_id', 'Detail')
    state = fields.Selection([('draft', 'Draft'), ('done', 'Done'), ('cancel', 'Cancel')],
                             default='draft')

    def get_date_from(self, year, mon):
        date_from_ = '{}-{}-{}'.format(year, mon, '01')
        return date_from_

    def get_date_to(self, year, mon):
        date_to_ = '{}-{}-{}'.format(year, mon, monthrange(year, mon)[1])
        return date_to_

    @api.depends('detail_ids')
    def _compute_amount(self):
        for s in self:
            amount = 0
            for detail in s.detail_ids:
                amount += detail.amount
            s.amount_total = amount

    @api.depends('month', 'year')
    def _compute_name(self):
        for s in self:
            s.name = u'Thanh toán bảo hiểm {}/{}'.format(s.month, str(s.year)) or '/'

    def get_account(self):
        account_ids = self.env['account.account'].search([('company_id', '=', self.company_id.id),
                                                        ('code', 'in',
                                                        ['3383', '3384', '3386', '3335','3382'])])
        if not account_ids:
            raise UserWarning(_('Need setup account first!'))
        account_ids_ = {i.code: [i.id, i.name] for i in account_ids}
        return account_ids_

    def load_insurance(self):
        if self.detail_ids:
            res = self.detail_ids.unlink()
        date_from = self.get_date_from(int(self.year), int(self.month))
        date_to = self.get_date_to(int(self.year), int(self.month))
        check_insurance = self.env['hr.payslip'].search(
            [('company_id', '=', self.company_id.id), ('date_from', '>=', date_from),
             ('date_to', '<=', date_to)])

        if not check_insurance:
            return

        bhxh3383 = bhyt3384 = bhtn3386 = ttn3335 = cpcd = 0

        for ins in check_insurance:
            for line in ins.line_ids:
                if line.code == 'dnbhxh' or line.code == 'BHXH':
                    bhxh3383 += line.total
                elif line.code == 'dnbhyt' or line.code == 'BHYT':
                    bhyt3384 += line.total
                elif line.code == 'dnbhtn' or line.code == 'BHTN':
                    bhtn3386 += line.total
                elif line.code == 'TTNCN':
                    ttn3335 += line.total
                elif line.code == 'CPCD':
                    cpcd += line.total

        account_ids = self.env['account.account'].search([('company_id', '=', self.company_id.id),
                                                         ('code', 'in',
                                                          ['3383','3384','3386','3335','3382'])])
        if not account_ids:
            raise UserWarning(_('Need setup account first!'))
        account_ids_ = {i.code : [i.id, i.name] for i in account_ids}

        vals = [
                (0, 0, {'descript': account_ids_['3383'][1],
                        'account': account_ids_['3383'][0], 'amount': bhxh3383}),
                (0, 0, {'descript': account_ids_['3384'][1],
                        'account': account_ids_['3384'][0], 'amount': bhyt3384}),
                (0, 0, {'descript': account_ids_['3386'][1],
                        'account': account_ids_['3386'][0], 'amount': bhtn3386}),
                (0, 0, {'descript': account_ids_['3335'][1],
                        'account': account_ids_['3335'][0], 'amount': ttn3335}),
                (0, 0, {'descript': account_ids_['3382'][1],
                        'account': account_ids_['3382'][0], 'amount': cpcd}),
                 ]
        res = self.write({'detail_ids': vals})
        return res

    def open_payment_ins(self):
        context = dict(self._context or {})
        action_obj = self.env.ref('btek_hr_holiday.open_payment_insurance_action')
        action = action_obj.read([])[0]
        action['res_id'] = self._ids[0]
        return action

    def cancel_ins(self):
        return self.write({'state': 'cancel'})

    def pay_insurance(self):
        if not self.detail_ids:
            return
        val = []
        vals = {}
        for detail in self.detail_ids:
            val.append((0, 0, {'account_id': detail.account.id, 'name': detail.descript or '', 'debit': float(detail.amount)}))
            val.append((0, 0, {'account_id': self.journal_id.default_credit_account_id.id, 'name': detail.descript or '', 'credit': float(detail.amount)}))
        vals.update({
            'name': self.name,
            'ref': self.descript or '',
            'journal_id': self.journal_id.id,
            'date': self.date_payment,
            'line_ids': val,
        })
        res = self.env['account.move'].sudo().create(vals)
        return self.write({'state': 'done'})