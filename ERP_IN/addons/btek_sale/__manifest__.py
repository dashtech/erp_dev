# -*- coding: utf-8 -*-
{
    "name": "Btek Sale",
    "version": "1.0",
    "author" : 'Bave technology',
    'website' : 'http://bave.io/',
    "depends": [
        'crm',
        'sale',
        'purchase',
    ],
    "category": "Sale",
    "data": [
        'security/sale.xml',

        'views/sale.xml',
        'views/purchase.xml',
        'views/stock.xml',
        'views/product.xml',
        # 'views/product_category.xml',
    ],

    'installable': True,
    'application': True,
}
