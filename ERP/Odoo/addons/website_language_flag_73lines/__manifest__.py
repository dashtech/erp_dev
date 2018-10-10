# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by 73lines
# See LICENSE file for full copyright and licensing details.

{
    'name': 'Website Language Flag',
    'summary': 'Shows language flag image in website',
    'description': 'Shows language flag image in website',
    'category': 'Website',
    'version': '10.0.1.0.0',
    'author': '73Lines',
    'website': 'https://www.73lines.com/',
    'depends': ['website'],
    'data': [
        'views/assets.xml',
        'views/res_lang_view.xml',
        'views/website_templates.xml',
    ],
    'images': [
        'static/description/website_language_flag.jpg',
    ],
    'installable': True,
    'price': 15,
    'license': 'OEEL-1',
    'currency': 'EUR',
}
