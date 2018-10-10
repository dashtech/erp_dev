# -*- coding: utf-8 -*-
# Part of Odoo Module Developed by 73lines
# See LICENSE file for full copyright and licensing details.

{
    'name': 'Theme Home Store',
    'description': 'Theme Home Store By 73Lines',
    'category': 'Theme/Ecommerce',
    'version': "10.0.1.0.1",
    'author': "73Lines",
    'depends': [
        # Default Modules
        'mass_mailing',
        'website',
        # 73lines Depend Modules
        # Don't forget to see README file in order to how to install
        # In order to install complete theme, uncomment the following .
        # Dependent modules are supplied in a zip file along with the theme,
        # if you have not received it,please contact us at
        # enquiry@73lines.com with proof of your purchase.
#        ###############################################################
       'carousel_slider_73lines',
       'snippet_blog_carousel_73lines',
       'snippet_product_brand_carousel_73lines',
       'snippet_product_carousel_73lines',
       'snippet_product_category_carousel_73lines',
       'website_header_layout_73lines',
       'website_language_flag_73lines',
       'website_product_categ_menu_and_banner_73lines',
       'website_product_misc_options_73lines',
       'website_product_page_layout_73lines',
       'website_product_ribbon_73lines',
       'website_product_share_options_73lines',
       'website_user_wishlist_73lines',
       'website_product_ribbon_73lines',
       'website_mega_menu_73lines',
       'website_customize_model_73lines',
       'website_product_comparison_73lines',
       'website_product_quick_view_73lines',
#        ###############################################################
    ],
    'data': [
        # Snippets
        'snippets/snippet_contact_us.xml',
        'snippets/snippet_four_image.xml',
        'snippets/snippet_happy_customer_count.xml',
        'snippets/snippet_home_banner.xml',
        'snippets/snippet_one_image.xml',
        'snippets/snippet_sale_timer.xml',
        'snippets/snippet_footer.xml',
        # templates
        'views/assets.xml',
        'views/s_product_carousel.xml',
        'views/s_mid_header.xml',
        'views/s_accordion_category.xml',
        'views/s_product_view.xml',
        'views/single_product_template.xml',
        'views/customize_model.xml',
    ],
    'demo': [
        'data/template_home_page.xml',
        'data/brand_demo.xml',
        'data/blog_post_demo.xml',
        'data/footer.xml',
        'data/menu_data.xml',
    ],
    'images': [
        'static/description/homestore-banner.png',
    ],
    'price': 200,
    'license': 'OPL-1',
    'currency': 'EUR',
    'live_test_url': 'https://www.73lines.com/r/v7J'
}
