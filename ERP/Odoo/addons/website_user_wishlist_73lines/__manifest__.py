# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by 73lines
# See LICENSE file for full copyright and licensing details.

{
    'name': 'Website User WishList',
    'summary': 'Allows users to add their favorite products in wish list',
    'description': 'Allows users to add their favorite products in wish list',
    'category': 'Website',
    'version': '10.0.1.0.0',
    'author': '73Lines',
    'website': 'https://www.73lines.com/',
    'depends': ['website_sale', 'website_portal_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/website_user_wishlist_view.xml',
        'views/website_user_wishlist_template.xml',
        'views/website_portal_sale_templates.xml',
    ],
    'images': [
        'static/description/website_user_wishlist.jpg',
    ],
    'installable': True,
    'price': 25,
    'license': 'OEEL-1',
    'currency': 'EUR',
}
