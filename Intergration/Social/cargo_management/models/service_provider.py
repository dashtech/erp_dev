# -*- coding: utf-8 -*-
from odoo import api, tools, fields, models, _
import datetime
from operator import itemgetter


class service_provider_categ(models.Model):
    _name = 'service.provider.categ'
    _description = 'service.provider.categ'

    name = fields.Char(required=True)
    description = fields.Char()
    active = fields.Boolean(default=True)
    icon = fields.Binary(attachment=True)


class car_manufacturer(models.Model):
    _name = 'car.manufacturer'
    _description = 'car.manufacturer'

    name = fields.Char(required=True)
    logo = fields.Binary(attachment=True)
    logo_medium = fields.Binary(attachment=True)
    logo_small = fields.Binary(attachment=True)
    description = fields.Char()
    active = fields.Boolean(default=True)
    service_provider_id = fields.Many2one('service.provider', "Service provider")
    avatar = fields.Binary(attachment=True)
    avatar_medium = fields.Binary(attachment=True, string='Avatar')
    avatar_small = fields.Binary(attachment=True)

    @api.model
    def create(self, vals):
        tools.image_resize_images(
            vals, 'logo', 'logo_medium', 'logo_small')
        tools.image_resize_images(
            vals, 'avatar', 'avatar_medium', 'avatar_small')
        return super(car_manufacturer, self).create(vals)

    @api.multi
    def write(self, vals):
        tools.image_resize_images(
            vals, 'logo', 'logo_medium', 'logo_small')
        tools.image_resize_images(
            vals, 'avatar', 'avatar_medium', 'avatar_small')
        return super(car_manufacturer, self).write(vals)


class CarColor(models.Model):
    _name = 'car.color'
    _description = 'Car Color'

    name = fields.Char(required=True)
    description = fields.Char()
    active = fields.Boolean(default=True)
    car_vehicle_model_ids = fields.Many2many(
        'car.vehicle.model', 'car_vehicle_model_color_rel',
        'car_color_id', 'car_vehicle_model_id',
        string='Colors')


class car_vehicle_model(models.Model):
    _name = 'car.vehicle.model'
    _description = 'car.vehicle.model'
    _rec_name = 'full_name'

    name = fields.Char(required=True)
    manufacturer_id = fields.Many2one(
        'car.manufacturer', 'Manufacturer',
        required=True)
    full_name = fields.Char(compute='_compute_full_name', readonly=True)
    description = fields.Char()
    active = fields.Boolean(default=True)
    car_color_ids = fields.Many2many('car.color',
                                     'car_vehicle_model_color_rel',
                                     'car_vehicle_model_id', 'car_color_id',
                                     string='Colors')

    @api.multi
    @api.depends('name', 'manufacturer_id')
    def _compute_full_name(self):
        for s in self:
            if s.name and s.manufacturer_id:
                s.full_name = unicode(s.manufacturer_id.name_get()[0][1]) + \
                              u' - ' + unicode(s.name)


class service_provider(models.Model):
    _name = "service.provider"

    spo_id = fields.Float(digits=(10,0))
    name = fields.Char(required=True)
    categ_ids = fields.Many2many('service.provider.categ', 'service_provider_service_categ_rel',
                                 'service_provider_id', 'categ_id', string='Gara type')
    model_ids = fields.Many2many(
        'car.vehicle.model', 'service_provider_model_rel',
        'provider_id', 'model_id', string='Models')

    type = fields.Char()
    code = fields.Char()
    description = fields.Char()
    address = fields.Char()
    country_id = fields.Many2one(
        'res.country',
        default = lambda s:s.env.ref('base.vn').id)
    state_id = fields.Many2one(
        'res.country.state',
        string='Province'
    )
    district_id = fields.Many2one(
        'res.country.district',
        string='District'
    )
    ward_id = fields.Many2one(
        'res.country.ward',
        string='Ward'
    )
    logo = fields.Binary(attachment=True)
    logo_medium = fields.Binary(attachment=True)
    logo_small = fields.Binary(attachment=True)
    ranking = fields.Selection(
        [('0', '0'), ('1', '1'), ('2', '2'),
         ('3', '3'), ('4', '4')],
        'Ranking'
    )
    active = fields.Boolean(default=True)

    avatar = fields.Binary(attachment=True)
    avatar_medium = fields.Binary(attachment=True,
                                  string='Avatar')
    avatar_small = fields.Binary(attachment=True)
    banner_medium = fields.Binary(attachment=True, string="Banner")
    maps_img = fields.Binary(attachment=True, string="Maps")
    manufacturer_ids = fields.One2many('car.manufacturer', 'service_provider_id',
                                       'Manufacturer')
    service_catalog_ids = fields.One2many(
        'service.catalog', 'service_provider_id',
        'Service catalog')
    service_package_ids = fields.One2many('service.package', 'service_provider_id', 'Service package')
    service_ids = fields.One2many('services', 'service_provider_id', "Services")
    # service_ids = fields.Many2many(
    #     compute='_compute_service_ids',
    #     string='Services', relation='services',
    #     comodel_name='services')

    free_service_ids = fields.Many2many('free.service', 'service_provider_free_service_rel',
                                        'service_provider_id', 'free_service_id', 'Free service')
    album_ids = fields.One2many(
        'album', 'provider_id', 'Albums')

    user_id = fields.Many2one(
        'res.users', 'Corresponding users')

    banner = fields.Char()
    phone = fields.Char()
    website = fields.Char()
    introduction = fields.Char()
    likecount = fields.Float(digits=(10,0))
    viewcount = fields.Float(digits=(10,0))
    sharecount = fields.Float(digits=(10,0))
    commentcount = fields.Float(digits=(10,0))
    # ranking = fields.Float(digits=(10,0))
    opentime = fields.Char(compute='_compute_opentime', store=1)
    opentime_show = fields.Char()
    closetime = fields.Char(compute='_compute_closetime', store=1)
    closetime_show = fields.Char()
    longitude = fields.Float()
    latitude = fields.Float()
    notify = fields.Char()
    notify_type = fields.Char()
    notify_mobile = fields.Char()
    notify_email = fields.Char()
    notify_time = fields.Char()
    g_place_id = fields.Char()
    # country_id = fields.Float(digits=(10,0))
    province_id = fields.Float(digits=(10,0))
    ratecount = fields.Float()
    facebook = fields.Char()
    email = fields.Char()

    @api.model
    def create(self, vals):
        tools.image_resize_images(
            vals, 'logo', 'logo_medium', 'logo_small')
        tools.image_resize_images(
            vals, 'avatar', 'avatar_medium', 'avatar_small')
        return super(service_provider, self).create(vals)

    @api.multi
    def write(self, vals):
        tools.image_resize_images(
            vals, 'logo', 'logo_medium', 'logo_small')
        tools.image_resize_images(
            vals, 'avatar', 'avatar_medium', 'avatar_small')
        return super(service_provider, self).write(vals)

    @api.multi
    @api.depends('opentime_show')
    def _compute_opentime(self):
        for s in self:
            s.opentime = s.to_time(s.opentime_show)

    @api.multi
    @api.depends('closetime_show')
    def _compute_closetime(self):
        for s in self:
            s.closetime = s.to_time(s.closetime_show)

    def to_time(self, time):
        time = unicode(time)
        if '.' not in time:
            time_ = time + ':00'
        else:
            time = time.split('.')
            hour = time[0] + ':'
            min = round(float('0.' + time[1]) * 60, 0)
            time_ = hour + unicode(min)[:-2]
        return time_
    # @api.multi
    # def _compute_service_ids(self):
    #     for provider in self:
    #         service_ids = []
    #         for catalog in provider.service_catalog_ids:
    #             service_ids.extend(catalog.service_ids._ids)
    #         provider.service_ids = service_ids

