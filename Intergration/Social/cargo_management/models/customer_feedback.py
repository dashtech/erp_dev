# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
import datetime


class CustomerFeedback(models.Model):
    _name = 'customer.feedback'
    _description = 'Customer Feedback'

    name = fields.Char(required=True,
                       readonly=True, string='STT')
    member_id = fields.Many2one('member', string='Customer',
                                required=True)
    service_provider_id = fields.Many2one(
        'service.provider', string='Service Provider',
        required=True)
    detail = fields.Text()
    ranking = fields.Selection(
        [('0', '0'), ('1', '1'), ('2', '2'),
         ('3', '3'), ('4', '4')], 'Ranking')

    _sql_constraints = [
        ('quotation_name_unique', 'UNIQUE(name)',
         _('STT must be unique!')),
    ]

    @api.model
    def create(self, vals):
        name = self.env['ir.sequence'].next_by_code('customer.feedback')
        vals['name'] = name

        return super(CustomerFeedback, self).create(vals)