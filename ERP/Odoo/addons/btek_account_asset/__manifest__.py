# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'B Tek Account Asset',
    'version' : '1.0',
    'summary': 'B Tek Account Asset',
    'sequence': 1,
    'description': """
        B Tek Account Asset  """,
    'category': 'Accounting',
    'depends' : ['account_asset', 'btek_account'],
    'data': [
        'views/btek_account_asset_views.xml',
        'security/ir.model.access.csv',
        'views/import_account_asset_categ.xml',
        'views/import_account_asset_asset.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
