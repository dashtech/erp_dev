# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import re
import urllib2
import werkzeug.utils
import werkzeug.wrappers

import odoo
from odoo import http
from odoo import fields
from odoo.http import request
from odoo.addons.web.controllers.main import WebClient, Binary, Home
from odoo.addons.website.controllers.main import Website

logger = logging.getLogger(__name__)


class BaveWebsite(Website):

    @http.route('/', type='http', auth="public", website=True)
    def index(self, **kw):
        res = super(BaveWebsite, self).index(**kw)
        # ensure_db()
        if not request.session.uid:
            return werkzeug.utils.redirect('/web/login', 303)
        if kw.get('redirect'):
            return werkzeug.utils.redirect(kw.get('redirect'), 303)

        request.uid = request.session.uid
        context = request.env['ir.http'].webclient_rendering_context()

        return request.render('web.webclient_bootstrap', qcontext=context)
        # page = 'homepage'
        # main_menu = request.website.menu_id or request.env.ref('website.main_menu', raise_if_not_found=False)
        # if main_menu:
        #     first_menu = main_menu.child_id and main_menu.child_id[0]
        #     if first_menu:
        #         if first_menu.url and (not (first_menu.url.startswith(('/page/', '/?', '/#')) or (first_menu.url == '/'))):
        #             return request.redirect(first_menu.url)
        #         if first_menu.url and first_menu.url.startswith('/page/'):
        #             return request.env['ir.http'].reroute(first_menu.url)
        # return self.page(page)