# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _


class ProductTemplate(models.Model):
    _inherit = "product.template"

    suggest_ids = fields.Many2many(
        'product.product',
        'product_product_suggest_rel',
        'product_id', 'suggest_id',
        'Suggest product')

    hs_code = fields.Char()
    description = fields.Text()
    product_origin_id = fields.Many2one('product.origin', string='Product origin')
    is_cost_item = fields.Boolean(string='Cost Item')
    purchase_method = fields.Selection([
        ('purchase', 'On ordered quantities'),
        ('receive', 'On received quantities'),
    ], default="purchase")

    @api.onchange('is_cost_item')
    def _change_is_cost_item(self):
        if self.is_cost_item is True:
            self.sale_ok = False
            self.purchase_ok = False

    _sql_constraints = [
        ('default_code_unique', 'check(1=1)', 'Product Code Must Be Unique !!!'),
    ]

    @api.model
    def default_get(self, fields):
        res = super(ProductTemplate, self).default_get(fields)
        res['taxes_id'] = False
        res['supplier_taxes_id'] = False

        res['type'] = self.env.context.get('default_type', 'product')
        return res


class ProductProduct(models.Model):
    _inherit = "product.product"


    default_code = fields.Char('Product code', index=True,
                               required=True)

    _sql_constraints = [
        ('default_code_uniq', 'unique(default_code)', 'Product Code Must Be Unique !!!'),
    ]

    @api.onchange('is_cost_item')
    def _change_is_cost_item(self):
        if self.is_cost_item is True:
            self.sale_ok = False
            self.purchase_ok = False
            cated_id = self.env['product.category'].search([('name', '=', 'Danh mục chi phí')])
            self.categ_id = cated_id

    @api.model
    def name_search(self, name='', args=None,
                    operator='ilike', limit=100):
        res = super(ProductProduct, self).name_search(
            name=name, args=args,
            operator=operator, limit=limit)

        if not name:
            return res
        limit = limit or 0

        searched_ids = [r[0] for r in res]

        deficit = limit - len(res)
        if deficit <= 0:
            return res

        args = args or []
        args.append(['hs_code', 'ilike', name])
        args.append(['id', 'not in', searched_ids])

        products = self.search(args, limit=deficit)
        products_name_get = products.name_get()
        res.extend(products_name_get)

        return res

    @api.multi
    def name_get(self):
        if not self.env.context.get('only_show_name', False):
            return super(ProductProduct, self).name_get()

        res = [(p.id, p.name) for p in self]

        return res

    @api.model
    def create(self, vals):
        product_tmpl_id = vals.get('product_tmpl_id', False)
        if product_tmpl_id and not vals.get('default_code'):
            product_tmpl = self.env['product.template'].browse(product_tmpl_id)
            if product_tmpl.default_code:
                vals['default_code'] = product_tmpl.default_code

        res = super(ProductProduct, self).create(vals)
        return res


class ProductCategory(models.Model):
    _inherit = "product.category"

    property_account_creditor_price_difference_categ = fields.Many2one(
        'account.account', string="Price Difference Account",
        company_dependent=True, copy=True, required=True,
        help="This account will be used to value price difference between purchase price and accounting cost.")
    property_account_income_categ_id = fields.Many2one('account.account', company_dependent=True, required=True,
                                                       string="Income Account", oldname="property_account_income_categ",
                                                       domain=[('deprecated', '=', False)], copy=True,
                                                       help="This account will be used for invoices to value sales.")
    property_account_expense_categ_id = fields.Many2one('account.account', company_dependent=True, required=True,
                                                        string="Expense Account", copy=True,
                                                        oldname="property_account_expense_categ",
                                                        domain=[('deprecated', '=', False)],
                                                        help="This account will be used for invoices to value expenses.")
    property_stock_journal = fields.Many2one('account.journal', copy=True, required=True,
                                             string='Stock Journal', company_dependent=True,
        help="When doing real-time inventory valuation, this is the Accounting Journal in which entries will be automatically posted when stock moves are processed.")
    property_stock_account_input_categ_id = fields.Many2one(
        'account.account', 'Stock Input Account', company_dependent=True, required=True,
        domain=[('deprecated', '=', False)], copy=True,
        oldname="property_stock_account_input_categ",
        help="When doing real-time inventory valuation, counterpart journal items for all incoming stock moves will be posted in this account, unless "
             "there is a specific valuation account set on the source location. This is the default value for all products in this category. It "
             "can also directly be set on each product")
    property_stock_account_output_categ_id = fields.Many2one(
        'account.account', 'Stock Output Account', company_dependent=True, required=True,
        domain=[('deprecated', '=', False)], copy=True,
        oldname="property_stock_account_output_categ",
        help="When doing real-time inventory valuation, counterpart journal items for all outgoing stock moves will be posted in this account, unless "
             "there is a specific valuation account set on the destination location. This is the default value for all products in this category. It "
             "can also directly be set on each product")
    property_stock_valuation_account_id = fields.Many2one(
        'account.account', 'Stock Valuation Account', company_dependent=True, required=True,
        domain=[('deprecated', '=', False)], copy=True,
        help="When real-time inventory valuation is enabled on a product, this account will hold the current value of the products.", )

    @api.model
    def default_get(self, fields):
        res = super(ProductCategory, self).default_get(fields)

        account_creditor_price_difference_categ_id = self.env['account.account'].search([('code', 'like', '%TG%1521%')])
        if account_creditor_price_difference_categ_id:
            res['property_account_creditor_price_difference_categ'] = account_creditor_price_difference_categ_id[0].id

        account_income_categ_id = self.env['account.account'].search([('code', '=', '51135')])
        if account_income_categ_id:
            res['property_account_income_categ_id'] = account_income_categ_id[0].id

        account_expense_categ_id = self.env['account.account'].search([('code', 'like', '%TG%1521%')])
        if account_expense_categ_id:
            res['property_account_expense_categ_id'] = account_expense_categ_id[0].id

        stock_account_input_categ_id = self.env['account.account'].search([('code', 'like', '%TG%1521%')])
        if stock_account_input_categ_id:
            res['property_stock_account_input_categ_id'] = stock_account_input_categ_id[0].id

        stock_account_output_categ_id = self.env['account.account'].search([('code', '=', '63235')])
        if stock_account_output_categ_id:
            res['property_stock_account_output_categ_id'] = stock_account_output_categ_id[0].id

        stock_valuation_account_id = self.env['account.account'].search([('code', '=', '1521')])
        if stock_valuation_account_id:
            res['property_stock_valuation_account_id'] = stock_valuation_account_id[0].id


        res['property_cost_method'] = 'average'
        res['property_valuation'] = 'real_time'

        return res

    @api.onchange('parent_id')
    def change_parent_id(self):
        if self.parent_id:
            self.property_account_creditor_price_difference_categ = self.parent_id.property_account_creditor_price_difference_categ
            self.property_account_income_categ_id = self.parent_id.property_account_income_categ_id
            self.property_account_expense_categ_id = self.parent_id.property_account_expense_categ_id
            self.property_stock_account_input_categ_id = self.parent_id.property_stock_account_input_categ_id
            self.property_stock_account_output_categ_id = self.parent_id.property_stock_account_output_categ_id
            self.property_stock_valuation_account_id = self.parent_id.property_stock_valuation_account_id
            self.property_stock_journal = self.parent_id.property_stock_journal

