# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class account_invoice(models.Model):
    _inherit = "account.invoice"

    @api.model
    def _refund_cleanup_lines(self, lines):

        """ Convert records to dict of values suitable for one2many line creation

            :param recordset lines: records to convert
            :return: list of command tuple for one2many line creation [(0, 0, dict of valueis), ...]
        """
        result = super(account_invoice, self)._refund_cleanup_lines(lines)
        if result:
            for line in result:
                if line[2].get('product_id', False):
                    product_o = self.env['product.product'].browse(line[2]['product_id'])
                    new_account_id = product_o.x_property_account_refund.id or product_o.categ_id.x_property_account_refund_categ.id
                    if new_account_id:
                        line[2]['account_id'] = new_account_id
        return result

account_invoice()

class account_invoice_line(models.Model):
    _inherit = "account.invoice.line"

    @api.onchange('product_id')
    def _onchange_product_id(self):
        res = super(account_invoice_line,self)._onchange_product_id()
        if self.product_id and self.invoice_id.type == 'out_refund':
            product_o = self.product_id
            account_id = product_o.x_property_account_refund.id or product_o.categ_id.x_property_account_refund_categ.id

            if account_id:
                self.account_id = account_id
        if self.product_id:
            name_template = self.product_id.name
            self.name = name_template
        return res
