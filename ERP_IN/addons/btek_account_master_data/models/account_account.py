# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _


class AccountAccount(models.Model):
    _inherit = "account.account"

    def init(self):
        # 3331, 3338, 3431, 4111 change type to view
        account_ids = []
        extend_account_list = [
            'l10n_vn.1_chart3331',
            'l10n_vn.1_chart3338',
            'l10n_vn.1_chart3431',
            'l10n_vn.1_chart4111'
        ]
        for extend_account_id in extend_account_list:
            account = self.env.ref(extend_account_id)
            if account:
                account_ids.append(account.id)
        if account_ids:
            user_type_id = self.env.ref('account_parent.data_account_type_view').id
            account_obj = self.env['account.account'].browse(account_ids)
            account_obj.write({'user_type_id': user_type_id})

        # 1111, 1121 set parent
        account_1111s = self.env['account.account'].search([('code', '=', '1111')])
        if account_1111s:
            account_1111 = account_1111s[0]
            try:
                account_111 = self.env.ref(
                    'btek_account_master_data.btek_account_111').id
                account_1111.write({'parent_id': account_111})
            except:
                pass

        account_1121s = self.env['account.account'].search(
            [('code', '=', '1121')])
        if account_1121s:
            account_1121 = account_1121s[0]
            try:
                account_112 = self.env.ref(
                    'btek_account_master_data.btek_account_112').id
                account_1121.write({'parent_id': account_112})
            except:
                pass

        return True
