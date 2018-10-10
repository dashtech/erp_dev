# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class WizardServicePackage(models.TransientModel):
    _name = 'wizard.service.package'

    mrp_bom_ids = fields.Many2many('mrp.bom', 'wizard_provider_mrp_bom_rel', 'provider_id', 'bom_id',
                                   string="Service Package")
    res_id = fields.Integer()

    @api.multi
    def write(self, vals):
        return True

    def action_ok(self):
        if not self.mrp_bom_ids:
            return True
        pack_ids = self.mrp_bom_ids
        packs = []
        services = []
        for pack_id in pack_ids:
            pack = {}
            if not pack_id.bom_line_ids:
                service = {}
            else:
                for bom in pack_id.bom_line_ids:
                    service = {}
                    service.update({'name': bom.display_name,
                                    'prefer_product_id': bom.product_id.id,
                                    'price': bom.product_id.lst_price,
                                    'service_provider_id': self.res_id})
                    services.append({pack_id.id: service})
            pack.update({
                'name': pack_id.display_name,
                'prefer_bom_id': pack_id.id,
                'price': pack_id.product_tmpl_id.list_price,
                'service_provider_id': self.res_id,})
            packs.append(pack)

        for pack in packs:
            services_ = []
            for service in services:
                val = service.values()[0]
                res_service = self.env['services'].create(val)
                if not res_service:
                    continue
                if pack['prefer_bom_id'] in service.keys():
                    services_.append(res_service.id)
            if services_:
                pack['service_ids'] = [(6, 0, services_)]
            res_pack = self.env['service.package'].create(pack)

        # for service in services:
        #     val = service.values()[0]
        #     res_service = self.env['services'].create(val)
        #     if not res_service:
        #         continue
        #     for pack in packs:
        #         if pack['prefer_bom_id'] in service.keys():
        #             pack['service_ids'] = [(6, 0, [res_service.id])]
        #             res_pack = self.env['service.package'].create(pack)
        #
        # return True

    @api.model
    def create(self, vals):
        vals['res_id'] = self.env.context.get('active_id')
        return super(WizardServicePackage, self).create(vals)