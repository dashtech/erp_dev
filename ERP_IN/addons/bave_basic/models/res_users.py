# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def get_user_info(self):
        res = super(ResUsers, self).get_user_info()
        res['package'] = 'basic'
        return res