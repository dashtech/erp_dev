# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'B Tek Booking Management',
    'version': '1.0',
    'summary': 'B Tek Booking',
    'sequence': 1,
    'description': """
        Boooking Management """,
    'category': '',
    'depends': ['base', 'cargo_management', 'vietnam_localization'],

    'data': [

        'views/booking_view.xml',

        'security/ir.model.access.csv',
        'security/groups.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
