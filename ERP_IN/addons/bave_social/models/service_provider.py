# -*- coding: utf-8 -*-
from odoo import api, tools, fields, models, _


class service_provider_categ(models.Model):
    _name = 'service.provider.categ'
    _description = 'service.provider.categ'
    _inherit = 'social.connect'

    name = fields.Char(required=True)
    description = fields.Char()
    active = fields.Boolean(default=True)


class car_manufacturer(models.Model):
    _name = 'car.manufacturer'
    _description = 'car.manufacturer'
    _inherit = 'social.connect'

    name = fields.Char(required=True)
    logo = fields.Binary(attachment=True)
    logo_medium = fields.Binary(attachment=True)
    logo_small = fields.Binary(attachment=True)
    description = fields.Char()
    active = fields.Boolean(default=True)
    service_provider_id = fields.Many2one('service.provider')
    avatar = fields.Binary(attachment=True)
    avatar_medium = fields.Binary(attachment=True, string='Avatar')
    avatar_small = fields.Binary(attachment=True)

    # @api.model
    # def create(self, vals):
    #     tools.image_resize_images(
    #         vals, 'logo', 'logo_medium', 'logo_small')
    #     return super(car_manufacturer, self).create(vals)
    #
    # @api.multi
    # def write(self, vals):
    #     tools.image_resize_images(
    #         vals, 'logo', 'logo_medium', 'logo_small')
    #     return super(car_manufacturer, self).write(vals)


class car_vehicle_model(models.Model):
    _name = 'car.vehicle.model'
    _description = 'car.vehicle.model'
    _rec_name = 'full_name'
    _inherit = 'social.connect'

    name = fields.Char(required=True)
    manufacturer_id = fields.Many2one(
        'car.manufacturer', 'Manufacturer',
        required=True)
    full_name = fields.Char(compute='_compute_full_name', readonly=True)
    description = fields.Char()
    active = fields.Boolean(default=True)
    icon = fields.Binary(attachment=True)

    # @api.multi
    # @api.depends('name', 'manufacturer_id')
    # def _compute_full_name(self):
    #     for s in self:
    #         if s.name and s.manufacturer_id:
    #             s.full_name = str(
    #                 s.manufacturer_id.name_get()[0][1]) + ' - ' + str(s.name)


class ServiceProvider(models.Model):
    _name = "service.provider"
    _inherit = 'social.connect'

    spo_id = fields.Float(digits=(10, 0))
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
        'res.country', required=True,
        default=lambda s: s.env.ref('base.vn').id)
    state_id = fields.Many2one(
        'res.country.state', required=True,
        string='Province'
    )
    district_id = fields.Many2one(
        'res.country.district',
        required=True, string='District'
    )
    ward_id = fields.Many2one(
        'res.country.ward',
        required=True, string='Ward'
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
    maps_img = fields.Binary(attachment=True, string="Maps")
    service_catalog_ids = fields.One2many('service.catalog',
                                          'service_provider_id','Service catalog')
    service_package_ids = fields.One2many('service.package', 'service_provider_id', 'Service package')
    service_ids = fields.One2many('services', 'service_provider_id', 'Services')
    free_service_ids = fields.Many2many('free.service', 'service_provider_free_service_rel',
                                        'service_provider_id', 'free_service_id', 'Free service')
    manufacturer_ids = fields.One2many('car.manufacturer', 'service_provider_id',
                                       'Manufacturer')
    album_ids = fields.One2many(
        'album', 'provider_id', 'Albums')

    user_id = fields.Many2one(
        'res.users', 'Corresponding users')
    # product_ids = fields.Many2many('product.product', 'provider_product_rel', 'provider_id', 'product_id')
    banner = fields.Char()
    banner_medium = fields.Binary(attachment=True, string="Banner Image")
    phone = fields.Char()
    website = fields.Char()
    introduction = fields.Char()
    likecount = fields.Float(digits=(10, 0))
    viewcount = fields.Float(digits=(10, 0))
    sharecount = fields.Float(digits=(10, 0))
    commentcount = fields.Float(digits=(10, 0))
    # ranking = fields.Float(digits=(10,0))
    opentime = fields.Char()
    opentime_show = fields.Char()
    closetime = fields.Char()
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
    province_id = fields.Float(digits=(10, 0))
    ratecount = fields.Float()
    facebook = fields.Char()
    email = fields.Char()

    def quick_choose(self):
        action_obj = self.env.ref('bave_social.action_wizard_service_package')
        action = action_obj.read([])[0]
        # action['res_id'] = self[0].id
        return action

    def quick_choose_service(self):
        action_obj = self.env.ref('bave_social.action_wizard_service')
        action = action_obj.read([])[0]
        # action['res_id'] = self[0].id
        return action



    # @api.model
    # def create(self, vals):
    #     tools.image_resize_images(
    #         vals, 'logo', 'logo_medium', 'logo_small')
    #     tools.image_resize_images(
    #         vals, 'avatar', 'avatar_medium', 'avatar_small')
    #     return super(service_provider, self).create(vals)
    #
    @api.multi
    def write(self, vals):
        # if vals.has_key('mrp_bom_ids'):
        #     bom_ids = vals['mrp_bom_ids'][0][2]
        #     pack_ids = self.env['mrp.bom'].browse(bom_ids)
        #     pack = []
        #     service = []
        #     for pack_id in pack_ids:
        #         if not pack_id.bom_line_ids:
        #             service = False
        #         else:
        #             for bom in pack_id.bom_line_ids:
        #                 service.append((0, 0, {'name': bom.display_name,
        #                                        'prefer_product_id': bom.product_id.id}))
        #         pack.append((0, 0, {'name': pack_id.display_name,
        #                      'prefer_bom_id': pack_id.id, 'service_ids': service}))
        #     vals['service_package_ids'] = pack
        #     vals.pop('mrp_bom_ids')
        #
        # if vals.has_key('product_ids'):
        #     product_ids = vals['product_ids'][0][2]
        #     products = self.env['product.product'].browse(product_ids)
        #     service = []
        #     for product in products:
        #         service.append((0, 0, {'name': product.name,
        #                                'prefer_product_id': product.id}))
        #     vals['service_ids'] = service
        #     vals.pop('product_ids')
        res = super(ServiceProvider, self).write(vals)
        return res
