{
    "name": "Btek notification",
    "version": "1.0",
    "author" : 'Bave technology',
    'website' : 'http://bave.io/',
    "depends": [
        'base',
        'mail',
        'auditlog',
    ],
    "category": "Notification",
    "data": [
        'datas/notify_data.xml',

        'security/groups.xml',
        'security/ir.model.access.csv',

        'views/mail_message.xml',
        'views/res_users.xml',
        'views/notify_configuration.xml',
    ],
    'css': [
    ],
    'installable': True,
    'application': True,
}
