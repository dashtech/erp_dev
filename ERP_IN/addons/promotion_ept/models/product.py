from odoo import api, fields, models

class product(models.Model):
    _inherit='product.product'
    
    is_promo_product=fields.Boolean("Is Promotion Product")
    
    @api.multi
    def _get_promo_product_category(self):
        if self._context.get('default_type')=='service':
            category_id = self.env['ir.values'].sudo().get_default('sale.config.settings', 'promotion_product_category_id')
            if category_id:
                return self.env['product.category'].search([('id','=',category_id)])
            else:
                return self.env['product.template']._get_default_category_id()
        else:
            return self.env['product.template']._get_default_category_id()
        
    categ_id = fields.Many2one(
        'product.category', 'Internal Category',
        change_default=True, default=_get_promo_product_category, domain="[('type','=','normal')]",
        required=True, help="Select category for the current product")