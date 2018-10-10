# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import ValidationError
import calendar


class HrKpiEmpoyeeLine(models.Model):
    _name = 'hr.kpi.employee.line'

    employee_id = fields.Many2one('hr.employee', 'Employee')
    kpi_id = fields.Many2one('hr.kpi.employee')
    rate = fields.Integer()
