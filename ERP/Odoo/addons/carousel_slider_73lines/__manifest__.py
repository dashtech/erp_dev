# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by 73lines
# See LICENSE file for full copyright and licensing details.

{
    'name': 'Carousel Slider',
    'summary': 'Carousel Slider is base module used in other '
               '`snippet_*_carousel_73lines` modules that are '
               'developed by 73lines',
    'description': 'Carousel Slider is base module used in other '
                   '`snippet_*_carousel_73lines` modules that are '
                   'developed by 73lines',
    'category': 'Website',
    'version': '10.0.1.0.0',
    'author': '73Lines',
    'website': 'https://www.73lines.com/',
    'data': [
        'views/assets.xml',
        'views/carousel_snippet_options.xml',
    ],
    'depends': ['website'],
    'images': [
        'static/description/snippet_object_carousel.jpg'
    ],
    'installable': True,
    'price': 50,
    'license': 'OEEL-1',
    'currency': 'EUR',
}
