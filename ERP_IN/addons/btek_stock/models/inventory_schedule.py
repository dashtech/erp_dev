# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class BtekWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    code = fields.Char('Short Name', required=True, size=10,
                       help="Short name used to identify your warehouse")

    def _get_sequence_values(self):
        return {
            'in_type_id': {'name': self.name + ' ' + _('Sequence PNK'), 'prefix': 'PNK', 'padding': 5},
            'out_type_id': {'name': self.name + ' ' + _('Sequence PXK'), 'prefix': 'PXK', 'padding': 5},
            'pack_type_id': {'name': self.name + ' ' + _('Sequence packing'), 'prefix': self.code + '/PACK/', 'padding': 5},
            'pick_type_id': {'name': self.name + ' ' + _('Sequence picking'), 'prefix': self.code + '/PICK/', 'padding': 5},
            'int_type_id': {'name': self.name + ' ' + _('Sequence internal'), 'prefix': self.code + '/INT/', 'padding': 5},
        }


class BtekInventoryConfig(models.Model):
    _name = 'btek.inventory.config'

    name = fields.Char(default=_('Configure'), translate=True)
    mailling_list = fields.Text('Mailing list', help='Email been delimited by mark ;')

    @api.multi
    def check_inventory(self):
        products_orderpoit = self.env['stock.warehouse.orderpoint'].sudo().search([])
        if not products_orderpoit:
            return True
        products = []
        for product in products_orderpoit:
            products.append({
                'product_id': product.product_id.id,
                'location_id': product.location_id.id,
                'min_qty': product.product_min_qty,
                'company_id': product.company_id.id,
            })
        warning_lst = []
        for product in products:
            check_quant = self.env['stock.quant'].sudo().search([
                ('product_id', '=', product['product_id']),
                ('location_id', '=', product['location_id']),
                ('company_id', '=', product['company_id'])
            ])
            warning = {}
            if check_quant and check_quant.qty < product['min_qty']:
                warning['product'] = check_quant.product_id.name or ''
                warning['location'] = check_quant.location_id.name or ''
                warning['min_qty'] = product['min_qty'] or 0
                warning['product_qty'] = check_quant.qty or 0
                warning['check'] = check_quant.qty - product['min_qty']
                warning_lst.append(warning)
        return warning_lst

    def send_email(self):
        id_ = self.env.ref('btek_stock.inventory_config_view').id
        res = self.env.ref('btek_stock.inventory_warning_templates').send_mail(id_)
        return res


class StockWarehouseOrderpointInherit(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    _sql_constraints = [
        ('check_product_location', 'unique(product_id, location_id)',
         _('Can not create Reordering Rules, product with location existed!'))
    ]
