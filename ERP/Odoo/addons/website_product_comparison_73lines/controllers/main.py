# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by 73lines
# See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleCompare(WebsiteSale):

    @http.route('/shop/compare/', type='http', auth="public", website=True)
    def product_compare(self, **post):
        context = dict(request.context)
        if not context.get('pricelist'):
            context['pricelist'] = int(
                request.website.get_current_pricelist().id)
        from_currency = request.env['res.users'].browse(
            request.uid).company_id.currency_id

        ###########################################
        # Keep lambda function only for reference
        # Already replaced by python closure
        ###########################################
        # compute_currency = lambda price: request.env['res.currency'].\
        #     _compute(from_currency, request.env['product.pricelist'].browse(
        #     context['pricelist']).currency_id, price)
        def compute_currency(price):
            return request.env['res.currency'].\
                _compute(from_currency, request.env['product.pricelist'].
                         browse(context['pricelist']).currency_id, price)

        values = {'compute_currency': compute_currency}
        if post.get('products'):
            product_ids = [int(i) for i in post.get('products').split(',')]
            products = request.env['product.template'].sudo().with_context(
                context).browse(product_ids)
            values['products'] = products

            res = {}
            list_template = [' - ' for i in range(len(products))]
            for num, product in enumerate(products):
                for var in product.sudo().attribute_line_ids:
                    cat_name = var.attribute_id.category_id.name
                    att_name = var.attribute_id.name
                    res.setdefault(cat_name, {})
                    if not res[cat_name].get(att_name):
                        # copy by value
                        res[cat_name][att_name] = list_template[:]

                    res[cat_name][att_name][num] = ' or '.join(
                        var.value_ids.mapped('name'))
            values['specs'] = res
        return request.render(
            "website_product_comparison_73lines.product_compare", values)

    @http.route(['/shop/get_product_data'], type='json',
                auth="public", website=True)
    def get_product_data(self, product_ids):
        context = dict(request.context)
        if not context.get('pricelist'):
            context['pricelist'] = int(
                request.website.get_current_pricelist().id)
        values = request.env['product.template'].sudo().with_context(context)\
            .browse(product_ids).read(['product_variant_ids', 'name',
                                       'lst_price', 'price',
                                       'public_categ_ids'])
        product_currency = request.env['product.pricelist'].browse(
            context['pricelist']).currency_id.symbol
        for value in values:
            value['product_currency'] = product_currency
        return values

    @http.route(['/shop/check_product_attributes'], type='json',
                auth="public", website=True)
    def check_product_attributes(self, template):
        return request.env.ref(template).active
