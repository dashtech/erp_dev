# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessDenied, UserError
import datetime
import odoo


class ResUsers(models.Model):
    _inherit = 'res.users'

    expiration_datetime = fields.Datetime()

    @api.model
    def check_expiration_datetime(self):
        user = self.sudo().search(
            [('id', '=', self._uid)])
        if not user.expiration_datetime:
            return True

        expiration_datetime = datetime.datetime.strptime(
            user.expiration_datetime,
            '%Y-%m-%d %H:%M:%S')

        if expiration_datetime < datetime.datetime.now():
            return False
        return True

    @api.model
    def check_credentials(self, password):
        if not self.check_expiration_datetime():
            raise AccessDenied()

        try:
            return super(ResUsers, self).check_credentials(password)
        except odoo.exceptions.AccessDenied:
            users = self.sudo().search(
                [('id', '=', self._uid),
                 ('password_crypt', '=', password)])
            if not users:
                raise
