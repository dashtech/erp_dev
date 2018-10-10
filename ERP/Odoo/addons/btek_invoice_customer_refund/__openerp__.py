# -*- coding: utf-8 -*-

{
    'name': 'Invoice Customer Refunds',
    'version': '1.0',
    'category': 'account',
    'summary': """
        """,
    'author': 'Anhtt',
    'description': """ * Change process and method in the functional currency
    """,
    'depends': ['account', 'stock', 'btek_product'],
    'data': [
                'product_view.xml',
                'product_category_view.xml',
                'invoice_customer_refund_view.xml',
            ],
    'css': [],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}
