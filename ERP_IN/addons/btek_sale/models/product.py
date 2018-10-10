# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _

class Product(models.Model):
    _inherit = 'product.template'

    @api.multi
    def _compute_consignment_available(self):
        for product in self:
            product.consignment_available = True

    @api.model
    def _search_consignment_available(self, operator, value):
        company_id = self.env.user.company_id.id
        consignment_location_s = \
            self.env['stock.location'].search(
                [('consignment', '=', True),
                 ('company_id', '=', company_id)])

        if not consignment_location_s:
            return []

        consignment_location = consignment_location_s[0]

        quants = self.env['stock.quant'].search(
            [('location_id', '=', consignment_location.id)]
        )

        product_dict = {}
        for quant in quants:
            if not product_dict.get(quant.product_id.product_tmpl_id.id, False):
                product_dict[quant.product_id.product_tmpl_id.id] = 0

            product_dict[quant.product_id.product_tmpl_id.id] += quant.qty

        product_ids = []
        for product_id in product_dict.keys():
            if product_dict[product_id] > 0:
                product_ids.append(product_id)

        o = 'not in'
        if value:
            o = 'in'

        field = 'id'

        domain = [(field, o, product_ids)]
        return domain

    consignment_available = fields.Boolean(
        compute='_compute_consignment_available',
        search='_search_consignment_available')
