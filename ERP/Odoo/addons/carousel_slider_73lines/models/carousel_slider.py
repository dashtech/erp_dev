# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by 73lines
# See LICENSE file for full copyright and licensing details.

from odoo import models, _
from odoo.tools.safe_eval import safe_eval


class CarouselSlider(models.AbstractModel):
    _name = 'carousel.slider'

    def eval_filter_data(self, filter_id):
        if self.env.context is None:
            self.env.context = {}
        res = {'domain': [], 'model': self._name}
        # res = {'domain': [], 'model': self._name, 'order': False}
        if filter_id:
            filter_data = self.env['ir.filters'].sudo().browse(filter_id)
            localdict = {'uid': self.env.uid}
            res['domain'] = safe_eval(filter_data.domain, localdict)
            res['model'] = filter_data.model_id
            res['name'] = filter_data.name
        return res

    def get_objects_for_carousel(self, filter_id, limit):
        filter_data = self.eval_filter_data(filter_id)
        model_obj = self.env[filter_data['model']]
        if filter_data:
            object_ids = model_obj.sudo().search(filter_data['domain'],
                                                 limit=limit)
            return {'objects': object_ids,
                    'name': 'name' in filter_data and
                            filter_data['name'] or _("All")}
