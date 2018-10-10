# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'B Tek Financial Report',
    'version' : '1.0',
    'summary': 'B Tek Financial Report',
    'sequence': 1,
    'description': """
        B Tek Financial Report""",
    'category': 'Accounting',
    'depends' : ['account', 'report_xlsx'],
    'data': [
            'security/ir.model.access.csv',
            'security/to_financial_statement_account_code_security.xml',
            'data/data.xml',
            'data/balance_sheet_200_config.xml',
            'data/income_statement_200_config.xml',
            'data/cash_flow_200_config.xml',
            'views/financial_config_views.xml',
            'views/is_report_view.xml',
            'views/bs_report_view.xml',
            'views/cf_report_view.xml',
            'views/res_company.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
