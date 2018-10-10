# -*- coding: utf-8 -*-
from odoo import api, tools, fields, models, _


class Voucher(models.Model):
    _name = "voucher"
    _description = "voucher"
    _rec_name = 'title'

    stt = fields.Char(readonly=True)
    service_provider_id = fields.Many2one(
        'service.provider', 'Service provider',
        required=True)
    title = fields.Char(required=True)
    value = fields.Float(digits=(10,0))
    type = fields.Selection(
        [('1', '%'), ('2', 'Cash'),
         ('3', 'Product'), ('4', 'Gift')],
        required=True)
    start_date = fields.Date()
    end_date = fields.Date()
    banner = fields.Binary(attachment=True)
    banner_medium = fields.Binary(attachment=True)
    banner_small = fields.Binary(attachment=True)

    member_ids = fields.Many2many(
        'member', 'voucher_member_rel',
        'voucher_id', 'member_id',
        'Member')

    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('voucher_stt_unique', 'UNIQUE(stt)',
         _('STT must be unique!')),
    ]

    @api.model
    def default_get(self, fields_list):
        res = super(Voucher, self).default_get(fields_list)
        service_providers = self.env['service.provider'].search([])
        res['service_provider_id'] = service_providers and service_providers[0].id or False

        return res

    @api.model
    def create(self, vals):
        tools.image_resize_images(
            vals, 'banner', 'banner_medium', 'banner_small')

        name = self.env['ir.sequence'].next_by_code('voucher')
        vals['stt'] = name

        return super(Voucher, self).create(vals)

    @api.multi
    def write(self, vals):
        tools.image_resize_images(
            vals, 'banner', 'banner_medium', 'banner_small')
        return super(Voucher, self).write(vals)

