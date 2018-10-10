# -*- coding: utf-8 -*-
from odoo import fields, models, api
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError, ValidationError
from dateutil import parser
import pytz
import calendar
from dateutil.rrule import rrule, DAILY


class EmployeeWorkedDay(models.Model):
    _name = 'hr.worked.day'

    name = fields.Char(default='Worked day')
    employee_id = fields.Many2one('hr.employee', 'Employee')
    date_from = fields.Date()
    date_to = fields.Date()
    worked_days = fields.One2many('hr.worked.day.line', 'worked_day_id', )
    total_day = fields.Float(compute='_compute_total_day')

    state = fields.Selection([
        ('new', 'New'),
        ('draft', 'Open'),
        ('confirm', 'Waiting Approval'),
        ('done', 'Approved')], default='new', track_visibility='onchange',
        string='Status', required=True, readonly=True, index=True,
        help=' * The \'Open\' status is used when a user is encoding a new and unconfirmed timesheet. '
             '\n* The \'Waiting Approval\' status is used to confirm the timesheet by user. '
             '\n* The \'Approved\' status is used when the users timesheet is accepted by his/her senior.')

    def compute_date(self, day, month, year):
        end_day = ''
        if month in [1, 3, 5, 7, 8, 10, 12]:
            end_day = '31'
        elif month in [4, 6, 9, 11]:
            end_day = '30'
        elif month == 2:
            if calendar.isleap(year):
                end_day = '29'
            else:
                end_day = '28'
        if 1 < day < 15:
            start_date = datetime.strptime('{}-{}-{}'.format(year, month, day), '%Y-%m-%d')
            end_date = datetime.strptime('{}-{}-{}'.format(year, int(month) + 1, day), '%Y-%m-%d')
        elif day >= 15 and day < 30:
            start_date = datetime.strptime('{}-{}-{}'.format(year, int(month) - 1, day), '%Y-%m-%d')
            end_date = datetime.strptime('{}-{}-{}'.format(year, month, day), '%Y-%m-%d')
        elif day == 1 or day >= 30:
            start_date = datetime.strptime('{}-{}-01'.format(year, month), '%Y-%m-%d')
            end_date = datetime.strptime('{}-{}-{}'.format(year, month, end_day), '%Y-%m-%d')
        date_dct = {}
        date_dct.update({
            'start_date': start_date,
            'end_date': end_date,
        })
        return date_dct

    @api.onchange('date_from', 'date_to', 'employee_id')
    def _update_day(self):
        if self.date_from and self.date_to and self.employee_id:
            if self.employee_id.company_id:
                company_id = self.employee_id.company_id.id
                current_year = datetime.today().year
                current_month = datetime.today().day
                check_payroll_cf = self.env['config.payroll.day'].sudo().search([
                    ('company_id', '=', company_id),
                    ('state', '=', 'active'), ('year', '=', current_year)
                ])
                if not check_payroll_cf:
                    return
                day_payment = check_payroll_cf.day_monthly_payment
                date = self.compute_date(month=current_month, year=current_year, day=day_payment)
            if date:
                date_to = date['end_date']
                date_from = date['start_date']
                if self.date_from >= date_from:
                    pass
            year = datetime.strptime(self.date_from, '%Y-%m-%d').year
            date_from = datetime.strptime(self.date_from, '%Y-%m-%d')
            date_to = datetime.strptime(self.date_to, '%Y-%m-%d')
            lst_update = []
            values = {}
            for dt in rrule(DAILY, dtstart=date_from, until=date_to):
                day_name = calendar.day_name[dt.weekday()]
                day = dt.day
                month = dt.month
                last_str = '{} {}/T{}'.format(day_name, str(day), str(month))
                lst_update.append((0, 0, {'date': last_str, 'day': str(dt.date())}))
            if lst_update:
                values.update(worked_days=lst_update)
                return {'value': values}
                # for update in lst_update:
                #     self.create({'worked_days': [(1, self, update)],})

    @api.depends('worked_days')
    def _compute_total_day(self):
        for i in self:
            if i.worked_days:
                d = 0
                for w in i.worked_days:
                    d += w.worked
                i.total_day = d

    def worked_from_attendance(self):
        if self.employee_id and self.date_from and self.date_to:
            employee = self.employee_id.id
            works = self.env['hr.attendance'].sudo().search([
                ('employee_id', '=', employee),
                ('check_in', '>=', self.date_from),
                ('check_out', '<=', self.date_to)])
            if not works:
                return
            days_check_in = {}
            days_check_out = {}

            user_tz = self.env.user.tz or str(pytz.utc)
            tz_now = datetime.now(pytz.timezone(user_tz))
            difference = int(tz_now.utcoffset().total_seconds() / 60 / 60)

            def convert_datetime(source_dt):
                return str(parser.parse(source_dt).date())

        for work in works:
            day_check_in = convert_datetime(work.check_in)
            day_check_out = convert_datetime(work.check_out)
            chk_in = str(datetime.strptime(work.check_in, '%Y-%m-%d %H:%M:%S') + timedelta(hours=+difference))
            chk_out = str(datetime.strptime(work.check_out, '%Y-%m-%d %H:%M:%S') + timedelta(hours=+difference))
            if not days_check_in.get(day_check_in, False):
                days_check_in[day_check_in] = []
                days_check_in[day_check_in].append(chk_in)
            else:
                days_check_in[day_check_in].append(chk_in)

            if not days_check_out.get(day_check_out, False):
                days_check_out[day_check_out] = []
                days_check_out[day_check_out].append(chk_out)
            else:
                days_check_out[day_check_out].append(chk_out)

        work_dct = {}
        for key in days_check_in:
            delta = parser.parse(max(days_check_out[key])) - parser.parse(min(days_check_in[key]))
            if timedelta(hours=1) <= delta < timedelta(hours=6.5):
                d = 0.5
            elif timedelta(hours=6.5) <= delta:
                d = 1
            else:
                d = 0
            work_dct[key] = d

        for i in self.worked_days:
            for j in work_dct:
                if i.day == j:
                    res = self.env['hr.worked.day.line'].sudo().browse(
                        i.id).write({'worked':work_dct[j]})


