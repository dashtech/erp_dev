# -*- coding: utf-8 -*-
{
    "name": "Bave Import",
    "version": "1.0",
    "author" : 'Bave technology',
    'website' : 'http://bave.io/',
    "external_dependencies": {
        "python": [
            "validate_email",
        ]},
    "depends": [
        'sales_team',
        'product',
        'btek_account',
        'btek_account_asset',
        'car_repair_master_data',
        'car_repair_industry',
    ],
    "category": "Product",
    "data": [
        'security/ir.model.access.csv',
        'views/import_product_category.xml',
        'views/import_product_uom.xml',
        'views/import_customer.xml',
        'views/import_supplier.xml',
        'views/import_product.xml',
        'static/src/xml/css.xml',
        'views/homepage.xml',
        'views/home.xml',
        'views/wizard_import_fail.xml',
    ],
    "css": [
        'static/src/css/purchase.css',
    ],

    'installable': True,
    'application': True,
}
