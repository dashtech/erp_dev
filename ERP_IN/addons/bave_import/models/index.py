# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class HomeImport(models.Model):
    _name = 'home.import'

    name =fields.Char(default=_('User Guide'))
    index = fields.Html(compute='default_index', readonly=0, )


    def default_index(self):
        index = u'''
<table>
    <tr>
        <td style="width: 15%"/>
        <td ttyle="width: 70%;">
            <span style="text-align: center; color: blue;">
                <h1>HƯỚNG DẪN NHẬP DỮ LIỆU VÀO HỆ THỐNG</h1>
            </span></br>
            <span style="text-align: center; color: blue;">
                <h3>Đường dẫn: Menu => Nhập dữ liệu</h3></span>
            <br/>   
            <span style="color: blue;"><h4><b>Bước 1: Chọn menu cần nhập dữ liệu import</b></h4></span>
            <span>VD: Nhập Tài khoản kế toán <br/>
                <img src="bave_import/static/src/img/b1.png"/>
            </span>
            <br> <br/>
            <span>
                <p>
                <h4 style="color: blue;"><b>Bước 2: Kích vào link mẫu để tải file mẫu về</b></h4>
                <img src="bave_import/static/src/img/b2.png"/></p>
            </span>
            <br> <br/>
            <span>
                <p>
                <h4 style="color: blue;"><b>Bước 3: Nhập các trường thông tin có trong file và lưu file</b></h4>
                <img src="bave_import/static/src/img/b3.png"/></p>
            </span>
            <br> <br/>
            <span>
            <br/>
                <p>
                <h4 style="color: blue;"><b>Bước 4: Tải file lên hệ thống</b></h4>
                <img src="bave_import/static/src/img/b4.png"/></p>
                <p>
                <br> <br/>                
                <h5><b>Màn hình hiện ra => chọn file cần tải</b></h5><br/>
                <img src="bave_import/static/src/img/b41.png" width="650px" height="250px"/></p>
                <br/>
                <p>
                <br> <br/>                
                <b>Sau khi tải file thành công nhấn nút</b><br/>
                <img src="bave_import/static/src/img/b42.png"/></p>
            </span><br/><br/>
            <span style="text-align: center; color: blue;">
                <h2>CHÚC CÁC BẠN THÀNH CÔNG!</h1>
            </span>
        </td>
        <td style="width: 5%"/>
    </tr>
</table>
        '''
        for s in self:
            s.index = index