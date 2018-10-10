# -*- coding: utf-8 -*-
from odoo import api, tools, fields, models, _


# UPDATE member SET id = DEFAULT;
class Member(models.Model):
    _name = "member"
    _description = "Member"
    _inherit = 'social.connect'

    name = fields.Char(required=True)
    type = fields.Char()
    address = fields.Char()
    job_title = fields.Char()
    abount_me = fields.Char()
    mobile_phone = fields.Char()
    email = fields.Char()
    birthday = fields.Char()
    ranking = fields.Selection(
        [('0', '0'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4')])
    work_for = fields.Char()
    study_at = fields.Char()
    high_school = fields.Char()
    study_degree = fields.Char()
    home_url = fields.Char()

    longitude = fields.Float(digits=(10,0))
    latitude = fields.Float(digits=(10,0))

    avatar = fields.Binary(attachment=True)
    avatar_medium = fields.Binary(attachment=True,
                                  string='Avatar')
    avatar_small = fields.Binary(attachment=True)

    banner = fields.Binary(attachment=True)
    banner_medium = fields.Binary(attachment=True,
                                  string='Avatar')
    banner_small = fields.Binary(attachment=True)

    hotline = fields.Char()
    agent_numeric = fields.Char()

    device_id = fields.Char()
    device_model = fields.Char()
    first_name = fields.Char()
    last_name = fields.Char()
    player_id = fields.Char()
    last_update = fields.Datetime()

    active = fields.Boolean(default=True)
