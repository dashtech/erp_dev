{
    "name": "Preview xlsx report",
    "version": "1.0",
    "author" : 'Bave technology',
    'website' : 'http://bave.io/',
    "depends": [
        'website',
    ],
    "category": "Report",
    "data": [
        'templates/xlsx_report.xml',
    ],
    'css': [
        'preview_xlsx_report/static/src/css/style.css',
    ],
    'external_dependencies': {'python': ['openpyxl','xlsx2html']},
    'installable': True,
    'application': True,
}

# openpyxl==2.4.8