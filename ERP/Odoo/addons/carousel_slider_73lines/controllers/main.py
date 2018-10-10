# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by 73lines
# See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request


def chunks(l, n):
    for i in xrange(0, len(l), n):
        yield l[i:i+n]


class SnippetObjectCarousel(http.Controller):

    def split_objects(self, in_row, objects):
        res = list(chunks(objects, in_row))
        return res

    @http.route(['/carousel_slider/render/<object_name>'], type='json',
                auth='public', website=True, csrf=False, cache=300)
    def render_object_carousel(self, template=False, filter_id=False,
                               objects_in_slide=False, limit=False,
                               object_name=False, in_row=1):
        res = request.env[object_name].get_objects_for_carousel(
            filter_id=filter_id, limit=limit)
        values = {
            'objects': self.split_objects(in_row, res['objects']),
            'title': res['name'],
        }
        return request.env['ir.ui.view'].render_template(template, values)
