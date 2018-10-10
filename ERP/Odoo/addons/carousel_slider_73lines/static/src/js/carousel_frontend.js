/*
    Part of Odoo Module Developed by 73lines
    See LICENSE file for full copyright and licensing details.
*/
odoo.define('carousel_slider_73lines.carousel_frontend', function(require) {
    "use strict";

    var ajax = require('web.ajax');
    var core = require('web.core');
    var animation = require('web_editor.snippets.animation');
    var website = require('website.website');

    var _t = core._t;
    var qweb = core.qweb;

    animation.registry.js_get_objects = animation.Class.extend({
        selector: ".js_get_objects",

        start: function() {
            this.redraw();
        },

        stop: function() {
            this.clean();
        },

        redraw: function(debug) {
            this.clean(debug);
            this.build(debug);
        },

        clean: function(debug) {
            this.$target.empty();
        },

        apply_carousel: function(debug) {
            var self = this;
            var carouselCount = 0;
            $(".owl-carousel").owlCarousel({
                loop: false,
                dots: false,
                nav: true,
                pagination: false,
                autoplay: false,
                margin: 20,
                navText: ['<button id="owl-prv" class="btn btn-primary fa fa-angle-left" data-toggle="tooltip" title="Prev"/>',
                          '<button id="owl-nxt" class="btn btn-primary fa fa-angle-right" data-toggle="tooltip" title="Next"/>'],
                responsiveClass: true,
                responsive: {
                    768: {
                        items: 2
                    },
                    979: {
                        items : 2
                    },
                    479: {
                        items : 1
                    },
                    320: {
                        items : 1
                    },
                    1199: {
                        items : self.$target.data("objects_in_slide")
                    },
                },
            });
        },

        build: function(debug) {
            var self = this,
                limit = self.$target.data("objects_limit"),
                in_row = self.$target.data("objects_in_row"),
                filter_id = self.$target.data("filter_by_filter_id"),
                objects_in_slide = self.$target.data("objects_in_slide"),
                object_name = self.$target.data("object_name"),
                template = self.$target.data("template");

            self.$target.attr("contentEditable", false);

            if (! objects_in_slide) {
                objects_in_slide = 3;
            }
            if (! limit) {
                limit = 6;
            }
            if (! in_row) {
                in_row = 1;
            }
            var rpc_end_point = '/carousel_slider/render/' + object_name;

            ajax.jsonRpc(rpc_end_point, 'call', {
                'template' : template,
                'filter_id' : filter_id,
                'objects_in_slide' : objects_in_slide,
                'limit' : limit,
                'object_name' : object_name,
                'in_row' : in_row,
            }).then(function(objects) {
                $(objects).appendTo(self.$target);
                self.apply_carousel(objects);
            }).then(function() {
                self.loading(debug);
            }).fail(function(e) {
                return;
            });
        },

        loading: function(debug) {
            // function to hook things up after build
        }

    });

});
