# -*- coding: utf-8 -*-

from odoo import fields, models, api
from datetime import datetime, date


class HrPublicHoliday(models.Model):
    _name = 'btek.hr.public.holiday'
    _rec_name = 'year'

    year = fields.Char(default=date.today().year, string='Year')
    employee_tag = fields.Many2one('hr.employee.category', string='Employee Tag')
    hr_holiday_status = fields.Many2one('hr.holidays.status', string='Leave Type')
    public_holiday_line = fields.One2many('btek.hr.public.holiday.line', 'public_holiday_id')


class CalendarEventType(models.Model):
    _inherit = 'calendar.event.type'

    name = fields.Char('Name', required=True, translate=True)
