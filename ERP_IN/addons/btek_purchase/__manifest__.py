# -*- coding: utf-8 -*-
{
    "name": "Btek Purchase",
    "version": "1.0",
    "author" : 'Bave technology',
    'website' : 'http://bave.io/',
    "depends": [
        'purchase', 'toolz', 'car_repair_industry',
    ],
    "category": "Purchase",
    "data": [
        'report/purchase_quotation.xml',
        'report/purchase_oder_report.xml',
        'data/mail_template_data.xml',
        'views/purchase.xml',
        'static/src/xml/css.xml',
    ],
    "css": [
        'static/src/css/purchase.css',
    ],

    'installable': True,
    'application': True,
}
