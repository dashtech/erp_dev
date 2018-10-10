# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import ValidationError
import calendar
from dateutil.relativedelta import relativedelta as mondelta


class HrBscDepartment(models.Model):
    _name = 'hr.bsc.department'
    _rec_name = 'department_id'

    company_id = fields.Many2one('res.company', 'Company')
    department_id = fields.Many2one('hr.department', 'Department')
    config_id = fields.Many2one('config.payroll.day', 'Configure')
    month = fields.Selection([('1', 'January'), ('2', 'February '),
                               ('3', 'March'), ('4', 'April'),
                               ('5', 'May'), ('6', 'June'),
                               ('7', 'July'), ('8', 'August'),
                               ('9', 'September'), ('10', 'October'),
                               ('11', 'November'), ('12', 'December')])
    start_date_readonly = fields.Date()
    start_date = fields.Date(compute='_compute_start_date')
    end_date_readonly = fields.Date()
    end_date = fields.Date(compute='_compute_end_date')
    value = fields.Integer(size=2)

    @api.onchange('month', 'config_id')
    def compute_date(self):
        if self.month and self.config_id:
            day = self.config_id.day_monthly_payment
            mon = str(self.month)
            year = self.config_id.year
            date_from = datetime.strptime('{}-{}-{}'.format(year, mon, day), '%Y-%m-%d')
            date_to = str(date_from + mondelta(months=+1, day=day, days=-1))[:10]
            self.start_date_readonly = date_from
            self.end_date_readonly = date_to

    @api.depends('start_date_readonly')
    def _compute_start_date(self):
        for s in self:
            s.start_date = s.start_date_readonly

    @api.depends('end_date_readonly')
    def _compute_end_date(self):
        for s in self:
            s.end_date = s.end_date_readonly

    @api.model
    def create(self, vals):
        res = super(HrBscDepartment, self).create(vals)
        check_create = self.env['hr.bsc.department'].sudo().search(
            [('company_id', '=', vals['company_id']),
             ('department_id', '=', vals['department_id']),
             ('config_id', '=', vals['config_id']),
             ('month', '=', vals['month'])])
        if len(check_create) > 1:
            raise ValidationError(_('Can not create because record existed'))
        if vals.has_key('value'):
            if vals['value'] > 100 or vals['value'] < 0:
                raise ValidationError(_('Value must in range 0 -> 100(%)'))
        return res

    @api.multi
    def write(self, vals):
        res = super(HrBscDepartment, self).write(vals)
        company_id =  self.company_id.id
        if vals.has_key('company_id'):
            company_id = vals['company_id']
        department_id = self.department_id.id
        if vals.has_key('department_id'):
            department_id = vals['department_id']
        config_id = self.config_id.id
        if vals.has_key('config_id'):
            config_id = vals['config_id']
        month = self.month
        if vals.has_key('month'):
            month = vals['month']
        if vals:
            check_edit = self.env['hr.bsc.department'].sudo().search(
                [('company_id', '=', company_id),
                 ('department_id', '=', department_id),
                 ('config_id', '=', config_id),
                 ('month', '=', month)])
            if len(check_edit) > 1:
                raise ValidationError(_('Can not save because record existed'))
            if vals.has_key('value'):
                if vals['value'] > 100 or vals['value'] < 0:
                    raise ValidationError(_('Value must in range 0 -> 100(%)'))
        return res

    @api.onchange('company_id')
    def change_company(self):
        if self.department_id:
            self.department_id = False
        if self.config_id:
            self.config_id = False
