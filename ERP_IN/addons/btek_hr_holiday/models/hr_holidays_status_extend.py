# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class HrHolidayStatusExtend(models.Model):
    _inherit = 'hr.holidays.status'
    _rec_name = 'desc'

    name = fields.Char('Code', required=True, translate=True)
    desc = fields.Char('Leave Type', required=True, translate=True)

    @api.multi
    def name_get(self):
        if not self._context.get('employee_id'):
            # leave counts is based on employee_id, would be inaccurate if not based on correct employee
            return super(HrHolidayStatusExtend, self).name_get()
        # res = super(HrHolidayStatusExtend, self).name_get()
        res2 = []
        for record in self:
            name = record.desc or record.name
            if not record.limit:
                name = "%(name)s (%(count)s)" % {
                    'name': name,
                    'count': _('%g remaining out of %g') % (record.virtual_remaining_leaves or 0.0, record.max_leaves or 0.0)
                }
            res2.append((record.id, name))
        return res2