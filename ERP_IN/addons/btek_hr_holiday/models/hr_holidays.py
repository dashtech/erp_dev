# -*- coding: utf-8 -*-
# Copyright 2017 Eficent Business and IT Consulting Services S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, api, models
from datetime import datetime, timedelta


class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    day_ez = fields.Date('Date', compute='_compute_current_day', store=True)

    @api.multi
    @api.depends('number_of_days_temp')
    def _compute_current_day(self):
        for record in self:

            if record.number_of_days_temp and record.date_from:
                record.day_ez = datetime.strptime(record.date_from, '%Y-%m-%d %H:%M:%S')

