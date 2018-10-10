# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by 73lines
# See LICENSE file for full copyright and licensing details.

import json

from odoo import http
from odoo.http import request
from odoo.addons.carousel_slider_73lines.controllers.main import \
    SnippetObjectCarousel


class SnippetBlogCarousel(SnippetObjectCarousel):

    def get_property_value(self, blog):
        res = json.loads(blog.cover_properties)
        return res

    @http.route()
    def render_object_carousel(self, template=False, filter_id=False,
                               objects_in_slide=False, limit=False,
                               object_name=False, in_row=1):
        new_context = dict(request.env.context)
        new_context['get_property_value'] = self.get_property_value
        request.env.context = new_context
        res = super(SnippetBlogCarousel, self).render_object_carousel(
            template=template, filter_id=filter_id,
            objects_in_slide=objects_in_slide, limit=limit,
            object_name=object_name, in_row=in_row)
        return res
