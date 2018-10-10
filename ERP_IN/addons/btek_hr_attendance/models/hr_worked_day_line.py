# -*- coding: utf-8 -*-
from odoo import fields, models, api
from datetime import datetime, date, timedelta


class EmployeeWorkedDay(models.Model):
    _name = 'hr.worked.day.line'

    worked_day_id = fields.Many2one('hr.worked.day')
    date = fields.Char()
    worked = fields.Float()
    day = fields.Char()
