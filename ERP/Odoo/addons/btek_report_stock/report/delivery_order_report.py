# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import datetime
from odoo.report import report_sxw
import time


class DeliveryOder(models.Model):
    _inherit = 'stock.picking'

    def get_time_today(self):
        date_now = datetime.datetime.now()
        year = str(date_now.year)
        month = str(date_now.month)
        day = str(date_now.day)
        return u'Ngày ' + day + u' tháng ' + month + u' năm ' + year

    @api.depends('min_date')
    def get_min_date_word(self):
        if self.min_date:
            min_date_temp = datetime.datetime.strptime(self.min_date, '%Y-%m-%d %H:%M:%S')
            min_date_year = str(min_date_temp.year)
            min_date_month = str(min_date_temp.month)
            min_date_day = str(min_date_temp.day)
        return u'Ngày ' + min_date_day + u' tháng ' + min_date_month + u' năm ' + min_date_year



