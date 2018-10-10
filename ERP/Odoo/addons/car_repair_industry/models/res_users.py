# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def get_user_info(self):
        res = {}
        groups = []
        group_dict = {
            'car_repair_industry.group_gara_director': 'director',
            'car_repair_industry.group_fleet_repair_service_manager': 'service_advisor',
        }
        for xml_group_id in group_dict.keys():
            group = self.env.user.has_group(xml_group_id)

            if group:
                groups.append(group_dict[xml_group_id])
        res['groups'] = groups
        res['package'] = 'pro'
        return res
