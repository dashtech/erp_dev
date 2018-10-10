# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import AccessDenied, UserError
import odoo.addons.decimal_precision as dp
import datetime


class res_currency(models.Model):
    _inherit = 'res.currency'

    currency_text = fields.Char(string='Currency Text', size=256, translate=True, help="The full text of the currency, e.g. United State Dollar, Vietnam Dong, etc")


class account_voucher(models.Model):
    _inherit = 'account.voucher'

    amount_in_word = fields.Char(compute='_compute_amount_in_word')

    @api.multi
    @api.depends('amount')
    def _compute_amount_in_word(self):
        for s in self:
            if s.amount:
                s.amount_in_word = s.env['read.number'].docso(int(s.amount))

    def _word(self, number):
        return {
            '0': 'không',
            '1': 'một',
            '2': 'hai',
            '3': 'ba',
            '4': 'bốn',
            '5': 'năm',
            '6': 'sáu',
            '7': 'bảy',
            '8': 'tám',
            '9': 'chín',
        }[number]

    def _unit(self, number_of_digits):
        return {
            '1': '',
            '2': 'nghìn',
            '3': 'triệu',
            '4': 'tỷ',
            '5': 'nghìn',
            '6': 'triệu',
            '7': 'tỷ ',
        }[number_of_digits]

    def _split_mod(self, value):
        res = ''

        if value == '000':
            return ''
        if len(value) == 3:
            tr = value[:1]
            ch = value[1:2]
            dv = value[2:3]
            if tr == '0' and ch == '0':
                res = self._word(dv) + ' '
            if tr != '0' and ch == '0' and dv == '0':
                res = self._word(tr) + ' trăm '
            if tr != '0' and ch == '0' and dv != '0':
                res = self._word(tr) + ' trăm lẻ ' + self._word(dv) + ' '
            if tr == '0' and int(ch) > 1 and int(dv) > 0 and dv != '5':
                res = self._word(ch) + ' mươi ' + self._word(dv)
            if tr == '0' and int(ch) > 1 and dv == '0':
                res = self._word(ch) + ' mươi '
            if tr == '0' and int(ch) > 1 and dv == '5':
                res = self._word(ch) + ' mươi lăm '
            if tr == '0' and ch == '1' and int(dv) > 0 and dv != '5':
                res = ' mười ' + self._word(dv) + ' '
            if tr == '0' and ch == '1' and dv == '0':
                res = ' mười '
            if tr == '0' and ch == '1' and dv == '5':
                res = ' mười lăm '
            if int(tr) > 0 and int(ch) > 1 and int(dv) > 0 and dv != '5':
                res = self._word(tr) + ' trăm ' + self._word(ch) + ' mươi ' + self._word(dv) + ' '
            if int(tr) > 0 and int(ch) > 1 and dv == '0':
                res = self._word(tr) + ' trăm ' + self._word(ch) + ' mươi '
            if int(tr) > 0 and int(ch) > 1 and dv == '5':
                res = self._word(tr) + ' trăm ' + self._word(ch) + ' mươi lăm '
            if int(tr) > 0 and ch == '1' and int(dv) > 0 and dv != '5':
                res = self._word(tr) + ' trăm mười ' + self._word(dv) + ' '
            if int(tr) > 0 and ch == '1' and dv == '0':
                res = self._word(tr) + ' trăm mười '
            if int(tr) > 0 and ch == '1' and dv == '5':
                res = self._word(tr) + ' trăm mười lăm '

        return res

    def _split(self, value):
        res = ''

        if value == '000':
            return ''
        if len(value) == 3:
            tr = value[:1]
            ch = value[1:2]
            dv = value[2:3]
            if tr == '0' and ch == '0':
                res = ' không trăm lẻ ' + self._word(dv) + ' '
            if tr != '0' and ch == '0' and dv == '0':
                res = self._word(tr) + ' trăm '
            if tr != '0' and ch == '0' and dv != '0':
                res = self._word(tr) + ' trăm lẻ ' + self._word(dv) + ' '
            if tr == '0' and int(ch) > 1 and int(dv) > 0 and dv != '5':
                if int(dv) == 1:
                    res = ' không trăm ' + self._word(ch) + ' mươi mốt'
                else:
                    res = ' không trăm ' + self._word(ch) + ' mươi ' + self._word(dv)
            if tr == '0' and int(ch) > 1 and dv == '0':
                res = ' không trăm ' + self._word(ch) + ' mươi '
            if tr == '0' and int(ch) > 1 and dv == '5':
                res = ' không trăm ' + self._word(ch) + ' mươi lăm '
            if tr == '0' and ch == '1' and int(dv) > 0 and dv != '5':
                res = ' không trăm mười ' + self._word(dv)
            if tr == '0' and ch == '1' and dv == '0':
                res = ' không trăm mười '
            if tr == '0' and ch == '1' and dv == '5':
                res = ' không trăm mười lăm '
            if int(tr) > 0 and int(ch) > 1 and int(dv) > 0 and dv != '5':
                if int(dv) == 1:
                    res = self._word(tr) + ' trăm ' + self._word(ch) + ' mươi mốt'
                else:
                    res = self._word(tr) + ' trăm ' + self._word(ch) + ' mươi ' + self._word(dv) + ' '
            if int(tr) > 0 and int(ch) > 1 and dv == '0':
                res = self._word(tr) + ' trăm ' + self._word(ch) + ' mươi '
            if int(tr) > 0 and int(ch) > 1 and dv == '5':
                res = self._word(tr) + ' trăm ' + self._word(ch) + ' mươi lăm '
            if int(tr) > 0 and ch == '1' and int(dv) > 0 and dv != '5':
                res = self._word(tr) + ' trăm mười ' + self._word(dv) + ' '
            if int(tr) > 0 and ch == '1' and dv == '0':
                res = self._word(tr) + ' trăm mười '
            if int(tr) > 0 and ch == '1' and dv == '5':
                res = self._word(tr) + ' trăm mười lăm '

        return res

    def _num2word(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        for item in self.browse(cr, uid, ids, context=context):
            amount = item.amount
            if amount == 0:
                res[item.id] = 'Không'
                return res

            # delare
            in_word = ''
            split_mod = ''
            split_remain = ''
            num = int(amount)
            decimal = amount - num
            gnum = str(num)
            gdecimal = str(decimal)[2:]
            m = int(len(gnum) / 3)
            mod = len(gnum) - m * 3
            sign = '[+]'

            # sign
            if amount < 0:
                sign = '[-]'
            else:
                sign = ''

            # tách hàng lớn nhất
            if mod == 1:
                split_mod = '00' + str(num)[:1]
            elif mod == 2:
                split_mod = '0' + str(num)[:2]
            elif mod == 0:
                split_mod = '000'
            # tách hàng còn lại sau mod
            if len(str(num)) > 2:
                split_remain = str(num)[mod:]
            # đơn vị hàng mod
            im = m + 1
            if mod > 0:
                in_word = self._split_mod(split_mod) + ' ' + self._unit(str(im))
            # tách 3 trong split_remain
            i = m
            _m = m
            j = 1
            split3 = ''
            split3_ = ''
            while i > 0:
                split3 = split_remain[:3]
                split3_ = split3
                in_word = in_word + ' ' + self._split(split3)
                m = _m + 1 - j
                if int(split3_) != 0:
                    in_word = in_word + ' ' + self._unit(str(m))
                split_remain = split_remain[3:]
                i = i - 1
                j = j + 1
            if in_word[:1] == 'k':
                in_word = in_word[10:]
            if in_word[:1] == 'l':
                in_word = in_word[2:]
            if len(in_word) > 0:
                in_word = sign + ' ' + str(in_word.strip()[:1]).upper() + in_word.strip()[1:]

            if decimal > 0:
                in_word += ' phẩy'
                for i in range(0, len(gdecimal)):
                    in_word += ' ' + self._word(gdecimal[i])

        res[item.id] = in_word
        return res

    def _get_decision_type(self, cr, uid, ids, field_name, arg, context=None):
        res = {}

        decision_type = ''
        module_obj = self.pool.get('ir.module.module')
        module_ids = module_obj.search(cr, uid, [('name', '=', 'tvtma_l10n_vn_48')], context=context)
        for module in module_obj.browse(cr, uid, module_ids, context):
            if module.state == 'installed':
                decision_type = '48'
            else:
                decision_type = '15'
        for item in self.browse(cr, uid, ids, context=context):
            res[item.id] = decision_type

        return res

    def _get_date(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for item in self.browse(cr, uid, ids, context=context):
            res[item.id] = self.browse(cr, uid, ids, context=context).date[8:10]
        return res

    def _get_month(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for item in self.browse(cr, uid, ids, context=context):
            res[item.id] = self.browse(cr, uid, ids, context=context).date[5:7]
        return res

    def _get_year(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for item in self.browse(cr, uid, ids, context=context):
            res[item.id] = self.browse(cr, uid, ids, context=context).date[0:4]
        return res

    def _num2word_with_tax(self):
        for item in self:
            rouding_company = self.env.user.company_id.currency_id.decimal_places
            amount = round(item.amount, rouding_company)
            # amount = item.amount
            if amount == 0:
                return 'Không'
                # return res

            # delare
            in_word = ''
            split_mod = ''
            split_remain = ''
            num = int(amount)
            decimal = amount - num
            decimal = round(decimal, rouding_company)
            gnum = str(num)
            gdecimal = str(decimal)[2:]
            m = int(len(gnum) / 3)
            mod = len(gnum) - m * 3
            sign = '[+]'

            # sign
            if amount < 0:
                sign = '[-]'
            else:
                sign = ''

            # tách hàng lớn nhất
            if mod == 1:
                split_mod = '00' + str(num)[:1]
            elif mod == 2:
                split_mod = '0' + str(num)[:2]
            elif mod == 0:
                split_mod = '000'
            # tách hàng còn lại sau mod
            if len(str(num)) > 2:
                split_remain = str(num)[mod:]
            # đơn vị hàng mod
            im = m + 1
            if mod > 0:
                in_word = self._split_mod(split_mod) + ' ' + self._unit(str(im))
            # tách 3 trong split_remain
            i = m
            _m = m
            j = 1
            split3 = ''
            split3_ = ''
            while i > 0:
                split3 = split_remain[:3]
                split3_ = split3
                in_word = in_word + ' ' + self._split(split3)
                m = _m + 1 - j
                if int(split3_) != 0:
                    in_word = in_word + ' ' + self._unit(str(m))
                split_remain = split_remain[3:]
                i = i - 1
                j = j + 1
            if in_word[:1] == 'k':
                in_word = in_word[10:]
            if in_word[:1] == 'l':
                in_word = in_word[2:]
            if len(in_word) > 0:
                in_word = sign + ' ' + str(in_word.strip()[:1]).upper() + in_word.strip()[1:]

            if decimal > 0:
                in_word += ' phẩy'
                for i in range(0, len(gdecimal)):
                    in_word += ' ' + self._word(gdecimal[i])

        return in_word

    def _num2word_with_tax_pay(self, obj):
        for item in obj:
            rouding_company = self.env.user.company_id.currency_id.decimal_places
            amount = round(item.amount, rouding_company)
            if amount == 0:
                res[item.id] = 'Không'
                return res

            in_word = ''
            split_mod = ''
            split_remain = ''
            num = int(amount)
            decimal = amount - num
            decimal = round(decimal,rouding_company)
            gnum = str(num)
            gdecimal = str(decimal)[2:]
            m = int(len(gnum) / 3)
            mod = len(gnum) - m * 3
            sign = '[+]'
            if amount < 0:
                sign = '[-]'
            else:
                sign = ''
            if mod == 1:
                split_mod = '00' + str(num)[:1]
            elif mod == 2:
                split_mod = '0' + str(num)[:2]
            elif mod == 0:
                split_mod = '000'
            if len(str(num)) > 2:
                split_remain = str(num)[mod:]
            im = m + 1
            if mod > 0:
                in_word = self._split_mod(split_mod) + ' ' + self._unit(str(im))
            i = m
            _m = m
            j = 1
            split3 = ''
            split3_ = ''
            while i > 0:
                split3 = split_remain[:3]
                split3_ = split3
                in_word = in_word + ' ' + self._split(split3)
                m = _m + 1 - j
                if int(split3_) != 0:
                    in_word = in_word + ' ' + self._unit(str(m))
                split_remain = split_remain[3:]
                i = i - 1
                j = j + 1
            if in_word[:1] == 'k':
                in_word = in_word[10:]
            if in_word[:1] == 'l':
                in_word = in_word[2:]
            if len(in_word) > 0:
                in_word = sign + ' ' + str(in_word.strip()[:1]).upper() + in_word.strip()[1:]

            if decimal > 0:
                in_word += ' phẩy'
                for i in range(0, len(gdecimal)):
                    in_word += ' ' + self._word(gdecimal[i])

        return in_word

    def _get_quyen_so(self, number):
        if number:
            if number.count('/') >=2 and ('PT' in number or 'PC' in number):
                return number.split('/', 1)[1]
            return '..............'
        return '..............'

    def get_time_dotay(self):
        for r in self:
            if r.date:
                return (r.date[8:10]) + '/' + (r.date[5:7]) + '/' + (r.date[0:4])
            else:
                return " "

    def get_rate(self):
        for r in self:
            if r.company_id.currency_id.rate:
                return r.company_id.currency_id.rate
            else:
                return 0

    def _get_account(self):
        accounts = {}
        if not self.line_ids:
            return []
        lst = [(line.account_id.code, line.price_subtotal) for line in self.line_ids]
        for k, v in lst:
            if k in accounts:
                accounts[k] += v
            else:
                accounts[k] = v
        accounts = accounts.items()
        return accounts

    text_date = fields.Char(compute=_get_date)
    text_month = fields.Char(compute=_get_month)
    text_year = fields.Char(compute=_get_year)