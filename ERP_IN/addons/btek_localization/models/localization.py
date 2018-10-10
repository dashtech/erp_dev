# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCountryDistrict(models.Model):
    _name = "res.country.district"
    _description = "District"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(string='District Code', help='The district code.',
                       required=True)
    country_id = fields.Many2one('res.country', string='Country',
                                 required=True,
                                 default=lambda self: self.env.ref('base.vn'))
    state_id = fields.Many2one('res.country.state', string='State',
                               required=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('state_code_uniq', 'unique(state_id, code)',
         'The code of the district must be unique by state !')
    ]


class ResCountryWard(models.Model):
    _name = "res.country.ward"
    _description = "ward"

    name = fields.Char(required=True, translate=True)
    code = fields.Char(string='Ward Code', help='The ward code.',
                       required=True)
    country_id = fields.Many2one('res.country', string='Country',
                                 required=True,
                                 default=lambda self: self.env.ref('base.vn'))
    state_id = fields.Many2one('res.country.state', string='State',
                               required=True)
    district_id = fields.Many2one('res.country.district', string='District',
                                  required=True)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('district_code_uniq', 'unique(district_id, code)',
         'The code of the ward must be unique by district !')
    ]
