# -*- coding: utf-8 -*-
from odoo import fields, models, api


class LocalizationResPartner(models.Model):
    _inherit = 'res.partner'

    # change localization res.patner, add district, ward
    district_id = fields.Many2one('res.country.district',
                                  string='District')
    ward_id = fields.Many2one('res.country.ward',
                              string='Ward')
    address = fields.Char(compute='_compute_address', readonly=True)

    @api.multi
    @api.depends('street', 'country_id', 'state_id', 'district_id', 'ward_id')
    def _compute_address(self):
        for s in self:
            address_list = []
            if s.street:
                address_list.append(s.street)
            if s.ward_id:
                address_list.append(s.ward_id.name)
            if s.district_id:
                address_list.append(s.district_id.name)
            if s.state_id:
                address_list.append(s.state_id.name)
            if s.country_id:
                address_list.append(s.country_id.name)
            s.address = ', '.join(address_list)

    @api.onchange('country_id')
    def change_country_id(self):
        self.state_id = False

    @api.onchange('state_id')
    def change_state_id(self):
        self.district_id = False

    @api.onchange('district_id')
    def change_district_id(self):
        self.ward_id = False
