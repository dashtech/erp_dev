from odoo import tools
from odoo import api, fields, models


class dashboard_report_customer(models.Model):
    _name = "dashboard.report.customer"
    _description = "Darkboard Report Customer"
    _auto = False
    _rec_name = 'amount_total'
    _order = 'amount_total desc'

    cus_name = fields.Datetime('Customer Name', readonly=True)
    size = fields.Float('Size records', readonly=True)
    amount_tax = fields.Float('Amount Tax', readonly=True)
    amount_total = fields.Float('Amount Total', readonly=True)

    def _select(self):
        select_str = """
                    select  count(*) size , sum(so.amount_tax) amount_tax,sum(so.amount_total) amount_total,  pn.name cus_name
        """
        return select_str

    def _from(self):
        from_str = """
                sale_order so
                    left join product_pricelist pl on so.pricelist_id=pl.id
                    left join res_partner pn on so.partner_id=pn.id
                    left join res_users us on so.user_id=us.id
                    left join res_company com on so.company_id=com.id
        """
        return from_str

    def _where(self):
        where_str = """
            where so.confirmation_date <= now() and so.confirmation_date >= now()- interval '7 day' 
        """
        return where_str

    def _group_by(self):
        group_by_str = """
            GROUP BY pn.name
        """
        return group_by_str

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            %s
            %s
            )""" % (self._table, self._select(), self._from(),self._where(), self._group_by()))
