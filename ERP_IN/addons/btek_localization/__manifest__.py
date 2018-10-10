# -*- coding: utf-8 -*-
{
    'name': 'BTek Localization',
    'version': '10.0.1.0.0',
    'author': 'Bave technology',
    'summary': 'BTek localization',
    'sequence': 30,
    'category': 'BTek Module',
    'website': 'http://bave.io/',
    'images': [],
    'depends': ['base', 'sales_team'],
    'data': [
        'views/localization_view.xml',
        'views/res_partner_view.xml',
        'data/localization_data.xml',
    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
