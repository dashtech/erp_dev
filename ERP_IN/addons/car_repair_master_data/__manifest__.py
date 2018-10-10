{
    "name": "Car repair master data",
    "version": "1.0",
    "author" : 'Bave technology',
    'website' : 'http://bave.io/',
    "depends": [
        'car_repair_industry'
    ],
    "category": "Master data",
    "data": [
        'views/wizard_import_fleet_model.xml',
        'views/wizard_import_fleet_vehicle.xml',
        'views/wizard_import_car_repair_history.xml',
    ],
    'installable': True,
    'application': True,
}
