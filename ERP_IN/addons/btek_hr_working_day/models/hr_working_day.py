# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.tools.sql import drop_view_if_exists
from odoo.exceptions import UserError, ValidationError
import pytz
from dateutil import parser


class HrWorkingDay(models.Model):
    _name = 'hr.working.day'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _table = 'hr_working_day'
    _order = "id desc"
    _description = "Working Day"

    def _default_date_from(self):
        user = self.env['res.users'].browse(self.env.uid)
        r = user.company_id and user.company_id.timesheet_range or 'month'
        if r == 'month':
            return time.strftime('%Y-%m-01')
        elif r == 'week':
            return (datetime.today() + relativedelta(weekday=0, days=-6)).strftime('%Y-%m-%d')
        elif r == 'year':
            return time.strftime('%Y-01-01')
        return fields.Date.context_today(self)

    def _default_date_to(self):
        user = self.env['res.users'].browse(self.env.uid)
        r = user.company_id and user.company_id.timesheet_range or 'month'
        if r == 'month':
            return (datetime.today() + relativedelta(months=+1, day=1, days=-1)).strftime('%Y-%m-%d')
        elif r == 'week':
            return (datetime.today() + relativedelta(weekday=6)).strftime('%Y-%m-%d')
        elif r == 'year':
            return time.strftime('%Y-12-31')
        return fields.Date.context_today(self)

    def _default_employee(self):
        emp_ids = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return emp_ids and emp_ids[0] or False

    def _default_company_id(self):
        user_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        return user_id.company_id.id and user_id[0].company_id.id or False

    name = fields.Char(required=True)
    month = fields.Selection([('1', 'January'), ('2', 'February '), ('3', 'March'),
                              ('4', 'April'), ('5', 'May'), ('6', 'June'),
                              ('7', 'July'), ('8', 'August'), ('9', 'September'),
                              ('10', 'October'), ('11', 'November'), ('12', 'December')])
    date_from = fields.Date(string='Date From', default=_default_date_from, required=True,
                            index=True, readonly=True, states={'draft': [('readonly', False)]})
    date_to = fields.Date(string='Date To', default=_default_date_to, required=True,
                          index=True, readonly=True, states={'draft': [('readonly', False)]})
    department_ids = fields.Many2many('hr.department', string='Department', states={'draft': [('readonly', False)]})
    state = fields.Selection([('draft', 'Draft'), ('validated', 'Waiting Approval'),
                              ('done', 'Approved')], default='draft')
    company_id = fields.Many2one('res.company', 'Company', default=_default_company_id,
                                 states={'draft': [('readonly', False)]})

    timesheet_ids = fields.One2many('hr.working.day.employee.line', 'day_id',
                                    string='Timesheet lines',
                                    readonly=True, states={'draft': [('readonly', False)]})

    # @api.multi
    # def write(self, values):
    #     res = super(HrWorkingDay, self).write(values)
    #     if self.state != 'draft':
    #         raise ValidationError(_('Please set to draft before edit timesheets!'))
    #     return res

    def action_comfirm(self):
        if not self.timesheet_ids:
            raise UserError(_('Can not send total timesheet when timesheet detail empty!'))
        self.write({'state': 'validated'})

    def action_approve(self):
        working_emp = self.env['hr.working.day.employee']
        for ts in self.timesheet_ids:
            exist_ts = working_emp.search([('employee_id', '=', ts.employee_id.id), ('date', '=', ts.date)])
            if not exist_ts:
                working_emp.create({
                    'employee_id': ts.employee_id.id,
                    'unit_amount': ts.unit_amount,
                    'date': ts.date,
                })
        self.write({"state": 'done'})
        return True

    def action_set_draft(self):
        self.write({'state': 'draft'})
