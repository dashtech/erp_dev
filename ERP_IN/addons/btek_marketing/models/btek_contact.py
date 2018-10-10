#!/usr/bin/python
# -*- encoding: utf-8 -*-

from odoo import models, fields, api


class BtekContact(models.Model):
    _inherit = 'mail.mass_mailing.contact'

    mobile = fields.Char()
    zalo_id = fields.Char(string='Zalo ID')
    viber_id = fields.Char(string='Viber ID')
    facebook_id = fields.Char(string='Facebook ID')
    is_invite_zalo = fields.Boolean(default=False)

    @api.onchange('zalo_id')
    def _change_is_invite_zalo(self):
        if self.zalo_id:
            self.is_invite_zalo = True
