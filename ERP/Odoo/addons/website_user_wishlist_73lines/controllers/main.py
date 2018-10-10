# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by 73lines
# See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request
from odoo.addons.website_portal_sale.controllers.main import website_account


class WebsiteUserWishList(http.Controller):

    @http.route('/profile/add_to_wishlist', type='json',
                auth='user', website=True)
    def add_wishlist_json(self, product_id):
        dic_wishlist = {}
        if product_id:
            dic_wishlist = {
                'product_template_id': int(product_id),
                'user_id': request.uid,
            }
        request.env['user.wishlist'].create(dic_wishlist)
        return True


class WebsiteAccountWishList(website_account):

    @http.route()
    def account(self, **kw):
        response = super(WebsiteAccountWishList, self).account(**kw)
        wishlist_count = request.env['user.wishlist'].search_count([
            ('user_id', '=', request.env.user.id)
        ])
        response.qcontext.update({
            'wishlist_count': wishlist_count,
        })
        return response

    @http.route(['/my/wish-list', '/my/wish-list/page/<int:page>'],
                type='http', auth="user", website=True)
    def portal_my_wishlist(self, page=1, date_begin=None, date_end=None, **kw):
        values = self._prepare_portal_layout_values()
        WishList = request.env['user.wishlist']

        # count for pager
        wish_list_count = WishList.search_count(
            [('user_id', '=', request.env.user.id)])
        # make pager
        pager = request.website.pager(
            url="/my/wish-list",
            total=wish_list_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        wish_list = WishList.search([('user_id', '=', request.env.user.id)],
                                    limit=self._items_per_page,
                                    offset=pager['offset'])

        values.update({
            'wish_list': wish_list,
            'pager': pager,
            'default_url': '/my/wish-list',
        })

        return request.render(
            "website_user_wishlist_73lines.portal_my_wishlist", values)
