from odoo import http


class controller_example(http.Controller):
    @http.route('/example', type='http', auth='public', website=True)
    def render_example_page(self):
        return http.request.render('btek_dashboard_report8.example_page', {})