# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by 73lines
# See LICENSE file for full copyright and licensing details.

{
    'name': 'Products Category Carousel Slider',
    'summary': 'Allows to drag & drop product category carousel '
               'slider in website',
    'description': 'Allows to drag & drop product category carousel '
                   'slider in website',
    'category': 'Website',
    'version': '10.0.1.0.0',
    'author': '73Lines',
    'website': 'https://www.73lines.com/',
    'data': [
        'data/filter_data.xml',
        'views/assets.xml',
        'views/product_category_carousel.xml',
    ],
    'depends': ['website_sale', 'carousel_slider_73lines'],
    'images': [
        'static/description/snippet_product_category_carousel.jpg',
    ],
    'installable': True,
    'price': 20,
    'license': 'OEEL-1',
    'currency': 'EUR',
}
