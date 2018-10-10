# -*- coding: utf-8 -*-
from odoo import models, fields, api
import math


class ReadNumber(models.Model):
    _name = 'read.number'

    mangso = [u'không', u'một', u'hai', u'ba', u'bốn', u'năm', u'sáu', u'bảy',
          u'tám', u'chín']

    def dochangchuc(self, so, daydu, mangso=mangso):
        chuoi = ""
        chuc = so / 10;
        donvi = so % 10;
        if (chuc > 1):
            chuoi = " " + mangso[chuc] + u" mươi"
            if (donvi == 1):
                chuoi += u" mốt"
        elif (chuc == 1):
            chuoi = u" mười";
            if (donvi == 1):
                chuoi += u" một";
        elif (daydu and donvi > 0):
            chuoi = u" lẻ"

        if (donvi == 5 and chuc > 1):
            chuoi += u" lăm"
        elif (donvi > 1 or (donvi == 1 and chuc == 0)):
            chuoi += " " + mangso[donvi]
        return chuoi

    def docblock(self, so, daydu, mangso=mangso):
        chuoi = ""
        tram = so / 100;
        so = so % 100;
        if (daydu or tram > 0):
            chuoi = " " + mangso[tram] + u" trăm"
            chuoi += self.dochangchuc(so, True)
        else:
            chuoi = self.dochangchuc(so, False)
        return chuoi

    def dochangtrieu(self, so, daydu, mangso=mangso):
        chuoi = ""
        trieu = so / 1000000
        so = so % 1000000
        if (trieu > 0):
            chuoi = self.docblock(trieu, daydu) + u" triệu"
            daydu = True
        nghin = so / 1000
        so = so % 1000
        if (nghin > 0):
            chuoi += self.docblock(nghin, daydu) + u" nghìn"
            daydu = True
        if (so > 0):
            chuoi += self.docblock(so, daydu)
        return chuoi

    def docso(self, so, mangso=mangso):
        # frac, whole = math.modf(2.5)
        # frac sau thap phan
        if (so == 0):
            return mangso[0]
        prefix = u''
        if so < 0:
            prefix = u'Âm '
            so = abs(so)
        chuoi = ""
        hauto = ""
        ty = 0
        while so > 0:
            ty = so % 1000000000
            so = so / 1000000000
            if so > 0:
                chuoi = self.dochangtrieu(ty, True) + hauto + chuoi
            else:
                chuoi = self.dochangtrieu(ty, False) + hauto + chuoi
            hauto = u" tỷ"
        if chuoi[0] == ' ':
            chuoi = chuoi[1:]
        chuoi = prefix + chuoi.capitalize()
        return chuoi

    # def get_num2text(self, so):
    #     pre = int(str(so).split('.')[0])
    #     text_pre = self.docso(pre)
    #     # res = text_pre
    #     if len(str(so).split('.')) > 1:
    #         behind = int(str(so).split('.')[1])
    #         if behind > 0:
    #             text_behind = self.docso(behind)
    #             res = text_pre + u' phẩy ' + text_behind
    #             return res
    #     return text_pre