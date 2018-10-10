# -*- coding: utf-8 -*-
from odoo import api, tools, fields, models, _


class Service_catalog(models.Model):
    _name = 'service.catalog'
    _description = 'Service catalog'

    def _default_provider(self):
        uid_ = self.env.user.id
        providers = self.env['service.provider'].search([
            ('user_id', '=', uid_)])
        if not providers:
            return
        return providers[0].id

    name = fields.Char(required=True)
    parent_id = fields.Many2one('service.catalog', 'Parent')
    avatar = fields.Binary(attachment=True)
    avatar_medium = fields.Binary(attachment=True,
                                  string='Avatar')
    avatar_small = fields.Binary(attachment=True)
    description = fields.Char()
    active = fields.Boolean(default=True)

    service_provider_id = fields.Many2one('service.provider', 'Service provider',
                                          default=_default_provider, required=0)
    service_ids = fields.Many2many('services', 'catalog_service_rel',
                                   'catalog_id', 'service_id', 'Services',)
    package_ids = fields.Many2many('service.package', 'catalog_pack_rel',
                                   'catalog_id', 'pack_id', 'Packages')
    service_names = fields.Char(
        # compute='_compute_service_names',
        string='Services')
    type = fields.Selection([('package', 'Package'), ('service', 'Service')],
                            default='package', required=True, string="Type")
    highlight = fields.Boolean('Highlight')

    @api.model
    def create(self, vals):
        tools.image_resize_images(
            vals, 'avatar', 'avatar_medium', 'avatar_small')
        return super(Service_catalog, self).create(vals)

    @api.multi
    def write(self, vals):
        tools.image_resize_images(
            vals, 'avatar', 'avatar_medium', 'avatar_small')
        return super(Service_catalog, self).write(vals)

    # @api.multi
    # def _compute_service_names(self):
    #     for catalog in self:
    #         service_names = [service.name for service in catalog.service_ids]
    #         catalog.service_names = ','.join(service_names)


class ServicePackage(models.Model):
    _name = 'service.package'
    _description = 'Service package'

    def _default_provider(self):
        uid_ = self.env.user.id
        providers = self.env['service.provider'].search([
            ('user_id', '=', uid_)])
        if not providers:
            return
        return providers[0].id

    name = fields.Char(required=True)
    avatar = fields.Binary(attachment=True)
    avatar_medium = fields.Binary(attachment=True,
                                  string='Avatar')
    avatar_small = fields.Binary(attachment=True)
    description = fields.Char()
    price = fields.Float()
    active = fields.Boolean(default=True)

    service_provider_id = fields.Many2one('service.provider', 'Service provider',
                                  default=_default_provider, required=1)
    service_ids = fields.Many2many('services', 'package_service_rel',
                                   'package_id', 'service_id', 'Services')
    service_names = fields.Char(
        # compute='_compute_service_names',
        string='Services')
    prefer_bom_id = fields.Integer()

    # @api.model
    # def create(self, vals):
    #     tools.image_resize_images(
    #         vals, 'avatar', 'avatar_medium', 'avatar_small')
    #     return super(ServicePackage, self).create(vals)
    #
    # @api.multi
    # def write(self, vals):
    #     tools.image_resize_images(
    #         vals, 'avatar', 'avatar_medium', 'avatar_small')
    #     return super(ServicePackage, self).write(vals)

    # @api.multi
    # def _compute_service_names(self):
    #     for pack in self:
    #         service_names = [service.name for service in pack.service_ids]
    #         pack.service_names = ','.join(service_names)


class Services(models.Model):
    _name = 'services'
    _description = 'Services'

    # @api.multi
    def _default_provider(self):
        uid_ = self.env.user.id
        providers = self.env['service.provider'].search([
            ('user_id', '=', uid_)])
        if not providers:
            return
        return providers[0].id

    name = fields.Char(required=True)
    service_catalog_id = fields.Many2many('service.catalog', 'catalog_service_rel',
                                          'catalog_id', 'service_id', 'Catalog')
    avatar = fields.Binary(attachment=True)
    avatar_medium = fields.Binary(attachment=True,
                                  string='Avatar')
    avatar_small = fields.Binary(attachment=True)
    service_provider_id = fields.Many2one(
        'service.provider', required=1,
        default=_default_provider,
        string='Service provider')

    description = fields.Char()
    price = fields.Float()
    active = fields.Boolean(default=True)
    prefer_product_id = fields.Integer()

    @api.model
    def create(self, vals):
        tools.image_resize_images(
            vals, 'avatar', 'avatar_medium', 'avatar_small')
        return super(Services, self).create(vals)

    @api.multi
    def write(self, vals):
        tools.image_resize_images(
            vals, 'avatar', 'avatar_medium', 'avatar_small')
        return super(Services, self).write(vals)


class Free_service(models.Model):
    _name = 'free.service'
    _description = 'Free service'

    def _default_provider(self):
        uid_ = self.env.user.id
        providers = self.env['service.provider'].search([
            ('user_id', '=', uid_)])
        if not providers:
            return
        return providers[0].id

    name = fields.Char(required=True)
    avatar = fields.Binary(attachment=True)
    avatar_medium = fields.Binary(attachment=True,
                                  string='Avatar')
    avatar_small = fields.Binary(attachment=True)
    description = fields.Char()
    active = fields.Boolean(default=True)
    icon = fields.Binary(attachment=True)
    # service_provider_id = fields.Many2one('service.provider', 'Service provider',
    #                                       default=_default_provider, required=True)

    @api.model
    def create(self, vals):
        tools.image_resize_images(
            vals, 'avatar', 'avatar_medium', 'avatar_small')
        return super(Free_service, self).create(vals)

    @api.multi
    def write(self, vals):
        tools.image_resize_images(
            vals, 'avatar', 'avatar_medium', 'avatar_small')
        return super(Free_service, self).write(vals)
