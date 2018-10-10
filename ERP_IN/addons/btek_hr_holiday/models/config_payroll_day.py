# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta as mondelta
from odoo.exceptions import ValidationError
import calendar


class ConfigPayrollDay(models.Model):
    _name = 'config.payroll.day'

    company_id = fields.Many2one('res.company', 'Company')
    name = fields.Char('Configure Name')
    year = fields.Integer(default=datetime.today().year)
    day_monthly_payment = fields.Integer(default=1, string='Day of monthly payment')
    state = fields.Selection([('active', 'Active'), ('deactive', 'Deactive')], default='deactive')
    day_to_payroll_ids = fields.One2many('date.to.payroll', 'config_id')

    @api.model
    def create(self, vals):
        res = super(ConfigPayrollDay, self).create(vals)
        if vals.has_key('day_monthly_payment'):
            if vals['day_monthly_payment'] not in range(1,32):
                raise ValidationError(_('Day monthly payment must in range from 1 to 31'))
        return res

    @api.multi
    def write(self, vals):
        res = super(ConfigPayrollDay, self).write(vals)
        if vals.has_key('day_monthly_payment'):
            if vals['day_monthly_payment'] not in range(1,32):
                raise ValidationError(_('Day monthly payment must in range from 1 to 31'))
        return res

    def active(self):
        check_active = self.env['config.payroll.day'].sudo().search([
            ('company_id', '=', self.company_id.id), ('year', '=', self.year),
            ('state', '=', 'active')])
        if len(check_active) >= 1:
            for i in check_active:
                i.state = 'deactive'
        self.state = 'active'
        lst_update = []
        values = {}
        for mon in range(1, 13):
            date_from = '{}-{}-{}'.format(self.year, mon, str(self.day_monthly_payment))
            date_to = str(datetime.strptime(date_from, '%Y-%m-%d')
                          + mondelta(months=+1, day=self.day_monthly_payment, days=-1))[:10]
            lst_update.append(
                (0, 0, {'name': calendar.month_name[mon], 'month': mon,
                        'date_from': date_from, 'date_to': date_to}))
        if lst_update:
            values.update(day_to_payroll_ids=lst_update)
            self.write(values)
            return True

    def deactive(self):
        self.state = 'deactive'
        if self.day_to_payroll_ids:
            for i in self.day_to_payroll_ids:
                i.unlink()
