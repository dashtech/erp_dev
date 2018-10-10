# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class BtekAccountAnalyticLine(models.Model):
    _name = 'btek.account.analytic.line'
    _description = 'Analytic Line'
    _order = 'date desc, id desc'

    # @api.model
    # def _default_user(self):
    #     return self.env.context.get('user_id', self.env.user.id)

    name = fields.Char('Description', required=True)
    date = fields.Date('Date', required=True, index=True, default=fields.Date.context_today)
    unit_amount = fields.Float('Quantity', default=0.0)
    user_id = fields.Many2one('res.users', string='User')

    employee_id = fields.Many2one('hr.employee', 'Employee')

    day_id_computed = fields.Many2one('hr.working.day', string='Sheet', compute='_wk_day_compute_sheet',
                                      index=True, ondelete='cascade', search='_w_search_sheet')
    day_id = fields.Many2one('hr.working.day', compute='_wk_day_compute_sheet', string='Sheet', store=True)

    @api.depends('date', 'employee_id', 'day_id_computed.date_to', 'day_id_computed.date_from')
    def _wk_day_compute_sheet(self):
        """Links the timesheet line to the corresponding sheet
        """
        for ts_line in self:
            if not ts_line.employee_id:
                continue
            sheets = self.env['hr.working.day'].search(
                [('date_to', '>=', ts_line.date), ('date_from', '<=', ts_line.date),
                 ('state', 'in', ['draft'])])
            if sheets:
                ts_line.day_id_computed = sheets[0]
                ts_line.day_id = sheets[0]

    def _w_search_sheet(self, operator, value):
        assert operator == 'in'
        ids = []
        for ts in self.env['hr.working.day'].browse(value):
            self._cr.execute("""
                        SELECT l.id
                            FROM btek_account_analytic_line l
                        WHERE %(date_from)s >= l.date
                            AND %(date_to)s <= l.date
                        GROUP BY l.id""", {'date_from': ts.date_from,
                                           'date_to': ts.date_to})
            ids.extend([row[0] for row in self._cr.fetchall()])
        return [('id', 'in', ids)]

    @api.multi
    def write(self, values):
        self._check_state()
        return super(BtekAccountAnalyticLine, self).write(values)

    @api.multi
    def unlink(self):
        self._check_state()
        return super(BtekAccountAnalyticLine, self).unlink()

    def _check_state(self):
        for line in self:
            if line.day_id and line.day_id.state not in 'draft':
                raise UserError(_('You cannot modify an entry in a confirmed timesheet.'))
        return True

