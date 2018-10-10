# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class ProductCategory(models.Model):
    _inherit = 'product.category'

    def get_product_in_category(self, x_type):
        if x_type == 'service':
            querry = """
                 select count(p.id) as prod_count, pc.id, pc.name
                 from product_template p 
                 inner join product_category pc on p.categ_id = pc.id 
                 where p.type = 'service'
                 GROUP BY pc.id
                """
            self.env.cr.execute(querry)
            res = self.env.cr.fetchall()
        if x_type == 'product':
            querry = """select count(p.id) as prod_count, pc.id, pc.name
                         from product_template p 
                         inner join product_category pc on p.categ_id = pc.id 
                         where p.type = 'product' or p.type = 'consu'
                         GROUP BY pc.id
                        """
            self.env.cr.execute(querry)
            res = self.env.cr.fetchall()
        return res
