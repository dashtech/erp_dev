# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
  "name"                 :  "POS Loyalty & Rewards Program",
  "summary"              :  "Provide loyalty points on every purchase to your customers with some redemption benefits in Point Of Sale.",
  "category"             :  "Point Of Sale",
  "version"              :  "1.2.1",
  "author"               :  "Webkul Software Pvt. Ltd.",
  "license"              :  "Other proprietary",
  "website"              :  "https://store.webkul.com/OpenERP-POS-Loyalty-Management.html",
  "description"          :  """http://webkul.com/blog/odoo-pos-loyalty-management/""",
  "live_test_url"        :  "http://odoodemo.webkul.com/?module=pos_loyalty_management&version=10.0",
  "depends"              :  [
                             'point_of_sale',
                             'wk_wizard_messages',
                            ],
  "data"                 :  [
                             'security/ir.model.access.csv',
                             'data/ir_sequence_data.xml',
                             'data/product.xml',
                             'views/pos_loyalty_management_view.xml',
                             'views/pos_loyalty_history_view.xml',
                             'views/templates.xml',
                            ],
  "qweb"                 :  ['static/src/xml/pos_loyalty.xml'],
  "images"               :  ['static/description/Banner.png'],
  "active"               :  False,
  "installable"          :  True,
  "auto_install"         :  False,
  "price"                :  99,
  "currency"             :  "EUR",
  "pre_init_hook"        :  "pre_init_check",
}