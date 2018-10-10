# -*- coding: utf-8 -*-
from odoo import models, fields, api
import datetime

SUPERUSER_ID = 1

class res_company(models.Model):
    _inherit = 'res.company'

    short_name = fields.Char()


    @api.multi
    def open_setup_statement_account(self):
        action_obj = \
            self.env.ref(
                'btek_financial_report.action_setup_btek_financial_statement_account_code')
        action = action_obj.read([])[0]
        return action

class setup_btek_financial_statement_account_code(models.TransientModel):
    _name = 'setup.btek.financial.statement.account.code'

    company_id = fields.Many2one('res.company', 'To company',
                                 required=True)
    from_company_id = fields.Many2one('res.company', 'From company',
                                      required=True, default=1)

    _sql_constraints = [
        ('company_duplicate',
         'check(company_id != from_company_id)',
         'To company must be different from company!'),
    ]

    @api.multi
    def setup(self):
        company_id = self[0].company_id.id
        from_company_id = self[0].from_company_id.id
        created_s = \
            self.env['to.financial.statement.account.code'
            ].search([('company_id','=', company_id)])
        created_s.unlink()

        config_s = self.env['account.financial.report'].search([])
        for config in config_s:
            vals = {}
            # to_included_accounts
            to_included_accounts = []
            for item in config.to_included_accounts:
                if item.company_id.id == from_company_id:
                    to_included_accounts.append(
                        (0, 0, {'name': item.name,
                                'company_id': company_id
                                })
                    )
            if to_included_accounts:
                vals['to_included_accounts'] = to_included_accounts

            # to_excluded_accounts
            to_excluded_accounts = []
            for item in config.to_excluded_accounts:
                if item.company_id.id == from_company_id:
                    to_excluded_accounts.append(
                        (0, 0, {'name': item.name,
                                'company_id': company_id
                                })
                    )
            if to_excluded_accounts:
                vals['to_excluded_accounts'] = to_excluded_accounts

            # to_counterpart_accounts
            to_counterpart_accounts = []
            for item in config.to_counterpart_accounts:
                if item.company_id.id == from_company_id:
                    to_counterpart_accounts.append(
                        (0, 0, {'name': item.name,
                                'company_id': company_id
                                })
                    )
            if to_counterpart_accounts:
                vals['to_counterpart_accounts'] = to_counterpart_accounts

            if vals:
                config.write(vals)

        return True


