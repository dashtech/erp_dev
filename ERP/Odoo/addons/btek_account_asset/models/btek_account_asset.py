#!/usr/bin/python
# -*- encoding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF


class btek_account_asset(models.Model):
    _inherit = "account.asset.asset"

    year_of_manufacture = fields.Date(string='Năm sản xuất')
    day_of_purchase = fields.Date(string='Ngày mua')
    country_of_manufacture = fields.Many2one('res.country', string='Nước sản xuất')
    accessary_asset_ids = fields.One2many('btek.accessary.asset', 'asset_id')
    note = fields.Text(string=_('Ghi chú'))

    @api.multi
    def set_to_close(self):
        move_ids = []
        for asset in self:
            unposted_depreciation_line_ids = asset.depreciation_line_ids.filtered(lambda x: not x.move_check)
            if unposted_depreciation_line_ids:
                old_values = {
                    'method_end': asset.method_end,
                    'method_number': asset.method_number,
                }

                # Remove all unposted depr. lines
                commands = [(2, line_id.id, False) for line_id in unposted_depreciation_line_ids]

                # Create a new depr. line with the residual amount and post it
                sequence = len(asset.depreciation_line_ids) - len(unposted_depreciation_line_ids) + 1
                today = datetime.today().strftime(DF)
                vals = {
                    'amount': asset.value_residual,
                    'asset_id': asset.id,
                    'sequence': sequence,
                    'name': (asset.code or '') + '/' + str(sequence),
                    'remaining_value': 0,
                    'depreciated_value': asset.value - asset.salvage_value,  # the asset is completely depreciated
                    'depreciation_date': today,
                    'dispose_flag': True,
                }
                commands.append((0, False, vals))
                asset.write({'depreciation_line_ids': commands, 'method_end': today, 'method_number': sequence})
                tracked_fields = self.env['account.asset.asset'].fields_get(['method_number', 'method_end'])
                changes, tracking_value_ids = asset._message_track(tracked_fields, old_values)
                if changes:
                    asset.message_post(subject=_('Asset sold or disposed. Accounting entry awaiting for validation.'),
                                       tracking_value_ids=tracking_value_ids)
                move_ids += asset.depreciation_line_ids[-1].create_move(post_move=False)
        if move_ids:
            name = _('Disposal Move')
            view_mode = 'form'
            if len(move_ids) > 1:
                name = _('Disposal Moves')
                view_mode = 'tree,form'
            return {
                'name': name,
                'view_type': 'form',
                'view_mode': view_mode,
                'res_model': 'account.move',
                'type': 'ir.actions.act_window',
                'target': 'current',
                'res_id': move_ids[0],
            }


class btek_account_asset_category(models.Model):
    _inherit = "account.asset.category"

    prorata = fields.Boolean(string='Prorata Temporis', default=True,
                             help="Indicates that the first depreciation entry for this asset "
                                  "has to be done from the depreciation start date instead of "
                                  "the first day of the fiscal year.")
    _sql_constraints = [
        ('name_uniq', 'unique(name)',
         'Name of group asset must be unique!'),
    ]

    @api.multi
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {}, name=_('%s (copy)') % self.name)
        return super(btek_account_asset_category, self).copy(default)


class btek_account_asset_depreciation_line(models.Model):
    _inherit = "account.asset.depreciation.line"

    dispose_flag = fields.Boolean(string="Dispose flag", default=False)

