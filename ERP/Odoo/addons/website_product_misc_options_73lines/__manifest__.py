# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by 73lines
# See LICENSE file for full copyright and licensing details.

{
    'name': 'Website Product Miscellaneous Options',
    'summary': 'MISC Options like... Tags, Brands, View Limit, '
               'View Switcher, Sorting, Price Filter',
    'description': 'MISC Options like... Tags, Brands, View Limit, '
                   'View Switcher, Sorting, Price Filter',
    'category': 'Website',
    'version': '10.0.1.0.0',
    'author': '73Lines',
    'website': 'https://www.73lines.com/',
    'depends': ['website_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_limit_data.xml',
        'views/assets.xml',
        'views/templates.xml',
        'views/product_limit_view.xml',
        'views/product_views.xml',
    ],
    'installable': True,
    'price': 50,
    'license': 'OEEL-1',
    'currency': 'EUR',
}
