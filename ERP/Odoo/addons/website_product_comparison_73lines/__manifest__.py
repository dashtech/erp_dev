# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by 73lines
# See LICENSE file for full copyright and licensing details.

{
    'name': 'Website Product Comparison',
    'summary': 'Allows to compare products in website',
    'description': 'Allows to compare products in website',
    'category': 'Website',
    'version': '10.0.1.0.0',
    'author': '73Lines',
    'website': 'https://www.73lines.com/',
    'depends': ['website_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_comparison_template.xml',
        'views/product_comparison_view.xml',
    ],
    'images': [
        'static/description/website_product_compare.jpg',
    ],
    'demo': [
        'data/product_comparison_demo.xml',
    ],
    'installable': True,
    'price': 40,
    'license': 'OEEL-1',
    'currency': 'EUR',
}
