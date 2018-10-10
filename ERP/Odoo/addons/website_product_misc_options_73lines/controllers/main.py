# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by 73lines
# See LICENSE file for full copyright and licensing details.

from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale.controllers.main import TableCompute
from odoo.addons.website.models.website import slug

PPG = 20  # Products Per Page
PPR = 4  # Products Per Row


class WebsiteProductLimit(http.Controller):

    @http.route(['/shop/product_limit'], type='json', auth="public")
    def change_limit(self, value):
        global PPG
        PPG = int(value)
        return True


class WebsiteSaleExt(WebsiteSale):

    def _get_search_domain_ext(self, search, category, attrib_values,
                               tag_values, brand_values, price_min, price_max):
        domain = request.website.sale_product_domain()

        if search:
            for srch in search.split(" "):
                domain += [
                    '|', '|', '|', ('name', 'ilike', srch),
                    ('description', 'ilike', srch),
                    ('description_sale', 'ilike', srch),
                    ('product_variant_ids.default_code', 'ilike', srch)]

        if category:
            domain += [('public_categ_ids', 'child_of', int(category))]

        if attrib_values:
            attrib = None
            ids = []
            for value in attrib_values:
                if not attrib:
                    attrib = value[0]
                    ids.append(value[1])
                elif value[0] == attrib:
                    ids.append(value[1])
                else:
                    domain += [('attribute_line_ids.value_ids', 'in', ids)]
                    attrib = value[0]
                    ids = [value[1]]
            if attrib:
                domain += [('attribute_line_ids.value_ids', 'in', ids)]

        if tag_values:
            domain += [('tag_ids', 'in', tag_values)]

        if brand_values:
            domain += [('brand_id', 'in', brand_values)]

        if price_min or price_max:
            domain += [('list_price', '>=', price_min),
                       ('list_price', '<=', price_max)]

        return domain

    @http.route()
    def shop(self, page=0, category=None, search='', ppg=False, **post):

        if ppg:
            try:
                ppg = int(ppg)
            except ValueError:
                ppg = PPG
            post["ppg"] = ppg
        else:
            ppg = PPG

        # For Attributes
        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [map(int, v.split("-")) for v in attrib_list if v]
        attributes_ids = set([v[0] for v in attrib_values])
        attrib_set = set([v[1] for v in attrib_values])

        # For Tags
        tag_list = request.httprequest.args.getlist('tags')
        tag_values = [map(str, v.split("-")) for v in tag_list if v]
        tag_set = set([int(v[1]) for v in tag_values])

        # For Brands
        brand_list = request.httprequest.args.getlist('brands')
        brand_values = [map(str, v.split("-")) for v in brand_list if v]
        brand_set = set([int(v[1]) for v in brand_values])

        Product = request.env['product.template']

        # Price Filter Condition
        categ_products = None
        if category:
            categ_products = Product.search([
                ('website_published', '=', True),
                ('public_categ_ids', 'child_of', category.id)])
            if categ_products:
                products_price = [product.website_price
                                  for product in categ_products]
                products_price.sort()
                price_min_range = products_price and products_price[0]
                price_max_range = products_price and products_price[-1]

                if request.httprequest.args.getlist('price_min') \
                        and request.httprequest.args.getlist(
                            'price_min')[0] != '':
                    price_min = float(request.httprequest.args.getlist(
                        'price_min')[0])
                else:
                    price_min = float(price_min_range)

                if request.httprequest.args.getlist('price_max') \
                        and request.httprequest.args.getlist(
                            'price_max')[0] != '':
                    price_max = float(request.httprequest.args.getlist(
                        'price_max')[0])
                else:
                    price_max = float(price_max_range)
            else:
                price_max = price_min = price_min_range = price_max_range = 0.0
        else:
            price_max = price_min = price_min_range = price_max_range = 0.0

        domain = self._get_search_domain_ext(search, category, attrib_values,
                                             list(tag_set), list(brand_set),
                                             price_min, price_max)
        keep = QueryURL('/shop', category=category and int(category),
                        search=search, attrib=attrib_list,
                        order=post.get('order'), brands=brand_list,
                        tags=tag_list, price_min=price_min,
                        price_max=price_max)

        url = "/shop"
        if category:
            category = request.env['product.public.category'].browse(
                int(category))
            url = "/shop/category/%s" % slug(category)
        if attrib_list:
            post['attrib'] = attrib_list
        if tag_list:
            post['tags'] = tag_list
        if brand_list:
            post['brands'] = brand_list

        product_count = Product.search_count(domain)
        pager = request.website.pager(url=url, total=product_count,
                                      page=page, step=ppg, scope=7,
                                      url_args=post)
        products = Product.search(domain, limit=ppg, offset=pager['offset'],
                                  order=self._get_search_order(post))

        ProductAttribute = request.env['product.attribute']
        if products:
            attributes = ProductAttribute.search(
                [('attribute_line_ids.product_tmpl_id', 'in', products.ids)])
        else:
            attributes = ProductAttribute.browse(attributes_ids)

        limits = request.env['product.view.limit'].search([])

        # @todo
        # (Future Dev) Make tags & brands like attributes,
        # If used then shows in website otherwise hide it
        tags = request.env['product.tags'].search([])
        brands = request.env['product.brand'].search([])

        res = super(WebsiteSaleExt, self).shop(page=page, category=category,
                                               search=search, ppg=ppg, **post)

        res.qcontext.update({
            'pager': pager, 'products': products, 'tags': tags,
            'brands': brands, 'bins': TableCompute().process(products, ppg),
            'attributes': attributes, 'search_count': product_count,
            'attrib_values': attrib_values, 'tag_values': tag_values,
            'brand_values': brand_values, 'brand_set': brand_set,
            'attrib_set': attrib_set, 'tag_set': tag_set, 'limits': limits,
            'PPG': PPG, 'price_min_range': price_min_range,
            'price_max_range': price_max_range, 'price_min': price_min,
            'price_max': price_max, 'keep': keep,
            'categ_products': categ_products,
        })
        return res

    @http.route()
    def product(self, product, category='', search='', **kwargs):
        ProductCategory = request.env['product.public.category']
        if category:
            category = ProductCategory.browse(int(category)).exists()

        # For Attributes
        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [map(int, v.split("-")) for v in attrib_list if v]
        attrib_set = set([v[1] for v in attrib_values])

        # For Tags
        tag_list = request.httprequest.args.getlist('tags')
        tag_values = [map(str, v.split("-")) for v in tag_list if v]
        tag_set = set([int(v[1]) for v in tag_values])

        # For Brands
        brand_list = request.httprequest.args.getlist('brands')
        brand_values = [map(str, v.split("-")) for v in brand_list if v]
        brand_set = set([int(v[1]) for v in brand_values])

        if request.httprequest.args.getlist('price_min') \
                and request.httprequest.args.getlist('price_min')[0] != '':
            price_min = float(request.httprequest.args.getlist('price_min')[0])
        else:
            price_min = False

        if request.httprequest.args.getlist('price_max') \
                and request.httprequest.args.getlist('price_max')[0] != '':
            price_max = float(request.httprequest.args.getlist('price_max')[0])
        else:
            price_max = False

        keep = QueryURL('/shop', category=category and category.id,
                        search=search, attrib=attrib_list,
                        brands=brand_list, tags=tag_list, price_min=price_min,
                        price_max=price_max)

        res = super(WebsiteSaleExt, self).product(product=product,
                                                  category=category,
                                                  search=search, **kwargs)

        res.qcontext.update({
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'tag_values': tag_values,
            'tag_set': tag_set,
            'brand_values': brand_values,
            'brand_set': brand_set,
            'keep': keep,
            'price_min': price_min,
            'price_max': price_max,
        })
        return res
