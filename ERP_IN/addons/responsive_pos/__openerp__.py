# -*- coding: utf-8 -*-

{
    'name': 'Responsive POS Screen',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'author': 'Webveer',
    'summary': 'This module makes POS responsive. So you can use POS on any type  of screen.',
    'description': """

=======================

This module makes POS responsive. So you can use POS on any type  of screen.

""",
    'depends': ['point_of_sale'],
    'data': [
        'views/templates.xml',
        'views/views.xml',
    ],
    'qweb': [
        'static/src/xml/pos.xml',
    ],
    'images': [
        'static/description/port_product.jpg',
    ],
    'installable': True,
    'website': '',
    'auto_install': False,
    'price': 100,
    'currency': 'EUR',
}
