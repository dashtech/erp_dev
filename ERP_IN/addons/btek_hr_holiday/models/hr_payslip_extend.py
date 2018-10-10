# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from datetime import datetime, timedelta
import time
import calendar
from odoo.exceptions import UserError, ValidationError, Warning
from dateutil.relativedelta import relativedelta as mondelta
from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def compute_date(self, day, month, year):
        date_from = datetime.strptime('{}-{}-{}'.format(year, month, day), '%Y-%m-%d')
        date_to = str(date_from + mondelta(months=+1, day=day, days=-1))[:10]
        date_dct = {}
        date_dct.update({
            'start_date': date_from,
            'end_date': date_to,
        })
        return date_dct

    def get_date_from(self):
        date_from_ = time.strftime('%Y-%m-01')
        if self.employee_id.company_id:
            company_id = self.employee_id.company_id.id
            current_year = datetime.today().year
            current_month = datetime.today().month
            check_payroll_cf = self.env['config.payroll.day'].sudo().search([
                ('company_id', '=', company_id),
                ('state', '=', 'active'), ('year', '=', current_year)
            ])
            if not check_payroll_cf:
                return date_from_

            day_payment = check_payroll_cf.day_monthly_payment
            date_from = self.compute_date(month=current_month, year=current_year, day=day_payment)
            if date_from:
                date_from_ = date_from['start_date']
        return date_from_

    def get_date_to(self):
        date_to_ = str(datetime.now() + mondelta(months=+1, day=1, days=-1))[:10]
        if self.employee_id.company_id:
            company_id = self.employee_id.company_id.id
            current_year = datetime.today().year
            current_month = datetime.today().month
            check_payroll_cf = self.env['config.payroll.day'].sudo().search([
                ('company_id', '=', company_id),
                ('state', '=', 'active'), ('year', '=', current_year)
            ])
            if not check_payroll_cf:
                return date_to_

            day_payment = check_payroll_cf.day_monthly_payment
            date_to = self.compute_date(month=current_month, year=current_year, day=day_payment)
            if date_to:
                date_to_ = date_to['end_date']
        return date_to_

    net_wage = fields.Char(compute='_get_net_wage')
    payment = fields.Boolean('Payment')
    print_ = fields.Boolean('Print')
    email_ = fields.Boolean('Send Email')
    public_holiday_id = fields.Many2one('btek.hr.public.holiday')
    bsc_value = fields.Integer()
    bsc_readonly = fields.Integer(compute='_compute_bsc_value', string='BSC rate')
    kpi = fields.Integer()
    kpi_readonly = fields.Integer(compute='_compute_kpi', string='Kpi rate')
    # worked_days_line_ids = fields.One2many('hr.payslip.worked_days', 'payslip_id',
    #                                        compute='_compute_holiday',
    #                                        string='Payslip Worked Days', copy=True, readonly=True,
    #                                        states={'draft': [('readonly', False)]})


    @api.onchange('employee_id')
    def change_date(self):
        self.date_from = self.get_date_from()
        self.date_to = self.get_date_to()


    @api.onchange('employee_id', 'date_from', 'date_to')
    def onchange_employee(self):
        res = super(HrPayslip, self).onchange_employee()
        if self.employee_id and self.employee_id.company_id and self.employee_id.department_id:
            current_year = datetime.strptime(self.date_from, '%Y-%m-%d').year
            month = datetime.strptime(self.date_from, '%Y-%m-%d').month
            config_payroll = self.env['config.payroll.day'].search([
                ('company_id', '=', self.employee_id.company_id.id),
                ('year', '=', current_year), ('state', '=', 'active')])
            if config_payroll:
                for mon in config_payroll.day_to_payroll_ids:
                    if mon.month == month:
                        if self.date_from != mon.date_from or self.date_to != mon.date_to:
                            value = {}
                            warning = {
                                'title': _('Date invaild!'),
                                'message':
                                    _('Date from/date to in Period not match with your company '
                                      'configure.')}
                            if self.worked_days_line_ids:
                                value = {'worked_days_line_ids': [(5, )]}
                            return {'value': value, 'warning': warning}
            # search kpi for employee by month
            if self.employee_id.company_id:
                kpi = self.env['hr.kpi.employee'].search([
                    ('company_id', '=', self.employee_id.company_id.id),
                    ('month', '=', month)])
                if kpi:
                    for item in kpi:
                        if item.start_date_readonly == self.date_from \
                                and item.end_date_readonly == self.date_to:
                            for emp in item.employee_ids:
                                if emp.employee_id.id == self.employee_id.id:
                                    self.kpi = emp.rate

            # search bsc for employee by month and department
            if self.employee_id.department_id:
                bsc = self.env['hr.bsc.department'].sudo().search([
                    ('department_id', '=', self.employee_id.department_id.id),
                    ('month', '=', month)])
                if bsc:
                    for item in bsc:
                        if item.start_date == self.date_from and item.end_date == self.date_to:
                            self.bsc_value = item.value
                    # else:
                    #     raise UserError(_('Date from, date to need like day in configure'))

            related_person = 0
            if self.employee_id.related_person_ids:
                for related in self.employee_id.related_person_ids:
                    if related.date_begin <= self.date_to:
                        related_person += 1
            self.employee_id.related_person_payslip = related_person

            #compute public holiday
            annual_id = self.env['btek.hr.public.holiday'].sudo().search([('year', '=', current_year)])
            employee_tag_id = annual_id.employee_tag.id
            employee_tag_ids = []
            for i in self.employee_id.category_ids:
                employee_tag_ids.append(i.id)
            # if employee_tag_id not in employee_tag_ids:
            #     continue
            holiday_code = annual_id.hr_holiday_status.name
            annual_day = 0
            for line in annual_id.public_holiday_line:
                if line.date <= self.date_to and line.date >= self.date_from:
                    annual_day += 1
            contract_ids = self.get_contract(self.employee_id, self.date_from, self.date_to)
            annual = self.get_worked_day(contract_ids, self.date_from, self.date_to)
            work100 = sum([i['number_of_days'] for i in annual])
            if annual:
                annual[0]['number_of_days'] = work100
                annual[0]['number_of_hours'] = work100 * 8.0
            if annual_day > 0:
                annual.append({
                    'code': holiday_code or 'ANNUAL',
                    'name': _('Annual'),
                    'number_of_days': annual_day,
                    'number_of_hours': annual_day * 8.0,
                    'sequence': 2,
                    'contract_id': self.employee_id.contract_id.id or False,
                })
            work_day_by_attens = self.env['hr.working.day.employee'].sudo().search([
                ('employee_id', '=', self.employee_id.id), ('date', '>=', self.date_from),
                ('date', '<=', self.date_to)])
            if work_day_by_attens:
                total = {}
                for timesheet  in work_day_by_attens:
                    total[timesheet.date] = timesheet.unit_amount
                total_day = sum(total.values())
                annual.append({
                    'code': 'worked_attendance',
                    'name': _('Worked Day by Attendance'),
                    'number_of_days': total_day,
                    'number_of_hours': total_day * 8.0,
                    'sequence': 5,
                    'contract_id': self.employee_id.contract_id.id or False,
                })
            worked_days_line_ids = annual
            worked_days_lines = self.worked_days_line_ids.browse([])
            for r in worked_days_line_ids:
                worked_days_lines += worked_days_lines.new(r)
            self.worked_days_line_ids = worked_days_lines
        return res

    @api.model
    def get_worked_day(self, contract_ids, date_from, date_to):
        """
        @param contract_ids: list of contract id
        @return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
        """

        def was_on_leave_interval(employee_id, date_from, date_to):
            date_from = fields.Datetime.to_string(date_from)
            date_to = fields.Datetime.to_string(date_to)
            return self.env['hr.holidays'].search([
                ('state', '=', 'validate'),
                ('employee_id', '=', employee_id),
                ('type', '=', 'remove'),
                ('date_from', '<=', date_from),
                ('date_to', '>=', date_to)
            ], limit=1)

        res = []
        # fill only if the contract as a working schedule linked
        uom_day = self.env.ref('product.product_uom_day', raise_if_not_found=False)
        for contract in self.env['hr.contract'].browse(contract_ids).filtered(
                lambda contract: contract.working_hours):
            uom_hour = contract.employee_id.resource_id.calendar_id.uom_id or self.env.ref(
                'product.product_uom_hour', raise_if_not_found=False)
            interval_data = []
            holidays = self.env['hr.holidays']
            attendances = {
                'name': _("Normal Working Days paid at 100%"),
                'sequence': 1,
                'code': 'WORK100',
                'number_of_days': 0.0,
                'number_of_hours': 0.0,
                'contract_id': contract.id,
            }
            leaves = {}
            day_from = fields.Datetime.from_string(date_from)
            day_to = fields.Datetime.from_string(date_to)
            nb_of_days = (day_to - day_from).days + 1

            # Gather all intervals and holidays
            for day in range(0, nb_of_days):
                working_intervals_on_day = contract.working_hours.get_working_intervals_of_day(
                    start_dt=day_from + timedelta(days=day))
                for interval in working_intervals_on_day:
                    interval_data.append((interval, was_on_leave_interval(contract.employee_id.id,
                                                                          interval[0],
                                                                          interval[1])))

            # Extract information from previous data. A working interval is considered:
            # - as a leave if a hr.holiday completely covers the period
            # - as a working period instead
            for interval, holiday in interval_data:
                holidays |= holiday
                hours = (interval[1] - interval[0]).total_seconds() / 3600.0
                if holiday:
                    # if he was on leave, fill the leaves dict
                    if holiday.holiday_status_id.name in leaves:
                        leaves[holiday.holiday_status_id.name]['number_of_hours'] += hours
                    else:
                        leaves[holiday.holiday_status_id.name] = {
                            'name': holiday.holiday_status_id.desc or holiday.holiday_status_id.name,
                            'sequence': 5,
                            'code': holiday.holiday_status_id.name,
                            'number_of_days': 0.0,
                            'number_of_hours': hours,
                            'contract_id': contract.id,
                        }
                else:
                    # add the input vals to tmp (increment if existing)
                    attendances['number_of_hours'] += hours

            # Clean-up the results
            leaves = [value for key, value in leaves.items()]
            for data in [attendances] + leaves:
                data['number_of_days'] = uom_hour._compute_quantity(data['number_of_hours'],
                                                                    uom_day) \
                    if uom_day and uom_hour \
                    else data['number_of_hours'] / 8.0
                res.append(data)
        return res

    @api.depends('bsc_value')
    def _compute_bsc_value(self):
        for s in self:
            s.bsc_readonly = s.bsc_value

    @api.depends('kpi')
    def _compute_kpi(self):
        for s in self:
            s.kpi_readonly = s.kpi

    @api.multi
    def compute_sheet(self):
        for i in self:
            res_worked_day = i.onchange_employee()
        res = super(HrPayslip, self).compute_sheet()
        return res

    @api.depends('line_ids')
    def _get_net_wage(self):
        for s in self:
            for r in s.line_ids:
                if r.code == 'TL' or r.code == 'CTV_GIO':
                    s.net_wage = r.total


    def get_detail(self):
        res = self.env['report.hr_payroll.report_payslipdetails'].get_details_by_rule_category(
            self.details_by_salary_rule_category).get(self.id, [])
        for i in res:
            if i['code'] == 'WAGE' and i['level'] == 0:
                i['index'] = 0
            if i['code'] == 'WAGE' and i['level'] == 1:
                i['index'] = 1
            if i['code'] == 'BH':
                i['index'] = 2
            if i['code'] == 'BHXH':
                i['index'] = 3
            if i['code'] == 'BHYT':
                i['index'] = 4
            if i['code'] == 'BHTN':
                i['index'] = 5
            if i['code'] == 'TTN' and i['level'] == 0:
                i['index'] = 6
            if i['code'] == 'TTN' and i['level'] == 1:
                i['index'] = 7
            if i['code'] == 'GTTCN' and i['level'] == 0:
                i['index'] = 8
            if i['code'] == 'GTTCN' and i['level'] == 1:
                i['index'] = 9
            if i['code'] == 'TNTT' and i['level'] == 0:
                i['index'] = 10
            if i['code'] == 'TNTT' and i['level'] == 1:
                i['index'] = 11
            if i['code'] == 'TTNCN' and i['level'] == 0:
                i['index'] = 12
            if i['code'] == 'TTNCN' and i['level'] == 1:
                i['index'] = 13
            if i['code'] == 'DNDBH':
                i['index'] = 14
            if i['code'] == 'dnbhxh':
                i['index'] = 15
            if i['code'] == 'dnbhyt':
                i['index'] = 16
            if i['code'] == 'dnbhtn':
                i['index'] = 17
            if i['code'] == 'PCN' and i['level'] == 0:
                i['index'] = 18
            if i['code'] == 'PCN' and i['level'] == 1:
                i['index'] = 19
            if i['code'] == 'TL' and i['level'] == 0:
                i['index'] = 20
            if i['code'] == 'TL' and i['level'] == 1:
                i['index'] = 21

        res_ = sorted(res, key=lambda k: k['index'])
        return res_

    def get_register(self):
        res = self.env['report.hr_payroll.report_payslipdetails'].get_lines_by_contribution_register(
            self.details_by_salary_rule_category).get(self.id, [])
        return res

class HrPayslipRunInherit(models.Model):
    _inherit = 'hr.payslip.run'

    def compute_date(self, day, month, year):
        date_from = datetime.strptime('{}-{}-{}'.format(year, month, day), '%Y-%m-%d')
        date_to = str(date_from + mondelta(months=+1, day=day, days=-1))[:10]
        date_dct = {}
        date_dct.update({
            'start_date': date_from,
            'end_date': date_to,
        })
        return date_dct

    def _get_current_company(self):
        user = self.env.user
        company_id = user.company_id.id
        return company_id

    @api.model
    def get_date_from(self):
        date_from_ = time.strftime('%Y-%m-01')
        company_id = self.env.user.company_id
        if company_id:
            company_id = company_id.id
            current_year = datetime.today().year
            current_month = datetime.today().month
            check_payroll_cf = self.env['config.payroll.day'].sudo().search([
                    ('company_id', '=', company_id),
                    ('state', '=', 'active'), ('year', '=', current_year)
                ])
            if not check_payroll_cf:
                return date_from_

            day_payment = check_payroll_cf.day_monthly_payment
            date_from = self.compute_date(month=current_month, year=current_year, day=day_payment)
            if date_from:
                date_from_ = date_from['start_date']
        return date_from_

    # payment_box = fields.Boolean('Payment')
    # print_box = fields.Boolean('Print')
    # email_box = fields.Boolean('Send Email')

    @api.model
    def get_date_to(self):
        date_to_ = str(datetime.now() + mondelta(months=+1, day=1, days=-1))[:10]
        company_id = self.env.user.company_id
        if company_id:
            company_id = company_id.id
            current_year = datetime.today().year
            current_month = datetime.today().month
            check_payroll_cf = self.env['config.payroll.day'].sudo().search([
                ('company_id', '=', company_id),
                ('state', '=', 'active'), ('year', '=', current_year)
            ])
            if not check_payroll_cf:
                return date_to_

            day_payment = check_payroll_cf.day_monthly_payment
            date_to = self.compute_date(month=current_month, year=current_year, day=day_payment)
            if date_to:
                date_to_ = date_to['end_date']
        return date_to_

    date_start = fields.Date(string='Date From', required=True, readonly=True,
                             states={'draft': [('readonly', False)]}, default=get_date_from)
    date_end = fields.Date(string='Date To', required=True, readonly=True,
                           states={'draft': [('readonly', False)]},
                           default=get_date_to)
    journal_id = fields.Many2one('account.journal', 'Salary Journal',
                                 default=False,
                                 states={'draft': [('readonly', False)]})
    company_id = fields.Many2one('res.company', default=_get_current_company, store=True,
                                     compute='_compute_current_company')

    @api.multi
    def _compute_current_company(self):
        for s in self:
            user = s.env.user
            s.current_company = user.company_id.id

    def check_to_route(self):
        date_from = self.date_start
        date_to = self.date_end
        year = datetime.strptime(date_from, '%Y-%m-%d').year
        company_id = self.env.user.company_id
        config_date = self.env['config.payroll.day'].search([
            ('company_id', '=', company_id.id),
            ('year', '=', year), ('state', '=', 'active')
        ])
        if not config_date:
            raise ValidationError(_('Can not find your company configure payroll day'))
        for day in config_date.day_to_payroll_ids:
            if date_from == day.date_from and date_to == day.date_to:
                res = self.env.ref('hr_payroll.action_hr_payslip_by_employees').read([])[0]
                return res
        raise ValidationError(
            _('Date from/date to in Period not match with your company configure'))

    @api.multi
    def payment_act(self):
        context = dict(self._context or {})
        action_obj = self.env.ref('btek_hr_holiday.payment_payslip_action')
        action = action_obj.read([])[0]
        action['res_id'] = self._ids[0]
        return action

    def done_act(self):
        date = datetime.today()
        debit_account = self.journal_id.default_debit_account_id.id
        account_id = self.env['account.account'].search([('code', '=', '3341'),
                                                          ('company_id', '=', self.journal_id.company_id.id)])
        if not account_id:
            raise UserError(_('You need setup account 3341 first!'))
        credit_account = account_id.id
        line_ids = []
        slips = []
        vals = {}
        vals_slip = {}
        for slip in self.slip_ids:
            if slip.payment is True:
                slip.action_payslip_done()
                line_ids.append((0, 0, {'account_id': debit_account, 'name': slip.number, 'debit': float(slip.net_wage)}))
                line_ids.append((0, 0, {'account_id': credit_account, 'name': slip.number, 'credit': float(slip.net_wage)}))
                slip.payment = False
        vals.update({
            'name': self.name,
            'journal_id' : self.journal_id.id,
            'date': date,
            'x_voucher_day': date,
            'line_ids': line_ids,
        })
        vals_slip.update({'slip_ids': slips})
        if not line_ids:
            return
        res = self.env['account.move'].sudo().create(vals)
        res_slip = super(HrPayslipRunInherit, self).write(vals_slip)
        return res

    def send_act(self):
        mailling = [i for i in self.slip_ids if i.email_ is True]
        res = self.send_mail_salary(mailling=mailling)
        return res

    def send_mail_salary(self, mailling):
        html_body = u'''
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        <p><span style="font-size:18px;">Dear {}<br></em></span></p>
        <p><span style="font-size:15px;">Công ty gửi anh/chị bảng lương từ ngày {} đến ngày {}<br></em></span></p>
        <table style="border-collapse: collapse; width: 80%;">
            <tbody>
                <tr><td colspan="4" style="text-align: right;">ĐVT: VNĐ</td></tr>
                <tr>
                    <td style="border: 1px solid blue; font-size:15px; width: 3%;"><b>I</b></td>
                    <td style="border: 1px solid blue; font-size:15px; width: 35%"><b>Tổng lương</b></td>
                    <td style="border: 1px solid blue; font-size:15px; width: 35%">{:,.0f}</td>
                    <td style="border: 1px solid blue; font-size:15px; width: 25%;"></td>
                </tr>
                <tr>
                    <td style="border: 1px solid blue; font-size:15px;">1</th>
                    <td style="border: 1px solid blue; font-size:15px;">Số ngày công thực tế</td>
                    <td style="border: 1px solid blue; font-size:15px;">{}</td>
                    <td style="border: 1px solid blue; font-size:15px;"></td>
                </tr>
                <tr>
                    <td style="border: 1px solid blue; font-size:15px;">2</th>
                    <td style="border: 1px solid blue; font-size:15px;">Các khoản phụ cấp theo lương</td>
                    <td style="border: 1px solid blue; font-size:15px;"></td>
                    <td style="border: 1px solid blue; font-size:15px;"></td>
                </tr>
                <tr>
                    <td style="border: 1px solid blue; font-size:15px;">3</th>
                    <td style="border: 1px solid blue; font-size:15px;">Các khoản phụ cấp khác</td>
                    <td style="border: 1px solid blue; font-size:15px;"></td>
                    <td style="border: 1px solid blue; font-size:15px;"></td>
                </tr>
            <!--<tr>
                    <td style="border: 1px solid blue; font-size:15px;"><b>II</b></th>
                    <td style="border: 1px solid blue; font-size:15px;"><b>Các khoản giảm trừ theo lương</b></td>
                    <td style="border: 1px solid blue; font-size:15px;"></td>
                    <td style="border: 1px solid blue; font-size:15px;"></td>
                </tr>
                <tr>
                    <td style="border: 1px solid blue; font-size:15px;">1</th>
                    <td style="border: 1px solid blue; font-size:15px;">Bảo hiểm (BHXH, BHYT, BHTN)</td>
                    <td style="border: 1px solid blue; font-size:15px;">{:,.0f}</td>
                    <td style="border: 1px solid blue; font-size:15px;"></td>
                </tr>
                <tr>
                    <td style="border: 1px solid blue; font-size:15px;">2</th>
                    <td style="border: 1px solid blue; font-size:15px;">Thuế TNCN</td>
                    <td style="border: 1px solid blue; font-size:15px;">{:,.0f}</td>
                    <td style="border: 1px solid blue; font-size:15px;"></td>
                </tr>
                <tr>
                    <td style="border: 1px solid blue; font-size:15px;">3</th>
                    <td style="border: 1px solid blue; font-size:15px;">KPCĐ</td>
                    <td style="border: 1px solid blue; font-size:15px;">{}</td>
                    <td style="border: 1px solid blue; font-size:15px;"></td>
                </tr>
                <tr>
                    <td style="border: 1px solid blue; font-size:15px;">4</th>
                    <td style="border: 1px solid blue; font-size:15px;">Khác ….</td>
                    <td style="border: 1px solid blue; font-size:15px;"></td>
                    <td style="border: 1px solid blue; font-size:15px;"></td>
                </tr>-->
                <tr>
                    <td style="border: 1px solid blue; font-size:15px;"><b>II</b></th>
                    <td style="border: 1px solid blue; font-size:15px;"><b>Số tiền lương thực lĩnh: <b></td>
                    <td style="border: 1px solid blue; font-size:15px;">{:,.0f}</td>
                    <td style="border: 1px solid blue; font-size:15px;"></td>
                </tr>
                <tr>
                    <td colspan="4" style="border: 1px solid blue; font-size:15px;"><i>Bằng chữ: {}</i></th>
                </tr>
            </tbody>
        </table>'''

        mailling = mailling
        if not mailling:
            return
        for mail in mailling:
            worked_day = 0
            work100 = 0
            net_wage = float(mail.net_wage) or 0
            total = 0
            bh = 0
            ttncn = 0
            if mail.worked_days_line_ids:
                for day in mail.worked_days_line_ids:
                    if day.code == 'worked_attendance':
                        worked_day = day.number_of_days
                    if day.code == 'WORK100':
                        work100 = day.number_of_days

            if worked_day == 0:
                worked_day = work100
            if mail.line_ids:
                for line in mail.line_ids:
                    if line.code == 'TTN':
                        total = line.total
                    if line.code == 'BHXH':
                        bh += line.total
                    if line.code == 'BHYT':
                        bh += line.total
                    if line.code == 'BHTN':
                        bh += line.total
                    if line.code == 'TTNCN':
                        ttncn = line.total

            wage_to_str = self.env['read.number'].docso(int(net_wage)) + u' đồng'
            res = self.env['mail.mail'].sudo().create({
                'email_to': mail.employee_id.work_email or '',
                'body_html': html_body.format(mail.employee_id.name, mail.date_from, mail.date_to,
                                              total, worked_day, bh, ttncn, 0, net_wage, wage_to_str),
                'subject': u'{} thanh toán lương'.format(
                    self.env.user.company_id.name),
                'email_from': self.env.user.email or 'hr@bave.io',
                'auto_delete': True,})

            # }).send()
        return True

    @api.multi
    def print_act(self):
        datas = {'ids': self.ids}
        datas['model'] = 'hr.payslip.run'
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'btek_hr_holiday.report.payslip.xlsx',
            'datas': datas,
            'name': _('Payslip')
        }

    check_payment = fields.Boolean()
    check_print = fields.Boolean()
    check_email = fields.Boolean()

    @api.onchange('check_payment', 'check_print', 'check_email')
    def _check_all(self):
        for rec in self.slip_ids:
            if self.check_payment == True:
                if rec.state in ['done', 'cancel']:
                    rec.payment = False
                else:
                    rec.payment = True
            else:
                rec.payment = False
            if self.check_print == True:
                rec.print_ = True
            else:
                rec.print_ = False
            if self.check_email == True:
                rec.email_ = True
            else:
                rec.email_ = False

    @api.onchange('slip_ids')
    def _uncheck(self):
        for rec in self.slip_ids:
            if rec.print_ == False:
                self.check_print = False
            if rec.email_ == False:
                self.check_email = False
            if rec.payment == False:
                if rec.state not in ['done', 'cancel']:
                    self.check_payment = False

class HrPayslipEmployeesInherit(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    def get_company(self):
        user = self.env.user
        company_id = user.company_id
        return company_id

    company_id = fields.Many2one('res.company',default=get_company)


class ReportPayslip(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, wizard):
        sheet = workbook.add_worksheet(_('Payslip'))

        sheet.set_column(0, 0, 6)
        sheet.set_column(1, 1, 15)
        sheet.set_column(2, 2, 30)
        sheet.set_column(3, 3, 20)
        sheet.set_column(4, 4, 20)
        sheet.set_column(5, 5, 20)
        sheet.set_column(6, 6, 15)
        sheet.set_column(7, 7, 20)
        sheet.set_column(8, 8, 15)
        sheet.set_column(9, 9, 15)
        sheet.set_column(10, 10, 17)
        sheet.set_column(11, 11, 17)
        sheet.set_column(12, 12, 17)
        sheet.set_column(13, 13, 18)
        sheet.set_column(14, 14, 18)
        sheet.set_column(15, 15, 10)
        sheet.set_column(16, 16, 15)
        sheet.set_column(17, 17, 25)

        header = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 1,
            'font_name': 'Times New Roman',
            'font_size': 18,
            'text_wrap': False,
            'bold': True,
        })
        title = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 1,
            'font_name': 'Times New Roman',
            'font_size': 14,
            'text_wrap': True,
            'bold': True,
        })
        content = workbook.add_format({
            'valign': 'vcenter',
            'align': 'left',
            'border': 1,
            'font_name': 'Times New Roman',
            'font_size': 13,
            'text_wrap': True,
            'bold': False,
        })
        content_stt = workbook.add_format({
            'valign': 'vcenter',
            'align': 'center',
            'border': 1,
            'font_name': 'Times New Roman',
            'font_size': 13,
            'text_wrap': True,
            'bold': False,
        })
        content_number = workbook.add_format({
            'valign': 'vcenter',
            'align': 'right',
            'border': 1,
            'font_name': 'Times New Roman',
            'font_size': 13,
            'text_wrap': True,
            'bold': False,
            'num_format': '#,##0',
        })



        sheet.merge_range('A1:R2', u'BẢNG LƯƠNG NHÂN VIÊN', header)
        sheet.merge_range('A3:A4', u'STT', title)
        sheet.merge_range('B3:B4', u'Mã NV', title)
        sheet.merge_range('C3:C4', u'Tên Nhân viên', title)
        sheet.merge_range('D3:D4', u'Chức vụ', title)
        sheet.merge_range('E3:E4', u'Ngân hàng', title)
        sheet.merge_range('F3:F4', u'Số TK', title)
        sheet.merge_range('G3:G4', u'Lương cơ bản', title)
        sheet.merge_range('H3:H4', u'Ngày công quy định', title)
        sheet.merge_range('I3:I4', u'Ngày công thực tế', title)
        sheet.merge_range('J3:J4', u'Ngày nghỉ phép', title)
        sheet.merge_range('K3:K4', u'Lương được hưởng', title)
        sheet.merge_range('L3:L4', u'Giảm trừ gia cảnh', title)
        sheet.merge_range('M3:Q3', u'Các khoản khấu trừ vào lương', title)
        sheet.write('M4', u'BHXH(8%)', title)
        sheet.write('N4', u'BHYT(1.5%)', title)
        sheet.write('O4', u'BHTN(1%)', title)
        sheet.write('P4', u'KPCĐ', title)
        sheet.write('Q4', u'Thuế TNCN', title)
        sheet.merge_range('R3:R4', u'Thực lĩnh', title)
        sheet.write('A5', u'A', title)
        sheet.write('B5', u'B', title)
        sheet.write('C5', u'C', title)
        sheet.write('D5', u'D', title)
        sheet.write('E5', u'E', title)
        sheet.write('F5', u'F', title)
        sheet.write('G5', u'G', title)
        sheet.write('H5', u'H', title)
        sheet.write('I5', u'I', title)
        sheet.write('J5', u'J', title)
        sheet.write('K5', u'K=(G/H)*(I+J)', title)
        sheet.write('L5', u'L', title)
        sheet.write('M5', u'M', title)
        sheet.write('N5', u'N', title)
        sheet.write('O5', u'O', title)
        sheet.write('P5', u'P', title)
        sheet.write('Q5', u'Q', title)
        sheet.write('R5', u'R=K-M-N-O-P-Q', title)

        print_check = [slip for slip in wizard.slip_ids if slip.print_ is True]
        if not print_check:
            return
        row = 6
        stt = 1
        for line in print_check:
            normal_day = 1
            worked_day = 0
            wage = line.contract_id.wage or 0
            family_sub = 9000000
            bhxh = 0
            bhyt = 0
            bhtn = 0
            ttncn = 0
            if not line.net_wage:
                net_wage = 0
            else:
                net_wage = float(line.net_wage)

            bank = line.employee_id.bank_account_id.bank_id.name or u''
            bank_account = line.employee_id.bank_account_id.acc_number or u''

            annual_day = 0
            for day in line.worked_days_line_ids:
                if day.code == 'WORK100':
                    normal_day = day.number_of_days
                if day.code == 'worked_attendance':
                    worked_day = day.number_of_days
                if day.code == 'ANNUAL' or day.code == 'LEGAL':
                    annual_day += day.number_of_days

            salary = round((wage/normal_day) * worked_day, 0)
            if worked_day > 0:
                for id in line.line_ids:
                    if id.code == 'GTTCN':
                        family_sub = id.total
                    if id.code == 'BHXH':
                        bhxh = id.total
                    if id.code == 'BHYT':
                        bhyt = id.total
                    if id.code == 'BHTN':
                        bhtn = id.total
                    if id.code == 'TTNCN':
                        ttncn = id.total

            sheet.write('A{}'.format(row), stt, content_stt)
            sheet.write('B{}'.format(row), line.employee_id.code_name or u'', content)
            sheet.write('C{}'.format(row), line.employee_id.name or u'', content)
            sheet.write('D{}'.format(row), line.employee_id.job_id.name or u'', content)
            sheet.write('E{}'.format(row), bank, content)
            sheet.write('F{}'.format(row), bank_account, content)
            sheet.write('G{}'.format(row), wage, content_number)
            sheet.write('H{}'.format(row), normal_day, content_stt)
            sheet.write('I{}'.format(row), worked_day, content_stt)
            sheet.write('J{}'.format(row), annual_day, content_stt)
            sheet.write('K{}'.format(row), salary, content_number)
            sheet.write('L{}'.format(row), family_sub, content_number)
            sheet.write('M{}'.format(row), bhxh, content_number)
            sheet.write('N{}'.format(row), bhyt, content_number)
            sheet.write('O{}'.format(row), bhtn, content_number)
            sheet.write('P{}'.format(row), u'', content)
            sheet.write('Q{}'.format(row), ttncn, content_number)
            sheet.write('R{}'.format(row), net_wage, content_number)
            stt += 1
            row += 1


ReportPayslip('report.btek_hr_holiday.report.payslip.xlsx',
              'hr.payslip.run')
