# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import datetime
from operator import itemgetter
from odoo import tools


class Bave_sale_report(models.Model):
    _name = "bave.sale.report"
    _description = "Bave sale report"
    _auto = False
    _order = 'date_order desc'

    def tr(self, model_name, field_name):
        uid = self.env.uid
        user = self.env['res.users'].browse(uid)
        lang = user.partner_id.lang

        name = model_name + ',' + field_name

        trans = self.env['ir.translation'].search_read(
            [('lang', '=', lang),
             ('type', '=', 'selection'),
             ('name', '=', name)],
            ['source', 'value']
        )

        res = dict((tran['source'], tran['value']) for tran in trans)
        return res

    def get_state_selection(self):
        tr_dict = self.env['bave.sale.report'
        ].tr('sale.order', 'state')
        selection = self.get_selection('state', 'sale.order')
        res =[]
        for s in selection:
            res.append(
                (s[0], tr_dict.get(s[1], s[1]))
            )

        return res

    def get_invoice_status_selection(self):
        return self.get_selection('invoice_status', 'sale.order.line')

    def get_selection(self, field_name, object_name):
        uid = self.env.uid
        user = self.env['res.users'].browse(uid)
        line_object = self.env[object_name]. \
            with_context(lang=user.partner_id.lang)
        line_field = line_object._fields[field_name]
        selection = line_field.selection
        return selection

    name = fields.Char()
    product_id = fields.Many2one('product.product', 'Product')
    order_id = fields.Many2one('sale.order', 'Order')
    price_unit = fields.Float()
    cost_price = fields.Float(compute='_compute_cost_price')
    cost_total = fields.Float(compute='_compute_cost_price')
    profit = fields.Float(compute='_compute_cost_price')
    discount = fields.Float()
    discount_total = fields.Float()
    subtotal_with_out_discount = fields.Float()
    product_uom_qty = fields.Float()
    price_subtotal = fields.Float('Subtotal with discount')
    sub_price_after_tax_discount = fields.Float('Total')
    default_code = fields.Char()
    license_plate = fields.Char()
    invoice_status = fields.Selection(
        selection=get_invoice_status_selection)
    product_uom = fields.Many2one('product.uom')
    company_id = fields.Many2one('res.company', 'Company')
    state = fields.Selection(selection=get_state_selection)
    partner_id = fields.Many2one('res.partner', 'Partner')
    date_order = fields.Datetime()
    date_date_order = fields.Date(string='Date order')
    date_date_order_str = fields.Char(string='Date order')
    product_type = fields.Selection(
        [('product', 'Product'),
         ('service', 'Service')],
        'Product type')
    mobile = fields.Char()
    user_id = fields.Many2one('res.users', 'Saleman')
    workorder_user_id = fields.Many2one('res.users', 'Workorder user')
    product_categ_id = fields.Many2one(
        'product.category', 'Product category')
    invoice_confirmed = fields.Boolean()
    upsell = fields.Boolean()
    price_tax = fields.Float()
    invoice_state = fields.Selection(
        [('open', 'Confirmed'),
         ('paid', 'Paid')]
    )

    @api.multi
    def _compute_cost_price(self):
        querry = """
                select l.id, max(sm.price_unit)
                from {} as l
                left join stock_picking as sp on sp.order_id = l.order_id
                left join stock_move as sm on sm.picking_id = sp.id
                  and sm.product_id = l.product_id
                  and sm.product_uom_qty = l.product_uom_qty
                where l.id in ({})
                group by l.id
        """.format(self._table,
                   ','.join([str(l_id) for l_id in self._ids])
        )
        self.env.cr.execute(querry)
        result = self.env.cr.fetchall()
        result_dict = dict((row[0], row[1]) for row in result)
        for line in self:
            cost_price = result_dict.get(line.id, 0) or 0
            line.cost_price = cost_price
            line.cost_total = cost_price*line.product_uom_qty
            line.profit = line.price_subtotal - line.cost_total
            if cost_price:
                continue
            if line.product_id.categ_id.property_cost_method == 'average':
                cost_price = line.product_id.standard_price or 0
                line.cost_price = cost_price
                line.cost_total = cost_price * line.product_uom_qty
                line.profit = line.price_subtotal - line.cost_total

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr,
                                  'bave_sale_report')
        self.env.cr.execute(
            """create or replace view bave_sale_report as(
            with order_line as (
              select -l.id as id,
                  l.product_id as product_id,
                  l.order_id as order_id,
                  l.price_unit as price_unit,
                  l.product_uom_qty as product_uom_qty,
                  l.price_subtotal as price_subtotal,
                  l.discount as discount,
                  l.invoice_status as invoice_status,
                  l.product_uom as product_uom,
                  l.name as name,
                  l.workorder_id as workorder_id,
                  l.invoice_confirmed as invoice_confirmed,
                  l.price_tax,
                  l.invoice_state,
                  l.sub_price_after_tax_discount,
                  case when l.user_id is null then w.user_id
                  else l.user_id end as user_id
              from sale_order_line as l
                left join sale_order as so on so.id = l.order_id
                left join fleet_workorder as w on w.id = l.workorder_id
              where so.create_form_fleet = true
              union all
              select l.id as id,
                  l.product_id as product_id,
                  l.order_id as order_id,
                  l.price_unit as price_unit,
                  l.product_uom_qty as product_uom_qty,
                  l.price_subtotal as price_subtotal,
                  l.discount as discount,
                  l.invoice_status as invoice_status,
                  l.product_uom as product_uom,
                  l.name as name,
                  l.workorder_id as workorder_id,
                  l.invoice_confirmed as invoice_confirmed,
                  l.price_tax,
                  l.invoice_state,
                  l.sub_price_after_tax_discount,
                  case when l.user_id is null then w.user_id
                  else l.user_id end as user_id
              from repair_order_line as l
                left join sale_order as so on so.id = l.order_id
                left join fleet_workorder as w on w.id = l.workorder_id
              where so.create_form_fleet = true
            )
            select l.id as id,
	          l.id as line_id,
              l.product_id as product_id,
              l.order_id as order_id,
              l.price_unit as price_unit,
              l.product_uom_qty as product_uom_qty,
              l.discount*0.01*l.product_uom_qty*l.price_unit
              as discount_total,
              l.product_uom_qty*l.price_unit
              as subtotal_with_out_discount,
              l.product_uom_qty*l.price_unit*(1.0-l.discount*0.01) as price_subtotal,
              l.discount as discount,
              l.invoice_status as invoice_status,
              l.product_uom as product_uom,
              l.name as name,
              l.invoice_confirmed as invoice_confirmed,
              l.price_tax,
              l.invoice_state,
              l.sub_price_after_tax_discount,
              l.workorder_id as workorder_id,
              l.user_id as workorder_user_id,
              o.company_id as company_id,
              o.state as state,
              o.partner_id as partner_id,
              o.date_order as date_order,
              o.date_order::date as date_date_order,
              o.date_order::date as date_date_order_str,
              o.user_id as user_id,
              o.upsell as upsell,
              pp.default_code,
              pt.categ_id as product_categ_id,
              array_to_string(array_agg(f.license_plate),', ') as license_plate,
              case when pt.type = 'service' then 'service'
              else 'product' end as product_type,
              rp.mobile
            from order_line as l
              left join sale_order as o on o.id = l.order_id
              left join product_product as pp on pp.id = l.product_id
              left join product_template as pt on pt.id = pp.product_tmpl_id
              left join res_partner as rp on rp.id = o.partner_id
              left join fleet_vehicle_sale_order_rel as r
                on r.sale_order_id = o.id
	          left join fleet_vehicle as f
	            on r.fleet_vehicle_id = f.id
	          left join fleet_workorder as w on w.id = l.workorder_id
            --where o.state != 'cancel'
            group by
              l.id,
              l.product_id,
              l.order_id,
              l.price_unit,
              l.product_uom_qty,
              l.price_subtotal,
              l.sub_price_after_tax_discount,
              l.discount,
              l.invoice_status,
              l.product_uom,
              l.name,
              l.invoice_confirmed,
              l.price_tax,
              l.invoice_state,
              l.workorder_id,
              l.user_id,
              o.company_id,
              o.state,
              o.partner_id,
              o.date_order,
              o.date_order::date,
              o.user_id,
              o.upsell,
              pp.default_code,
              pt.categ_id,
              pt.type,
              rp.mobile
            )
            """)


class Bave_sale_order_report(models.Model):
    _name = "bave.sale.order.report"
    _description = "Bave sale order report"
    _auto = False
    _order = 'date_order desc'

    def get_state_selection(self):
        tr_dict = self.env['bave.sale.report'
        ].tr('sale.order', 'state')
        selection = self.env['bave.sale.report'].get_selection('state', 'sale.order')
        res =[]
        for s in selection:
            res.append(
                (s[0], tr_dict.get(s[1], s[1]))
            )

        return res

    name = fields.Char('Order')
    license_plate = fields.Char()
    date_order = fields.Datetime()
    date_date_order = fields.Date(string='Date order')
    date_date_order_str = fields.Char(string='Date order')
    qty = fields.Float('Quantity')
    amount_untaxed_repair = fields.Float()
    amount_total_discount_repair = fields.Float()
    amount_tax_repair = fields.Float()
    amount_total_repair = fields.Float()
    state = fields.Selection(selection=get_state_selection)
    upsell = fields.Boolean()
    user_id = fields.Many2one('res.users', 'Assignee')
    invoice_confirmed = fields.Boolean()
    invoice_state = fields.Selection(
        [('open', 'Confirmed'),
         ('paid', 'Paid')])
    company_id = fields.Many2one('res.company', 'Company')

    @api.multi
    def open_line(self):
        action_obj = self.env.ref('btek_summary_dashboard.action_bave_sale_out_report')
        action = action_obj.read([])[0]
        action['name'] = self.name
        action['target'] = 'new'
        action['views'] = [(False, u'tree')]
        action['domain'] = [('order_id', '=', self.id)]
        action.pop('help')

        return action

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr,
                                  'bave_sale_order_report')
        self.env.cr.execute(
            """create or replace view bave_sale_order_report as(
                with order_line as (
                  select
                      l.order_id as order_id,
                      l.product_uom_qty as product_uom_qty
                  from sale_order_line as l
                    left join sale_order as so on so.id = l.order_id
                  where so.create_form_fleet = true
                  union all
                  select
                      l.order_id as order_id,
                      l.product_uom_qty as product_uom_qty
                  from repair_order_line as l
                    left join sale_order as so on so.id = l.order_id
                  where so.create_form_fleet = true
                ),
                qty_count as (
                select order_id, sum(product_uom_qty) as qty
                from order_line group by order_id
                )
                select o.id,
                    o.name,
                    o.date_order,
                    o.date_order::date as date_date_order,
                    o.date_order::date as date_date_order_str,
                    o.amount_untaxed_repair,
                    o.amount_total_discount_repair,
                    o.amount_tax_repair,
                    o.amount_total_repair,
                    o.state,
                    o.invoice_confirmed,
                    o.invoice_state,
                    o.upsell,
                    o.company_id,
                    o.user_id,
                    qc.qty,
                    array_to_string(array_agg(fv.license_plate),', ') as license_plate

                from sale_order as o
                  left join fleet_vehicle_sale_order_rel as r
                    on r.sale_order_id = o.id
                  left join fleet_vehicle as fv on fv.id = r.fleet_vehicle_id
                  left join qty_count as qc on qc.order_id = o.id
                where o.create_form_fleet = true
                group by o.id,
                    o.name,
                    o.date_order,
                    o.amount_untaxed_repair,
                    o.amount_total_discount_repair,
                    o.amount_tax_repair,
                    o.amount_total_repair,
                    o.state,
                    o.invoice_confirmed,
                    o.invoice_state,
                    o.upsell,
                    o.company_id,
                    o.user_id,
                    qc.qty
                )
            """)

