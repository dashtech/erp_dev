# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by 73lines
# See LICENSE file for full copyright and licensing details.

{
    'name': 'Website Product Ribbon',
    'summary': 'Allows to add different ribbon on products',
    'description': 'Allows to add different ribbon on products',
    'category': 'Website',
    'version': '10.0.1.0.0',
    'author': '73Lines',
    'website': 'https://www.73lines.com/',
    'depends': ['website_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/product_ribbon_view.xml',
        'views/templates.xml',
    ],
    'installable': True,
    'price': 20,
    'license': 'OEEL-1',
    'currency': 'EUR',
}
