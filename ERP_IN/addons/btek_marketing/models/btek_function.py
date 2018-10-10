#!/usr/bin/python
# -*- encoding: utf-8 -*-

from odoo import fields, models, _


# model thong tin chuc vu trong res.partner

class BtekFunction(models.Model):
    _name = 'btek.function'
    _description = 'Btek Function'

    name = fields.Char()
    note = fields.Text()
    active = fields.Boolean(default=True)


# model congty/ngành/dichvu

class BtekCareer(models.Model):
    _name = 'btek.career'
    _description = 'Company/Career/Service'

    name = fields.Char()
    note = fields.Text()
    active = fields.Boolean(default=True)

