{
    "name": "Btek website menu",
    "version": "1.0",
    "author" : 'Bave technology',
    'website' : 'http://bave.io/',
    "depends": [
        'base',
        'website',
        'web',
        'website_sale'
    ],
    "category": "Website",
    "data": [
        'views/website_menu_view.xml',
        'views/website_header_footer.xml',
		'views/login.xml',
    ],
    'css': [
        'btek_website_menu/static/src/css/website_menu_style.css',
    ],
    'installable': True,
    'application': True,
}
