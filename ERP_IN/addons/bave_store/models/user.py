# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import datetime
import string, random


class ResUsersToken(models.Model):
    _name = 'res.users.token'

    user_id = fields.Many2one('res.users', 'User',
                              required=True)
    name = fields.Char(required=True)
    expiration_date = fields.Datetime(required=True)

    @api.model
    def create(self, vals):
        expiration_date = datetime.datetime.now() + datetime.timedelta(hours=2)
        expiration_date = expiration_date.strftime('%Y-%m-%d %H:%M:%S')
        vals['expiration_date'] = expiration_date

        token = ''.join(
            random.choice(string.ascii_letters) for x in
            range(random.randint(150, 250)))
        vals['name'] = token

        return super(ResUsersToken, self).create(vals)


class ResUsers(models.Model):
    _inherit = 'res.users'

    token_ids = fields.One2many('res.users.token', 'user_id',
                                readonly=True)

    @api.model
    def check_bave_store_authencation(self, login, token):
        if not login or not token:
            return False
        domain = [('login', '=', login)]
        users = self.search(domain)
        if not users:
            return False

        current_date = \
            datetime.datetime.now().strftime(
                '%Y-%m-%d %H:%M:%S')
        token_domain = [('user_id', '=', users[0].id),
                        ('name', '=', token),
                        ('expiration_date', '>', current_date)]

        token_s = self.env['res.users.token'].search(token_domain)
        if not token_s:
            return False
        return users[0]

    @api.model
    def generate_token(self):
        self.ensure_one()
        vals = {
            'user_id': self.id
        }
        token =  self.env['res.users.token'].create(vals)
        return token.name
