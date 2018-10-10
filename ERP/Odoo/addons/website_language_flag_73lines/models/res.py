# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by 73lines
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools
from odoo.http import request


class ResLang(models.Model):
    _inherit = 'res.lang'

    lang_flag = fields.Binary(string='Language Flag')


class Website(models.Model):
    _inherit = 'website'

    @tools.cache('self.id')
    def _get_languages(self):
        return [(lg.code, lg.name, lg.direction) for lg in self.language_ids]

    @api.multi
    def get_alternate_languages(self, req=None):
        langs = []
        if req is None:
            req = request.httprequest
        default = self.get_current_website().default_lang_code
        shorts = []

        def get_url_localized(router, lang):
            arguments = dict(request.endpoint_arguments)
            for key, val in arguments.items():
                if isinstance(val, models.BaseModel):
                    arguments[key] = val.with_context(lang=lang)
            return router.build(request.endpoint, arguments)

        router = request.httprequest.app.get_db_router(request.db).bind('')
        for code, dummy, direction in self.get_languages():
            lg_path = ('/' + code) if code != default else ''
            lg_codes = code.split('_')
            shorts.append(lg_codes[0])
            uri = get_url_localized(router, code) if request.endpoint \
                else request.httprequest.path
            if req.query_string:
                uri += '?' + req.query_string
            lang = {
                'hreflang': ('-'.join(lg_codes)).lower(),
                'short': lg_codes[0],
                'href': req.url_root[0:-1] + lg_path + uri,
            }
            langs.append(lang)
        for lang in langs:
            if shorts.count(lang['short']) == 1:
                lang['hreflang'] = lang['short']
        return langs


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def get_nearest_lang(cls, lang):
        # Try to find a similar lang. Eg: fr_BE and fr_FR
        short = lang.partition('_')[0]
        short_match = False
        for code, dummy, direction in request.website.get_languages():
            if code == lang:
                return lang
            if not short_match and code.startswith(short):
                short_match = code
        return short_match
