import requests
headers = {
    'Content-Type': 'application/json',
}
data = '{"params": {"name":"prakashsharma","email":"prakashsharmacs24@gmail.com","phone":"+917859884833"}}'
requests.post('http://localhost:8069/odoo/test/', headers=headers, data=data)