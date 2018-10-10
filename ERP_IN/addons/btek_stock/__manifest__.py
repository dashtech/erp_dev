# -*- coding: utf-8 -*-
{
    "name": "Btek Stock",
    "version": "1.0",
    "author" : 'Bave technology',
    'website' : 'http://bave.io/',
    "depends": [
        'stock', 'stock_account',
    ],
    "category": "Stock",
    "data": [
        # 'security/bave_stock_security.xml',
        'security/ir.model.access.csv',

        'data/check_inventory_data.xml',
        'data/inventory_config.xml',
        'views/inventory_inherit_view.xml',
        'views/inventory_config_view.xml',
        'views/menu_view.xml',
        'views/synthesis_stock_inventory.xml',
        'views/detail_import_export_by_product.xml',
        'views/synthesis_import_export.xml',
        'views/import_stock_inventory_line.xml',
        'data/inventory_warning_template.xml',
    ],

    'installable': True,
    'application': True,
}
