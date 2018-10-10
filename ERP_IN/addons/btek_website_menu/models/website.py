# -*- encoding: utf-8 -*-
from odoo import fields, models, api, _


class Website(models.Model):
    _inherit = 'website'

    def get_contact_info(self):
        phone = self.env['ir.config_parameter'].get_param(
            'website.contact.phone', default='0934 63 23 43')
        email = self.env['ir.config_parameter'].get_param(
            'website.contact.email', default='contact@bave.io')
        res = {
            'phone': phone,
            'email': email,
        }
        return res

    def get_login_logo(self):
        hongminh_logo = self.env['ir.config_parameter'
        ].get_param('hongminh.logo')
        if hongminh_logo:
            return '/btek_website_menu/static/src/img/hongminh_logo.png'
        return '/btek_website_menu/static/src/img/bave_agara_logo.png'
