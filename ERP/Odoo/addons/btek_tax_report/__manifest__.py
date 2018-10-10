# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'B Tek Report Tax',
    'version' : '1.0',
    'summary': 'B Tek Report Accounting',
    'sequence': 1,
    'description': """
        B Tek Report Accounting """,
    'category': 'Accounting',
    'depends' : ['account','btek_account_payment', 'report_xlsx'],
    'data': [
        'tax_inout_report.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
