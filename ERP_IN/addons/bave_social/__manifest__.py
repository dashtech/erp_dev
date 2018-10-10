# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Bave social',
    'version': '1.0',
    'summary': 'Bave social',
    'sequence': 1,
    'description': """
        Bave social """,
    'category': '',
    'depends': ['base',
                'web_tree_image',
                'btek_localization',
                'mrp'
    ],

    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',

        'views/social.xml',
        'views/album.xml',
        'views/service_provider.xml',
        'views/customer_feedback.xml',
        'views/booking_view.xml',
        'views/promotions.xml',
        'views/quotation.xml',
        # 'views/mrp_bom_view.xml',
        # 'views/service_view.xml',
        'wizard/wizard_service_package_view.xml',
        'wizard/wizard_service_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
