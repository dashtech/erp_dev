{
    "name": "Bave store",
    "version": "1.0",
    "author" : 'Bave technology',
    'website' : 'http://bave.io/',
    "depends": [
        'base',
        'website',
        'btek_purchase',
    ],
    "category": "Website",
    "data": [
        'views/website_shop.xml',
        'views/purchase.xml',
    ],
    'css': [
        'bave_store/static/src/css/style.css',
    ],
    'js': [
        'bave_store/static/src/js/shop.js',
    ],
    'installable': True,
    'application': True,
}
