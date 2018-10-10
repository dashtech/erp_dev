# -*- coding: utf-8 -*-
{
    "name": "Bave Basic Module",
    "version": "1.0",
    "author" : 'Bave technology',
    'website' : 'http://bave.io/',
    "depends": [
        'btek_purchase',
        'btek_stock',
        'car_repair_industry',
        'btek_account',
        'account_parent',
        'purchase_requisition',
        'toolz',
    ],
    "category": "Basic",
    "data": [
        'security/basic.xml',
        'security/ir.model.access.csv',
        'views/menu.xml',
        'views/sale.xml',
        'views/stock.xml',
        'views/purchase.xml',
        'views/accounting.xml',
        'views/auto_picking.xml',
        'views/repair.xml',
    ],
    "css": [
    ],

    'installable': True,
    'application': True,
}
