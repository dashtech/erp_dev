# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by 73lines
# See LICENSE file for full copyright and licensing details.

{
    'name': 'Product Brand Carousel Slider',
    'summary': 'Allows to drag & drop brand carousel slider in website',
    'description': 'Allows to drag & drop brand carousel slider in website',
    'category': 'Website',
    'version': '10.0.1.0.0',
    'author': '73Lines',
    'website': 'https://www.73lines.com/',
    'depends': [
        'carousel_slider_73lines',
        'website_product_misc_options_73lines'
    ],
    'data': [
        'views/assets.xml',
        'views/brand_carousel.xml',
    ],
    'images': [
        'static/description/snippet_brand_carousel.jpg',
    ],
    'installable': True,
    'price': 20,
    'license': 'OEEL-1',
    'currency': 'EUR',
}
