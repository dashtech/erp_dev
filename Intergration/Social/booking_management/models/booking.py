# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools


class Booking(models.Model):
    _name = "booking"
    _description = "Booking management"

    def _default_provider(self):
        uid_ = self.env.user.id
        providers = self.env['service.provider'].search([
            ('user_id', '=', uid_)])
        if not providers:
            return
        return providers[0].id

    member_id = fields.Many2one(
        'member', required=True, string='Member')
    avatar = fields.Binary(attachment=True)
    avatar_medium = fields.Binary(attachment=True)
    avatar_small = fields.Binary(attachment=True)
    mobile_phone = fields.Char(related='member_id.mobile_phone',
                               readonly=True)
    gender = fields.Selection([('male', 'Male'),
                               ('female', 'Female'),
                               ('other', 'Other')])
    address = fields.Char()
    country_id = fields.Many2one(
        'res.country',
        default=lambda s: s.env.ref('base.vn').id)
    state_id = fields.Many2one(
        'res.country.state',
        string='Province'
    )
    district_id = fields.Many2one(
        'res.country.district', string='District'
    )
    ward_id = fields.Many2one(
        'res.country.ward', string='Ward'
    )
    service_provider_id = fields.Many2one('service.provider', 'Service provider',
                                          default=_default_provider, required=True)

    booking_time = fields.Datetime(required=True)
    # car_plate = fields.Char()
    vehicle_id = fields.Many2one('vehicle', 'Car plate',
                                 required=0)
    car_vehicle_model_id = fields.Many2one('car.vehicle.model')
    promotion_number = fields.Integer()
    channel = fields.Selection([('cargo', 'Cargo'),
                                ('web', 'Web'),
                                ('call', 'Call'),
                                ('other', 'Other')])

    state = fields.Selection([('draft', 'Draft'), ('contacted', 'Contacted'),
                              ('confirm', 'Confirm'), ('done', 'Done'),
                              ('cancel', 'Cancel')], default='draft')
    note = fields.Text(default=' ')
    services_ids = fields.Many2many('services', 'booking_services_rel',
                                    'booking_id', 'services_id', string='Service')
    services_package_ids = fields.Many2many('service.package',
                                            'booking_services_package_rel',
                                            'booking_id', 'package_id', string='Service Package')
    notif = fields.Char('Notify')
    type = fields.Char()
    fleet_repair_id = fields.Integer('Fleet repair')
    sale_order_id = fields.Integer('Sale order')

    @api.model
    def create(self, vals):
        tools.image_resize_images(
            vals, 'avatar', 'avatar_medium', 'avatar_small')
        return super(Booking, self).create(vals)

    @api.multi
    def write(self, vals):
        tools.image_resize_images(
            vals, 'avatar', 'avatar_medium', 'avatar_small')
        return super(Booking, self).write(vals)

    def action_confirm(self):
        return self.write({'state': 'confirm'})

    def action_done(self):
        return self.write({'state': 'done'})

    def action_cancel(self):
        return self.write({'state': 'cancel'})

    def action_connect(self):
        return self.write({'state': 'contacted'})