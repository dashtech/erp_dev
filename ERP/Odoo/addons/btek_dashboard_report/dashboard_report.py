from odoo import tools
from odoo import api, fields, models


class dashboard_report(models.Model):
    _name = "dashboard.report"
    _description = "Dashboard Report"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    date = fields.Datetime('Date Order', readonly=True)
    size = fields.Float('Size records', readonly=True)
    amount_tax = fields.Float('Amount Tax', readonly=True)
    amount_total = fields.Float('Amount Total', readonly=True)

    def _select(self):
        select_str = """
                    select  count(*) size , sum(so.amount_tax) amount_tax,sum(so.amount_total) amount_total, to_char(so.confirmation_date,'YYYY/MM/DD') date
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

    def _group_by(self):
        group_by_str = """
            GROUP BY to_char(so.confirmation_date,'YYYY/MM/DD')
        """
        return group_by_str

    @api.model_cr
    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            %s
            FROM ( %s )
            %s
            )""" % (self._table, self._select(), self._from(), self._group_by()))
