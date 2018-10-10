# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from datetime import datetime
import re
from odoo.exceptions import ValidationError

class DatetoPayroll(models.Model):
    _name = 'date.to.payroll'

    name = fields.Char()
    month = fields.Integer()
    date_from = fields.Date()
    date_to = fields.Date()
    config_id = fields.Many2one('config.payroll.day')
