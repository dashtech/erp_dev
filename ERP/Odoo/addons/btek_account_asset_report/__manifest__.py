# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'B Tek Account Asset Report',
    'version' : '1.0',
    'summary': 'B Tek Account Asset Report',
    'sequence': 1,
    'description': """
        B Tek Account Asset Report""",
    'category': 'Account Asset',
    'depends': ['account_asset', 'account'],
    'data': ['security/ir.model.access.csv',
             'views/btek_asset_report.xml',
             ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
