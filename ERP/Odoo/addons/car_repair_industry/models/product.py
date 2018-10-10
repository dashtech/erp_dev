from odoo import fields, api, models


class BTProduct(models.Model):

    _inherit = "product.template"

    vehicle_model_id = fields.Many2many(
        "fleet.vehicle.model", "product_ids",
        string="Model")
    service_type_id = fields.Many2many(
        "service.type", "product_template_id",
        string="Service Type")
    # fleet_service_type_id = fields.Many2many("fleet.service.type", "product_ids", string="Fleet Service Type")
    fleet_vehicle_brand_id = fields.Many2many(
        "fleet.vehicle.model.brand", "product_id",
        string="Brand")
    # ticked = fields.Boolean(string="")

    is_service_package = fields.Boolean(
        compute='_compute_is_service_package',
        readonly=True, store=True
    )
    compute_vehicle_model = \
        fields.Integer(compute='_compute_vehicle_model',
                       search='search_vehicle_model')
    compute_vehicle_model_brand = \
        fields.Integer(compute='_compute_vehicle_model_brand',
                       search='search_vehicle_model_brand')

    def search_vehicle_model(self, operator, value):
        if not value:
            return []

        domain = ['|' for i in range(0, len(value))]

        for model_id in value:
            domain.append(('vehicle_model_id', 'in', model_id))

        domain.append(('vehicle_model_id', '=', False))
        return domain

    def search_vehicle_model_brand(self, operator, value):
        if not value:
            return []

        domain = ['|' for i in range(0, len(value))]

        for brand_id in value:
            domain.append(('fleet_vehicle_brand_id', 'in', brand_id))

        domain.append(('fleet_vehicle_brand_id', '=', False))
        return domain

    @api.depends('bom_ids.type')
    @api.multi
    def _compute_is_service_package(self):
        ids = self._ids
        ids_text = ','.join([str(id) for id in ids])

        query = """
                    select pt.id,
                        count(b.id)
                    from product_template as pt
                        left join mrp_bom as b
                            on pt.id = b.product_tmpl_id
                            and b.type = 'phantom'
                    where pt.id in ({})
                    group by pt.id
                """.format(ids_text)
        self.env.cr.execute(query)
        result_dict = \
            dict((row[0], row[1]) for row in self.env.cr.fetchall())

        for product in self:
            if result_dict.get(product.id, False):
                product.is_service_package = True
                continue
            product.is_service_package = False

    @api.onchange('vehicle_model_id')
    def onchange_vehicle_model(self):
        pass

    @api.multi
    def write(self, value):
        if 'vehicle_model_id' not in value.keys() and 'service_type_id' not in value.keys():
            return super(BTProduct, self).write(value)
        old_vehicle_model_id = self.vehicle_model_id
        old_service_type_id = self.service_type_id
        res = super(BTProduct, self).write(value)
        if res and "vehicle_model_id" in value and self.env.context.get('FROM_FLEET', True):
            for fv in self.vehicle_model_id:
                if fv not in old_vehicle_model_id:
                    product_id = fv.product_ids.ids
                    product_id.extend(self.ids)
                    value_write = {'product_ids': [[6, False, product_id]]}
                    fv.with_context(FROM_FLEET=False).write(value_write)
            fv_destroy = [x for x in old_vehicle_model_id if x not in self.vehicle_model_id]
            for fv_des in fv_destroy:
                product_id = fv_des.product_ids.ids
                for _id in self.ids:
                    if _id in product_id:
                        product_id.remove(_id)
                value_write = {'product_ids': [[6, False, product_id]]}
                fv_des.with_context(FROM_FLEET=False).write(value_write)
        if res and "service_type_id" in value and self.env.context.get('FROM_FLEET', True):
            for fv in self.service_type_id:
                if fv not in old_service_type_id:
                    product_id = fv.product_template_id.ids
                    product_id.extend(self.ids)
                    value_write = {'product_template_id': [[6, False, product_id]]}
                    fv.with_context(FROM_FLEET=False).write(value_write)
            fv_destroy = [x for x in old_service_type_id if x not in self.service_type_id]
            for fv_des in fv_destroy:
                product_id = fv_des.product_template_id.ids
                for _id in self.ids:
                    if _id in product_id:
                        product_id.remove(_id)
                value_write = {'product_template_id': [[6, False, product_id]]}
                fv_des.with_context(FROM_FLEET=False).write(value_write)
        return res

    @api.model
    def write_relation_field(self, field_get=None, type="create"):
        if field:
            if type == "create":
                for vm in res[field_get]:
                    product_ids = vm.product_ids.ids
                    product_ids.extend(res.ids)
                    value_write = {'product_ids': [[6, False, product_ids]]}
                    vm.with_context(FROM_FLEET=False).write(value_write)
            elif type == "write":
                pass

    # @api.model
    # def create(self, value):
    #     res = super(BTProduct, self).create(value)
    #     if res:
    #         # self.write_relation_field(field_get="vehicle_model_id")
    #         # self.write_relation_field(field_get="service_type_ids")
    #         for vm in res.vehicle_model_id:
    #             product_ids = vm.product_ids.ids
    #             product_ids.extend(res.ids)
    #             value_write = {'product_ids': [[6, False, product_ids]]}
    #             vm.with_context(FROM_FLEET=False).write(value_write)
    #         for st in res.service_type_id:
    #             product_ids = st.product_template_id.ids
    #             product_ids.extend(res.ids)
    #             value_write = {'product_template_id': [[6, False, product_ids]]}
    #             st.with_context(FROM_FLEET=False).write(value_write)
    #     return res

BTProduct()
