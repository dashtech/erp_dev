# -*- coding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import pytz

sequence_index = 0
default_code_index = 1
name_index = 3
date_planned_index = 4
product_qty_index = 5
product_uom_index = 6
price_unit_index = 7
taxes_id_index = 8

MIN_COL_NUMBER = 9


class ImportPurchaseOrderLine(models.TransientModel):
    _name = 'import.purchase.order.line'
    _inherits = {'ir.attachment': 'attachment_id'}
    _import_model_name = 'purchase.order.line'
    _import_date_format = '%d-%m-%Y'

    order_id = fields.Many2one('purchase.order')
    template_file_url = fields.Char(compute='_compute_template_file_url',
                                    default=lambda self:
                                    self.env['ir.config_parameter'].
                                    get_param('web.base.url') +
                                    '/btek_purchase/static/import_template/'
                                    'import_purchase_order_line.xlsx')

    @api.multi
    def _compute_template_file_url(self):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        url = base_url + '/btek_purchase/static/import_template/import_purchase_order_line.xlsx'
        for ip in self:
            ip.template_file_url = url

    @api.multi
    def import_order_line(self):
        # read excel file
        data = self.datas
        sheet = False

        user = self.env.user
        path = '/import_purchase_order_template_' \
               + user.login + '_' + str(
            self[0].id) + '_' + str(
            datetime.now()) + '.xls'
        path = path.replace(' ', '_')

        read_excel_obj = self.env['read.excel']
        excel_data = read_excel_obj.read_file(data, sheet, path)

        # check content excel data
        if len(excel_data) < 3:
            raise ValidationError(_('Cannot import empty file!'))

        # delete header excel (2 first line in file)
        del excel_data[0]

        # check number column excel file
        if len(excel_data[1]) < MIN_COL_NUMBER:
            raise ValidationError(_(
                'Format file incorrect, you must import file have at least {} column!').format(
                MIN_COL_NUMBER))

        # check format data in excell file(unicode, str, ...)
        self.verify_excel_data(excel_data)

        # Get db data dict for many2one, many2many field: dict with key = name,
        # value = ID db
        product_dict, product_uom_dict, tax_dict = \
            self.get_db_data(excel_data)

        # Get values list to create from excel data map with db data
        values_list = []

        row_num = 1
        for row in excel_data:
            row_num += 1
            values = self.get_value_from_excel_row(
                row, row_num, product_dict,
                product_uom_dict, tax_dict
            )
            values_list.append(values)

        self.create_record(values_list)

        return True

    @api.multi
    def verify_excel_data(self, excel_data):
        row_count = 1

        for row in excel_data:
            row_count += 1

            try:
                row[sequence_index] = row[sequence_index] or 0
                row[sequence_index] = int(row[sequence_index])
            except:
                raise UserError(
                    _('Error: row {} sequence invalid!').format(row_count))

            if not row[default_code_index]:
                raise UserError(
                    _('Error: row {} product code invalid!').format(row_count))

            try:
                row[default_code_index] = unicode(row[default_code_index])
            except:
                raise UserError(
                    _('Error: row {} product code invalid!').format(row_count))
            try:
                row[name_index] = row[name_index] or ''
                row[name_index] = unicode(row[name_index])
            except:
                raise UserError(
                    _('Error: row {} name invalid!').format(row_count))

            try:
                row[date_planned_index] = row[date_planned_index] or ''
                row[date_planned_index] = unicode(row[date_planned_index])
                if row[date_planned_index]:
                    date_planned = datetime.strptime(
                        row[date_planned_index], '%Y-%m-%d %H:%M:%S')
            except:
                raise UserError(
                    _('Error: row {} date planned invalid!').format(row_count))

            try:
                row[product_qty_index] = float(row[product_qty_index])
            except:
                raise UserError(
                    _('Error: row {} qty invalid!').format(row_count))

            try:
                row[product_uom_index] = unicode(row[product_uom_index])
            except:
                raise UserError(
                    _('Error: row {} Uom invalid!').format(row_count))

            try:
                row[price_unit_index] = float(row[price_unit_index])
            except:
                raise UserError(
                    _('Error: row {} price invalid!').format(row_count))

            try:
                row[taxes_id_index] = unicode(row[taxes_id_index])
            except:
                raise UserError(
                    _('Error: row {} tax invalid!').format(row_count))

        return True

    @api.multi
    def get_db_data(self, excel_data):
        product_code_list = []
        product_uom_list = []
        tax_list = []

        for row in excel_data:
            product_code = row[default_code_index].strip()
            product_uom = row[product_uom_index].strip()
            tax = row[taxes_id_index].strip()
            if tax:
                tax_list.extend(tax.split(','))
            if product_code:
                product_code_list.append(product_code)
            if product_uom:
                product_uom_list.append(product_uom)


        product_s = \
            self.env['product.product'].search_read(
                [('default_code', 'in', product_code_list)],
                ['default_code', 'uom_po_id', 'name']
            )

        product_dict = \
            dict((product['default_code'], product) for product in product_s)

        product_uom_s = \
            self.env['product.uom'].search_read(
                [('name', 'in', product_uom_list)],
                ['name']
            )
        product_uom_dict = \
            dict((uom['name'], uom['id']) for uom in product_uom_s)
        tax_s = \
            self.env['account.tax'].search_read(
                [('name', 'in', tax_list)],
                ['name']
            )
        tax_dict = dict((tax['name'], tax['id']) for tax in tax_s)
        return product_dict, product_uom_dict, tax_dict

    @api.multi
    def get_value_from_excel_row(
            self, row, row_num, product_dict,
            product_uom_dict, tax_dict):
        value = {
            'sequence': row[sequence_index],
            'product_qty': row[product_qty_index],
            'price_unit': row[price_unit_index],
        }

        default_code = row[default_code_index]
        name = row[name_index]
        date_planned = row[date_planned_index]
        product_uom = row[product_uom_index]
        taxes = row[taxes_id_index]

        product = product_dict.get(default_code, False)
        if not product:
            raise UserError(
                _('Error: row {}: cannot find product with product code ="{}"'
                  ).format(row_num, default_code))
        product_id = product['id']
        value['product_id'] = product_id

        if not name:
            name = u'[{}]{}'.format(product['default_code'],
                                   product['name'])
        value['name'] = name

        if not date_planned:
            date_planned = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            date_planned = \
                self.change_local_datetime_to_utc(date_planned)

        value['date_planned'] = date_planned

        product_uom_id = False
        if product_uom:
            product_uom_id = product_uom_dict.get(product_uom, False)
            if not product_uom_id:
                raise UserError(
                    _('Error: row {} unit invalid !').format(row_num))
        else:
            product_uom_id = product['uom_po_id'][0]

        value['product_uom'] = product_uom_id

        taxes_list = taxes.split(',')
        taxes_id = [(6, False, [])]
        for taxes_item in taxes_list:
            if not taxes_item:
                continue

            tax_id = tax_dict.get(taxes_item, False)
            if not tax_id:
                raise UserError(_('Error: row {} cannot find tax "{}"'
                                  ).format(row_num, taxes_item))
            taxes_id[0][2].append(tax_id)

        value['taxes_id'] = taxes_id

        return value

    def change_local_datetime_to_utc(self, souce_date):
        user_tz = self.env.user.tz or str(pytz.utc)
        tz_now = datetime.datetime.now(pytz.timezone(user_tz))
        difference = tz_now.utcoffset().total_seconds() / 60 / 60
        difference = int(difference)
        souce_date = datetime.datetime.strptime(
            souce_date, '%Y-%m-%d %H:%M:%S')
        local_date = souce_date + timedelta(hours=-difference)
        return local_date.strftime('%Y-%m-%d %H:%M:%S')

    # Create record from values list
    @api.multi
    def create_record(self, value_list):
        model_name_obj = self.env[self._import_model_name]
        default_value = model_name_obj.default_get([])
        values = {'order_line': []}

        for value in value_list:
            default_value_copy = default_value.copy()
            default_value_copy.update(value)
            values['order_line'].append(
                (0, 0, default_value_copy)
            )

        self[0].order_id.write(values)

        return True


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    real_date_order = fields.Char('Real Date Order', compute='get_real_date_order')
    real_date_planned = fields.Char('Real Date Planned', compute='get_real_date_planned')
    amount_total_in_word = fields.Text(compute='_compute_amount_total_in_word', readonly=True)

    @api.one
    @api.depends('date_order')
    def get_real_date_order(self):
        user_tz = self.env.user.tz or str(pytz.utc)
        tz_now = datetime.now(pytz.timezone(user_tz))
        difference = tz_now.utcoffset().total_seconds() / 60 / 60
        difference = int(difference)
        if self.date_order:
            real_date = datetime.strptime(self.date_order, '%Y-%m-%d %H:%M:%S') + timedelta(hours=difference)
            self.real_date_order = str(datetime.strftime(real_date, '%d-%m-%Y'))

    @api.one
    @api.depends('date_planned')
    def get_real_date_planned(self):
        user_tz = self.env.user.tz or str(pytz.utc)
        tz_now = datetime.now(pytz.timezone(user_tz))
        difference = tz_now.utcoffset().total_seconds() / 60 / 60
        difference = int(difference)
        if self.date_planned:
            real_date = datetime.strptime(self.date_planned, '%Y-%m-%d %H:%M:%S') + timedelta(hours=difference)
            self.real_date_planned = str(datetime.strftime(real_date, '%d-%m-%Y'))

    @api.multi
    def open_wizard_import_order_line(self):
        action_obj = self.env.ref(
            'btek_purchase.action_import_purchase_order_line')
        action = action_obj.read()[0]
        action['context'] = {
            'default_order_id': self[0].id,
            'default_name': '[{}]import purchase order line'.format(
                self[0].name)
        }
        return action

    _sql_constraints = [
        ('check_date_order_date_planned',
         'check(date_order <= date_planned)',
         'Date planned must be greater than date order!'),
    ]

    @api.multi
    @api.depends('amount_total')
    def _compute_amount_total_in_word(self):
        for s in self:
            if s.amount_total:
                s.amount_total_in_word = s.env['read.number'].docso(int(s.amount_total))

    @api.multi
    def print_quotation(self):
        self.write({'state': "sent"})
        return self.env['report'].get_action(self, 'btek_purchase.btek_purchase_quotation')

    @api.multi
    def bave_action_rfq_send(self):
        '''
        This function opens a window to compose an email, with the edi purchase template message loaded by default
        '''
        self.ensure_one()
        ir_model_data = self.env['ir.model.data']
        try:
            if self.env.context.get('send_rfq', False):
                template_id = ir_model_data.get_object_reference('btek_purchase', 'bave_email_template_edi_purchase')[1]
            else:
                template_id = ir_model_data.get_object_reference('btek_purchase', 'bave_email_template_edi_purchase_done')[1]
        except ValueError:
            template_id = False
        try:
            compose_form_id = ir_model_data.get_object_reference('mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False
        ctx = dict(self.env.context or {})
        ctx.update({
            'default_model': 'purchase.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
        })
        return {
            'name': _('Compose Email'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    sequence = fields.Integer()

    _sql_constraints = [
        ('sequence_uniq', 'check(1=1)',
         'The sequence must be unique per order!')
    ]

    @api.onchange('product_id')
    def onchange_product_id(self):
        res = super(PurchaseOrderLine, self).onchange_product_id()
        product_lang = self.product_id.with_context(
            lang=self.partner_id.lang,
            partner_id=self.partner_id.id,
        )
        if not product_lang:
            return res
        self.name = product_lang.code
        return res

    # @api.model
    # def default_get(self, fields):
    #     order_obj = self.env['purchase.order'].browse(1).onchange_seq()
    #     # self.with_context(get_sizes=True, default_sequence=order_obj)
    #     res = super(PurchaseOrderLine, self.with_context(get_sizes=True, default_sequence=order_obj)).default_get(fields)
    #     return res

