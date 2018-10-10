{
    "name": "Btek product",
    "version": "1.0",
    "author" : 'Bave technology',
    'website' : 'http://bave.io/',
    "depends": [
        'base',
        'product',
        'purchase',
        'product_expiry',
        'stock_account',
    ],
    "category": "Report",
    "data": [
        'views/product_view.xml',
        'views/product_origin_view.xml',
        'security/ir.model.access.csv',
    ],
    'css': [
    ],
    'installable': True,
    'application': True,
}
