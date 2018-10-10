# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'B Tek Marketing',
    'version': '1.0',
    'summary': 'B Tek Marketing',
    'sequence': 1,
    'description': """
        B Tek Marketing """,
    'category': '',
    'depends': ['base', 'mass_mailing',
                'btek_localization',
                'web_widget_domain_v11', 'web',
                'car_repair_industry'],
    "external_dependencies": {
        "python": [
            "unidecode",
        ],
    },
    'data': [
        'data/ir_sequence_data.xml',
        'data/multi_message_data.xml',
        'data/zalo_config.xml',
        'security/ir.model.access.csv',
        'views/btek_res_partner_view.xml',
        'views/btek_mass_mailing_view.xml',
        'views/btek_partner_source_view.xml',
        'views/btek_auto_condition_view.xml',
        'views/btek_function_view.xml',
        'views/btek_multi_message_config_view.xml',
        'views/btek_multi_message_view.xml',
        'views/btek_contact_view.xml',
        'views/btek_auto_send_mail_view.xml',
        'views/btek_auto_send_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
