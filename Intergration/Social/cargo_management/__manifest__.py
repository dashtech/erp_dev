{
    "name": "Cargo management",
    "version": "1.0",
    "author" : 'Bave technology',
    'website' : 'http://bave.io/',
    "depends": [
        'base',
        'vietnam_localization',
        'web_tree_image',
    ],
    "category": "Cargo",
    "data": [
        'views/services.xml',
        'views/album.xml',
        'views/service_provider.xml',
        'views/promotions.xml',
        'views/member.xml',
        'views/vehicle.xml',
        'views/quotation.xml',
        'views/customer_feedback.xml',

        'data/promotions_data.xml',
        'data/request_quotation_data.xml',

        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/customer_feedback_data.xml',
    ],
    'css': [
    ],
    'installable': True,
    'application': True,
}
