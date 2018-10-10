# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'B Tek Stock Move AML Rel',
    'version' : '1.0',
    'summary': 'B Tek Stock Move AML Rel',
    'sequence': 1,
    'description': """
        create relation from stock move to account move line """,
    'category': 'Accounting',
    'depends' : ['stock', 'stock_account'],
    'data': [

    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
