# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'B Tek Account Journal',
    'version' : '1.0',
    'summary': 'B Tek Account Journal',
    'sequence': 1,
    'description': """
        B Tek Account Journal  """,
    'category': 'Accounting',
    'depends' : ['account', 'account_voucher', 'btek_account_payment', 'account_cancel', 'btek_product'],
    'data': [
        'views/btek_journal_views.xml',
        'views/btek_account_move_views.xml',
        'views/account_payment.xml',
        'views/account_voucher_inherit.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
