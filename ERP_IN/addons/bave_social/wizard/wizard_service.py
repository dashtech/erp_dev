# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class WizardService(models.TransientModel):
    _name = 'wizard.service'

    product_ids = fields.Many2many('product.product', 'wizard_provider_product_rel',
                                   'provider_id', 'product_id', string="Services")
    res_id = fields.Integer()


    def action_ok(self):
        if not self.product_ids:
            return True
        product_ids = self.product_ids
        services = []
        for pro in product_ids:
            service = {}
            service.update({'name': pro.display_name,
                            'prefer_product_id': pro.id,
                            'service_provider_id': self.res_id})
            services.append(service)

        for service in services:
            val = service
            res_service = self.env['services'].create(val)
            if not res_service:
                continue
        return True

    @api.model
    def create(self, vals):
        vals['res_id'] = self.env.context.get('active_id')
        return super(WizardService, self).create(vals)