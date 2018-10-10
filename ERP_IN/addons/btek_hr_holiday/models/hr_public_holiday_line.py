# -*- coding: utf-8 -*-
from odoo import fields, models


class HrPublicHolidayLine(models.Model):
    _name = 'btek.hr.public.holiday.line'

    public_holiday_id = fields.Many2one('btek.hr.public.holiday')
    name = fields.Char()
    date = fields.Date()
    desc = fields.Char('Description')
