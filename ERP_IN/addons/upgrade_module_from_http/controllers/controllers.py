# -*- coding: utf-8 -*-

import json
import odoo.http as http


class upgrade_module(http.Controller):
    @http.route('/upgrade_module/<string:module_name>/<string:username>/',
                auth='public', website=True, csrf=False)
    def upgrade(self, module_name, username, **kwargs):
        pwd = kwargs.get('password', '')
        db = http.request.db
        user_id = http.request.env['res.users']._login(db, username, pwd)
        res = {}
        if not user_id:
            res['result'] = False
            res['message'] = 'Login fail'
            return json.dumps(res)
        try:
            module = http.request.env['ir.module.module'].sudo(user_id).search([('name', '=', module_name)])
            upgrade = module.button_immediate_upgrade()
        except Exception as e:
            res['result'] = False
            res['message'] = unicode(e)
            return json.dumps(res)
        res['result'] = True
        res['message'] = 'Upgrade module success'
        return json.dumps(res)