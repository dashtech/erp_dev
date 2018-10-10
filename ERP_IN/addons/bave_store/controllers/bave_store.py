# -*- coding: utf-8 -*-
import datetime
from odoo import http
from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.tools.translate import _
import json
from operator import itemgetter


class BaveStore(http.Controller):
    @http.route(
        ['/bave-store-main'],
        auth='user', website=True)
    def bavestore(self, **kw):
        datas = {
            'uid': http.request.env.user.id,
            'url': http.request.env['ir.config_parameter'].get_param('web.base.url') or '',
            'login': http.request.env.user.login,
            'token': http.request.env.user.generate_token(),
            'and_char': '&',
        }

        return http.request.render(
            'bave_store.bave_store_main',
            datas)

class BaveStoreCreatePO(http.Controller):
    @http.route(
        ['/create-bave-store-purchase-order'],
        auth='public', type='http',
        website=True, csrf=False, methods=['POST'])
    def create_bave_store_purchase_order(self, **post_data):
        # print '------------------'
        # print post_data

        login = post_data.get('login', False)
        token = post_data.get('token', False)
        detail = post_data.get('detail', False)

        user = \
            http.request.env['res.users'
            ].sudo().check_bave_store_authencation(login, token)
        if not user:
            res = {
                "result": "NOT OK",
                "message": "Fail authencation",
            }
            res = json.dumps(res)
            return res

        try:
            detail = json.loads(detail)
        except:
            res = {
                "result": "NOT OK",
                "message": "purchase order detail invalid",
            }
            res = json.dumps(res)
            return res

        return_data = http.request.env['purchase.order'
        ].sudo(user.id).create_bave_store_purchase_order(detail)
        return json.dumps(return_data)
