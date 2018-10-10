# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by 73lines
# See LICENSE file for full copyright and licensing details.


from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteProductQuick(WebsiteSale):

    def get_attribute_value_ids(self, product):
        """ list of selectable attributes of a product

        :return: list of product variant description
           (variant id, [visible attribute ids], variant price,
           variant sale price)
        """
        # product attributes with at least two choices
        product = product.with_context(quantity=1)

        visible_attrs_ids = product.attribute_line_ids.filtered(
            lambda l: len(l.value_ids) > 1).mapped('attribute_id').ids
        to_currency = request.website.get_current_pricelist().currency_id
        attribute_value_ids = []
        for variant in product.product_variant_ids:
            if to_currency != product.currency_id:
                price = variant.currency_id.compute(
                    variant.website_public_price, to_currency)
            else:
                price = variant.website_public_price
            visible_attribute_ids = [v.id for v in variant.attribute_value_ids
                                     if v.attribute_id.id in visible_attrs_ids]
            attribute_value_ids.append([variant.id, visible_attribute_ids,
                                        variant.website_price, price])
        return attribute_value_ids

    @http.route()
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        res = super(WebsiteProductQuick, self).shop(page=page,
                                                    category=category,
                                                    search=search, ppg=ppg,
                                                    **post)
        res.qcontext.update({
            'get_attribute_value_ids': self.get_attribute_value_ids,
        })
        return res
