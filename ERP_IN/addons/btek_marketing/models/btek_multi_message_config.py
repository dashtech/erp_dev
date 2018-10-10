#!/usr/bin/python
# -*- encoding: utf-8 -*-

from odoo import models, fields, api


class BtekSMSConfig(models.Model):
    _name = 'btek.sms.config'
    _description = 'Btek SMS Config'

    sms_supplier = fields.Selection([('eSMS', 'eSMS')])
    name = fields.Char(string='Brand Name')
    api_key = fields.Char()
    secret_key = fields.Char()
    url = fields.Char()
    sms_type = fields.Selection([('1', 'Brandname dvertisement'), ('2', 'Brandname Customer Care'),
                                 ('3', 'Random numbers'), ('4', 'Fixed Number Notify'),
                                 ('6', 'Fixed number Verify'), ('7', 'OPT'),
                                 ('8', 'Fixed Number 10 Numbers'), ('13', 'Two-way message')])

    @api.onchange('sms_supplier')
    def _change_sms_type_by_sms_supplier(self):
        if self.sms_supplier != 'eSMS':
            self.sms_type = '3'


class BtekZaloConfig(models.Model):
    _name = 'btek.zalo.config'
    _description = 'Btek Zalo Config'
    _rec_name = 'spcode'

    spcode = fields.Char()
    url = fields.Char()
    total_follow = fields.Integer(readonly=True)



