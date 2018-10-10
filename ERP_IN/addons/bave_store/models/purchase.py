# -*- encoding: utf-8 -*-
from datetime import datetime, timedelta
from odoo import api, fields, models, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    is_bave_store_order = fields.Boolean(
        default=False, readonly=True)

    @api.model
    def get_supplier(self, line):
        supplier = line.get('supplier', False)

        if not supplier:
            return False
        supplier_code = supplier.get('code', False)
        if not supplier_code:
            return False
        domain = [('supplier', '=', True),
                  ('code', '=', supplier_code)]
        supplier_s = self.env['res.partner'].search(domain)
        if supplier_s:
            return supplier_s[0].id

        supplier_name = supplier.get('name', False)
        if not supplier_name:
            return False

        supplier_value = {
            'name': supplier_name,
            'code': supplier_code,
            'supplier': True
        }
        supplier_obj = self.env['res.partner'].create(supplier_value)
        return supplier_obj.id

    @api.model
    def get_product(self, line):
        product = line.get('product', False)

        if not product:
            return False

        product_code = product.get('code', False)
        if not product_code:
            return False
        domain = [('default_code', '=', product_code)]
        product_s = self.env['product.product'].search(domain)
        if product_s:
            return product_s[0]

        product_name = product.get('name', False)
        if not product_name:
            return False

        uom_id = self.get_unit(line)
        if not uom_id:
            return False

        product_value = {
            'name': product_name,
            'default_code': product_code,
            'purchase_ok': True,
            'uom_id': uom_id,
            'uom_po_id': uom_id,
        }
        product_obj = self.env['product.product'].create(product_value)
        return product_obj

    @api.model
    def get_unit(self, line):
        unit_name = line.get('unit', False)

        if not unit_name:
            return False

        query = u"""
                    select id from product_uom
                    where lower(trim(name)) = %s
                """
        self.env.cr.execute(query, [unit_name.strip().lower()])
        query_result = self.env.cr.fetchall()
        if query_result:
            return query_result[0][0]

        uom_categ = self.env.ref('product.product_uom_categ_unit')
        if uom_categ:
            uom_categ_id = uom_categ.id
        else:
            uom_categs = self.env['product.uom.categ'].search([])
            if uom_categs:
                uom_categ_id = uom_categs[0].id
            else:
                uom_categ = self.env['product.uom.categ'].create({'name': 'Bave store unit'})
                uom_categ_id = uom_categ.id

        unit_value = {
            'name': unit_name,
            'category_id': uom_categ_id,
        }
        unit = self.env['product.uom'].create(unit_value)
        return unit.id

    @api.model
    def create_bave_store_purchase_order(self, detail):
        if not detail:
            return {"result": "NOT OK",
                    "message": "purchase order detail invalid"}

        date_order = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        date_planned = datetime.now() + timedelta(hours=2)
        date_planned = date_planned.strftime('%Y-%m-%d %H:%M:%S')

        po_dict = {}
        for line in detail:
            supplier_id = self.get_supplier(line)
            if not supplier_id:
                return {"result": "NOT OK",
                        "message": "supplier invalid"}
            product = self.get_product(line)
            if not product:
                return {"result": "NOT OK",
                        "message": "product invalid"}

            try:
                qty = float(line['qty'])
                price_unit = float(line['price_unit'])
            except:
                return {"result": "NOT OK",
                        "message": "qty or price_unit invalid"}
            if not po_dict.get(supplier_id, False):
                po_dict[supplier_id] = []
            po_dict[supplier_id].append(
                {
                    'product_id': product.id,
                    'name': product.default_code,
                    'product_uom': product.uom_po_id.id,
                    'product_qty': qty,
                    'price_unit': price_unit,
                    'date_planned': date_planned
                }
            )
        purchase_list = []
        for supplier_id in po_dict.keys():
            vals = {
                'date_order': date_order,
                'partner_id': supplier_id,
                'is_bave_store_order': True,
                'order_line': [(0, 0, line) for line in po_dict[supplier_id]]
            }
            purchase = self.create(vals)
            purchase_list.append(purchase.name)

        return {
            "result": "OK",
            "res_po": purchase_list
        }
