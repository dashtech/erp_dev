# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'B Tek LEGAL FINANCIAL',
    'version' : '1.0',
    'summary': 'B Tek LEGAL FINANCIAL',
    'sequence': 1,
    'description': """
    Xác định kết quả hoạt động kinh doanh
        B Tek LEGAL FINANCIAL """,
    'category': 'Accounting',
    'depends' : ['account', 'account_analytic_required'],
    'data': [
        'security/ir.model.access.csv',

        'views/config_entry.xml',
        'views/data_entry.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
