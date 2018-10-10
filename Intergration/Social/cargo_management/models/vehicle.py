# -*- coding: utf-8 -*-
from odoo import api, tools, fields, models, _


class Vehicle(models.Model):
    _name = "vehicle"
    _description = "Vehicle"
    _rec_name = 'plate'

    plate = fields.Char(
        required=True)
    vehicle_type = fields.Char()
    model_id = fields.Many2one(
        'car.vehicle.model', 'Model',
        required=True)
    car_color_id = fields.Many2one('car.color', string="Color")
    year = fields.Char()
    vin_number = fields.Char()
    vehicle_number = fields.Char()
    plate_search = fields.Char()
    member_id = fields.Many2one('member', 'Member', required=True)
    obd_mac_address = fields.Char('Obd MAC Address')
    brand_id = fields.Many2one('car.manufacturer', 'Brand')
    name = fields.Char(required=1)
    avatar = fields.Binary(attachment=True)
    avatar_medium = fields.Binary(attachment=True, string='Avatar')
    avatar_small = fields.Binary(attachment=True)

    @api.model
    def create(self, vals):
        tools.image_resize_images(
            vals, 'avatar', 'avatar_medium', 'avatar_small')
        return super(Vehicle, self).create(vals)

    @api.multi
    def write(self, vals):
        tools.image_resize_images(
            vals, 'avatar', 'avatar_medium', 'avatar_small')
        return super(Vehicle, self).write(vals)
