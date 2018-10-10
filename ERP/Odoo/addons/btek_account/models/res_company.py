# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResCompany(models.Model):
    _inherit = 'res.company'

    def open_setup_account_account(self):
        action_obj = \
            self.env.ref(
                'btek_account.wizard_setup_account_account_action')
        action = action_obj.read([])[0]

        return action

class WizardSetupAccount(models.TransientModel):
    _name = 'wizard.setup.account.account'

    from_company_id = fields.Many2one(
        'res.company', 'From company', required=True)
    to_company_id = fields.Many2one(
        'res.company', 'To company', required=True)

    @api.model
    def default_get(self, fields_list):
        res = super(WizardSetupAccount,self).default_get(fields_list)
        active_id = self.env.context.get('active_id', False)
        if active_id:
            res['to_company_id'] = active_id
        return res

    def action_create_account(self, vals, to_company):
        vals['company_id'] = to_company.id

        account_id = self.env['account.account'].create(vals)
        return account_id.id

    def create_account(self, account, to_company, id_dict):
        domain = [('company_id', '=', to_company.id),
             ('code', '=', account['code'])]
        to_company_account_ids = \
            self.env['account.account'].with_context(
            show_parent_account=True).search(domain)

        if to_company_account_ids:
            return to_company_account_ids[0].id

        vals = {
            'name': account['name'],
            'code': account['code'],
            'user_type_id': account['user_type_id'][0],
            'reconcile': account['reconcile'],
            'deprecated': account['deprecated'],
            'company_id': to_company.id,
        }
        parent_id = account['parent_id'] and account['parent_id'][0] or 0
        if not parent_id:
            account_id = self.action_create_account(vals, to_company)
            return account_id

        parent = id_dict.get(parent_id, False)

        if not parent:
            raise UserError(_(
                'Error: parent account {} invalid!'.format(
                    account['code'])))

        vals['parent_id'] = self.create_account(parent, to_company, id_dict)

        account_id = self.action_create_account(vals, to_company)
        return account_id

    @api.multi
    def setup_account_account(self):
        from_company = self[0].from_company_id
        to_company = self[0].to_company_id

        field_list = [
            'name', 'code', 'parent_id', 'user_type_id',
            'reconcile', 'deprecated'
        ]

        account_s = self.env['account.account'].with_context(
            show_parent_account=True).search_read(
            [('company_id', '=', from_company.id)],
            field_list
        )

        # code_dict = dict((a['code'], a) for a in account_s)
        id_dict = dict((a['id'], a) for a in account_s)

        for account in account_s:
            account_id = self.create_account(account, to_company, id_dict)

        return True
