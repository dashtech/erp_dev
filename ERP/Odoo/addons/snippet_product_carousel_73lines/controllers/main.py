# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by 73lines
# See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request
from odoo.addons.carousel_slider_73lines.controllers.main import \
    SnippetObjectCarousel
from odoo.addons.website_sale.controllers.main import WebsiteSale


class SnippetProductCarousel(SnippetObjectCarousel):

    def get_rating_stat(self, product, context=None):
        rating_product = product.rating_get_stats(
            [('website_published', '=', True)])
        return rating_product

    @http.route()
    def render_object_carousel(self, template=False, filter_id=False,
                               objects_in_slide=False, limit=False,
                               object_name=False, in_row=1):
        new_context = dict(request.env.context)
        if not new_context.get('pricelist'):
            pricelist = request.website.get_current_pricelist()
            new_context['pricelist'] = pricelist.id
        else:
            pricelist = request.env['product.pricelist'].browse(
                new_context['pricelist'])

        from_currency = request.env.user.company_id.currency_id
        to_currency = pricelist.currency_id

        ###########################################
        # Keep lambda function only for reference
        # Already replaced by python closure
        ###########################################
        # compute_currency = lambda price: from_currency.compute(price,
        #                                                        to_currency)
        def compute_currency(price):
            return from_currency.compute(price, to_currency)

        new_context['compute_currency'] = compute_currency
        new_context['pricelist'] = pricelist.id
        new_context['get_rating_stat'] = self.get_rating_stat

        request.env.context = new_context
        res = super(SnippetProductCarousel, self).render_object_carousel(
            template=template, filter_id=filter_id,
            objects_in_slide=objects_in_slide, limit=limit,
            object_name=object_name, in_row=in_row)
        return res


class WebsiteSaleProductCarousel(WebsiteSale):

    @http.route(['/shop/cart/update_continue'], type='http', auth="public",
                methods=['POST'], website=True)
    def cart_update_continue(self, product_id, add_qty=1, set_qty=0, **kw):
        request.website.sale_get_order(force_create=1)._cart_update(
            product_id=int(product_id), add_qty=float(add_qty),
            set_qty=float(set_qty))
        return request.redirect(request.httprequest.referrer)
