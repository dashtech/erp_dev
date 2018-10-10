# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by 73lines
# See LICENSE file for full copyright and licensing details.

from collections import OrderedDict

from odoo import api, fields, models


class ProductAttributeCategory(models.Model):
    _name = "product.attribute.category"
    _description = "Product Attribute Category"
    _order = 'sequence'

    name = fields.Char(string="Category Name", required=True)
    sequence = fields.Integer(help="Gives the sequence order when "
                                   "displaying a list of rules.")


class ProductAttribute(models.Model):
    _inherit = 'product.attribute'

    category_id = fields.Many2one('product.attribute.category',
                                  string="Category")

    @api.multi
    @api.depends('name')
    def name_get(self):
        result = []
        for attr in self:
            name = attr.name
            if attr.category_id:
                name = ('%s (%s)' % (attr.name, attr.category_id.name))
            result.append((attr.id, name))
        return result


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def get_variant_groups(self):
        res = OrderedDict()
        for var in self.sudo().attribute_line_ids:
            res.setdefault(var.attribute_id.category_id.name, []).append(var)
        return res
