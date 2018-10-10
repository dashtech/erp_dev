# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
import datetime, pytz


class ChangeDateTime(models.Model):
    _name = 'change.datetime'
    _description = 'Change Datetime'

    def change_utc_to_local_datetime(self, souce_date, option):
        user_tz = self.env.user.tz or str(pytz.utc)
        tz_now = datetime.datetime.now(pytz.timezone(user_tz))
        difference = tz_now.utcoffset().total_seconds() / 60 / 60
        difference = int(difference)
        utc_date = datetime.datetime.strptime(souce_date, '%Y-%m-%d %H:%M:%S')
        local_date = utc_date + datetime.timedelta(hours=difference)
        return local_date.strftime(option)

    def change_local_datetime_to_utc(self, souce_date, option):
        user_tz = self.env.user.tz or str(pytz.utc)
        tz_now = datetime.datetime.now(pytz.timezone(user_tz))
        difference = tz_now.utcoffset().total_seconds() / 60 / 60
        difference = int(difference)
        local_date = datetime.datetime.strptime(souce_date,
                                                '%Y-%m-%d %H:%M:%S')
        utc_date = local_date + datetime.timedelta(hours=-difference)
        return utc_date.strftime(option)
