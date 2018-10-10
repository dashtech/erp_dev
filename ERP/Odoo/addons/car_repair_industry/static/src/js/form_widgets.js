odoo.define('car_repair_industry.car_repair', function (require) {

    var bus = require('bus.bus').bus;
    var core = require('web.core');
    var data = require('web.data');
    var common = require('web.form_common');
    var Model = require('web.DataModel');
    var Dialog = require('web.Dialog');
    var FieldMany2ManyTags = core.form_widget_registry.get('many2many_tags');
    var FieldMany2One = core.form_widget_registry.get('many2one');
    var CrashManager = require('web.CrashManager');

    var form_common = require('web.form_common');
    var form_relational = require('web.form_relational');

    var _t = core._t;
    var QWeb = core.qweb;

    CrashManager.include({
        show_warning: function(error) {
            if (!this.active) {
                return;
            }
            new Dialog(this, {
                size: 'medium',
                title: "Agara " + (_.str.capitalize(error.type) || _t("Warning")),
                subtitle: error.data.title,
                $content: $('<div>').html(QWeb.render('CrashManager.warning', {error: error}))
            }).open();
        },
        show_error: function(error) {
            if (!this.active) {
                return;
            }
            new Dialog(this, {
                title: "Agara " + _.str.capitalize(error.type),
                $content: QWeb.render('CrashManager.error', {error: error})
            }).open();
        },
    });

    Dialog.include({
        init: function (parent, options) {
            this._super(parent);
            this._opened = $.Deferred();

            options = _.defaults(options || {}, {
                title: _t('Agara'), subtitle: '',
                size: 'large',
                dialogClass: '',
                $content: false,
                buttons: [{text: _t("Ok"), close: true}]
            });

            this.$content = options.$content;

            this.title = options.title;
            this.subtitle = options.subtitle;
            this.$modal = $(QWeb.render('Dialog', {title: this.title, subtitle: this.subtitle}));

            switch(options.size) {
                case 'large':
                    this.$modal.find('.modal-dialog').addClass('modal-lg');
                    break;
                case 'small':
                    this.$modal.find('.modal-dialog').addClass('modal-sm');
                    break;
            }

            this.dialogClass = options.dialogClass;
            this.$footer = this.$modal.find(".modal-footer");

            this.set_buttons(options.buttons);

            this.$modal.on('hidden.bs.modal', _.bind(this.destroy, this));
        },
    });

    var MyKanban = common.AbstractField.extend(common.ReinitializeFieldMixin, {
        template: "Nothing",
        init: function (field_manager, node) {
            this._super(field_manager, node);
            this.data = [];
            this.data_store = {};
            this.isInit = true;
            this.page = 0;
            this.offset = 0;
            this.limit = 80;
            this.page_label = "";
            this._length = 0;
            this.domain = [];
            this.model = new Model('sale.order');
            this.category = [];
            this.category_id = 0;
            this.category_value = "---Select an Item---";
        },
        start: function() {
            this._super.apply(this, arguments);
            this.onLoadData();

            //  bus.on('notification', null, function (notifications){
            //     _.each(notifications, function (notification) {
            //         var model = notification[0][1];
            //         if (model === 'hr.holidays.message'){
            //             alert("anc")
            //         }
            //     });
            // });
        },
        calPage: function () {
            this.offset = this.limit * this.page;
        },
        getProCategory: function () {
            var self = this;
            return this.model.call('get_product_category', []).then(function (result) {
                self.category = [{id: 0, name: "---Select an Item---"}].concat(result);
            });
        },
        getProduct: function () {
            var self = this;
            self.calPage();
            this.model.call('get_product', [[self.field_manager.datarecord.id], self.domain, self.category_id, self.offset, self.limit]
            ).then(
                function (result) {
                    self.data = result['data'];
                    self.data_store = result['data_store'];
                    self._length = result['length'];
                    self.isInit = false;
                    self.offset = self.offset + self.data.length;
                    self.page_label = self.offset + " of " + self._length;
                    if (self.data.length < self.limit) {
                        self.page = -1;
                    }
                    var $items = $(QWeb.render('MyKanBan', {widget: self}));
                    self.replaceElement($items);
                    self.view.$el.find(".oknhehihi").parent().css({width: "100%"});
                    return result;
            }).then(
                function (result) {
                    self.onFilter();
                    self.onSearch();
                    self.onPage();
                    self.createProduct();
                    self.orderProduct();
            });
        },
        onSearch: function () {
            var self = this;
            this.$el.on('click', '.search-ok', function () {
                var data = self.$el.find('.input-search-ok').val();
                self.page = 0;
                self.domain = ['|', ['name', 'ilike', data], ['default_code', 'ilike', data]];
                self.getProduct();
            });
        },
        nextPage: function () {
            var self = this;
            this.$el.find('.next-ok').click(function () {
                 self.page += 1;
                 self.getProduct();
            });
        },
        prevPage: function () {
            var self = this;
            this.$el.find('.previous-ok').click(function () {
                if (self.page >= 1){
                    self.page -= 1;
                    self.getProduct();
                }
            });
        },
        onPage: function () {
            this.nextPage();
            this.prevPage();
        },
        createProduct: function () {
            var self = this;
            this.$el.find('.create_product').click(function () {
                var value = self.data_store[$(this).attr("data")];
                value.name = value.name;
                new Model('product.template').call("create", [value]).then(function (result) {
                    if (result){
                        alert("Thanh Cong!");
                    }else{
                        alert("That Bai!")
                    }
                });
            });
        },
        onOrderProduct: function (data) {
            var fields = this.view_form.fields;
            var val = {product_id: parseInt(data)};
            Object.keys(fields).map(function (k) {
               val[k] = fields[k].get_value();
            });
            new Model("bave.order").call("order_product", [val]).then(function (result) {
                if (result){
                    alert("Thanh Cong!");
                }else{
                    alert("That Bai!");
                }
            });
        },
        orderProduct: function () {
            var self = this;
            this.$el.find('.order_product').click(function () {
                var content = $(QWeb.render('OrderProduct', {widget: self}));
                var data = $(this).attr("data");
                this.dialog = new common.FormViewDialog(self, {
                    res_model: 'bave.order',
                    title: _t("Dat Hang"),
                    size: "medium",
                    buttons: [
                        {text: _t("Order"), classes: 'btn-primary', close: true,
                            click: function () {
                              self.onOrderProduct.bind(this)(data);
                            }
                        },
                    ],
                }).open();
                //
                // var dialog = new Dialog(self,
                //     {
                //         title: _t("Dat Hang"),
                //         buttons: [
                //             {text: _t("Order"), classes: 'btn-primary', close: true,
                //                 click: function () {
                //                     self.onOrderProduct();
                //                 }},
                //             {text: _t("Discard"), close: true}
                //         ],
                //         $content: content,
                // }).open();
             });
        },
        onFilter: function () {
            var self = this;
            this.$el.on('click', '.btn-select', function (e) {
                e.preventDefault();
                var ul = $(this).find("ul");
                if ($(this).hasClass("active")) {
                    if (ul.find("li").is(e.target)) {
                        var target = $(e.target);
                        self.category_id = e.target.value;
                        target.addClass("selected").siblings().removeClass("selected");
                        var value = target.html();
                        self.category_value = value;
                        self.page = 0;
                        self.getProduct();
                    }
                    ul.hide();
                    $(this).removeClass("active");
                }
                else {
                    $('.btn-select').not(this).each(function () {
                        $(this).removeClass("active").find("ul").hide();
                    });
                    ul.slideDown(300);
                    $(this).addClass("active");
                }
            });
        },
        onLoadData: function () {
            var self = this;
            this.view.$el.find("[mydata='car_repair']").click(function () {
                if (self.isInit){
                    self.getProCategory().then(function () {
                        self.getProduct();
                    });
                }
            });
        },
        get_value: function () {
            return "";
        },
        commit_value: function () {
            this.store_dom_value();
            return this._super();
        },
        store_dom_value: function () {
            this.internal_set_value(this.get_value());
        },
    });


    var MyWidget = common.AbstractField.extend(common.ReinitializeFieldMixin, {
        template: 'FieldOK',
        init: function (field_manager, node) {
            var sef = this;
            this._super(field_manager, node);
            var pages = [];
            this.pages = pages;
        },
        set_value: function(value_) {
            this._super(value_);
        },
        get_data_by_type: function (_type) {

        },
        get_value: function () {
            var self = this;
            for (var i=0; i<this.pages.length; i++) {
                var page = this.pages[i];
                for (var j=0; j<page.group.length; j++){
                    for (var l=0; l<page.group[j].length; l++){
                        var questions = page.group[j][l].question;
                        for (var k=0; k<questions.length; k++){
                            var question = questions[k];
                            switch (question.type){
                                case "matrix_input":
                                    var label_2 = question['labels_2'];
                                    for (var m=0; m<label_2.length; m++){
                                        var label = label_2[m];
                                        label.value_input = self.$el.find("[data='"+label.id+"']").val();
                                        label.value_radio = self.$el.find("input[name='"+label.id+"']:checked").val();
                                    }
                                    break;
                                case "matrix":
                                    var label_2 = question['labels_2'];
                                    for (var m=0; m<label_2.length; m++){
                                        var label = label_2[m];
                                        label.value_input = self.$el.find("[data='"+label.id+"']").val();
                                        label.value_radio = self.$el.find("input[name='"+label.id+"']:checked").val();
                                    }
                                    break;
                                case "textbox":
                                    question.value = self.$el.find("[data='"+question.id+"']").val();
                                    break;
                                case "free_text":
                                    question.value = self.$el.find("[data='"+question.id+"']").val().trim();
                                    break;
                                case "datetime":
                                    question.value = self.$el.find("[data='"+question.id+"']").val();
                                    break;
                                case "simple_choice":
                                    question.value = self.$el.find("[data='"+question.id+"']").val();
                                    break;
                                case "multiple_choice":
                                    question.value = self.$el.find("[data='"+question.id+"']").val();
                                    break;
                                default:
                                    break;
                            }

                        }
                    }
                }
            }
            return JSON.stringify(this.pages);
        },
        commit_value: function () {
            this.store_dom_value();
            return this._super();
        },
        store_dom_value: function () {
            this.internal_set_value(this.get_value());
        },
        render_value: function () {
            var value = this.get_value();
            var self = this;
            var _id = self.view.datarecord.id;
            new Model('survey.survey').call('search_ok', [_id]).then(function (result) {
                if (typeof result === 'string'){
                    result = JSON.parse(result);
                }
                self.pages = result;
                var $items = $(QWeb.render('FieldOK', {widget: self}));
                self.field_manager.$el.find(".car_auto_page").css({width: "100%"});
                self.field_manager.$el.find(".car_auto_page").removeClass("o_form_field_empty");

                var pageid_to_display = $items.find('div[role="tabpanel"]:not(.o_form_invisible):first').attr('id');

                $items.find('a[href=#' + pageid_to_display + ']').parent().addClass('active');
                $items.find('#' + pageid_to_display).addClass('active');

                self.$el.html($items)
                return true
            });
        }
    });

    // FieldMany2ManyTags.include({
        // events: {
        //     "click .o_badge_text": "on_show_detail",
        // },
        // init: function(field_manager, node) {
        //     this._super(field_manager, node);
        //     this.data_ids = [];
        //     if (this.field.context.no) {
        //         this.options['no_close'] = true;
        //     }
        // },
        // add_id: function(id) {
        //     if (this.field.context.no) {
        //         this.data_ids.push(id);
        //         this.view.fields.listen_search.set_value(JSON.stringify({data: this.data_ids}));
        //     }else{
        //         this._super(id);
        //     }
        // },
    // });

    FieldMany2ManyTags.prototype.events['click .o_badge_text'] = 'on_show_detail';

    FieldMany2ManyTags.include({
        tag_template: "Many2ManyFleet",

        on_show_detail: function (ev) {
            var context = this.build_context().eval();
            var model_obj = new Model(this.field.relation);
            var id = parseInt($(ev.currentTarget).parent().attr("data-id"));
            var self = this;
            model_obj.call('get_formview_id', [[id], context]).then(function(view_id){
                var pop = new common.FormViewDialog(self, {
                    res_model: model_obj.name,
                    res_id: id,
                    context: context,
                    title: _t("Open: Car Information"),
                    view_id: view_id,
                    readonly: true
                }).open();
                pop.on('write_completed', self, function(){
                    self.display_value = {};
                    self.display_value_backup = {};
                    self.render_value();
                    self.focus();
                    self.trigger('changed_value');
                });
            });
        },
        open_color_picker: function(ev){
            ev.preventDefault();
        },
    });
    // var Many2ManyFleets = form_relational.AbstractManyField.extend(form_common.ReinitializeWidgetMixin, {
    //     className: "o_form_field_many2manytags",
    //     tag_template: "Many2ManyFleet",
    //
    //     events: {
    //         'click .o_delete': function(e) {
    //             this.remove_id($(e.target).parent().data('id'));
    //         },
    //         // 'mousedown .o_colorpicker span': 'update_color',
    //         // 'focusout .o_colorpicker': 'close_color_picker',
    //         'click .o_badge_text': 'on_show_detail'
    //     },
    //     init: function(field_manager, node) {
    //             this._super(field_manager, node);
    //             this.data_ids = [];
    //             if (this.field.context.no) {
    //                 this.options['no_close'] = true;
    //             }
    //         },
    //     willStart: function () {
    //         var self = this;
    //         return this.dataset.call('fields_get', []).then(function(fields) {
    //            self.fields = fields;
    //         });
    //     },
    //     commit_value: function() {
    //         this.dataset.cancel_read();
    //         return this._super();
    //     },
    //     initialize_content: function() {
    //         if(!this.get("effective_readonly")) {
    //             this.many2one = new FieldMany2One(this.field_manager, this.node);
    //             this.many2one.options.no_open = true;
    //             this.many2one.on('changed_value', this, function() {
    //                 var newValue = this.many2one.get('value');
    //                 if(newValue) {
    //                     this.add_id(newValue);
    //                     this.many2one.set({'value': false});
    //                 }
    //             });
    //
    //             this.many2one.prependTo(this.$el);
    //
    //             var self = this;
    //             this.many2one.$('input').on('keydown', function(e) {
    //                 if(!$(e.target).val() && e.which === 8) {
    //                     var $badges = self.$('.badge');
    //                     if($badges.length) {
    //                         self.remove_id($badges.last().data('id'));
    //                     }
    //                 }
    //             });
    //             this.many2one.get_search_blacklist = function () {
    //                 return self.get('value');
    //             };
    //         }
    //     },
    //     destroy_content: function() {
    //         if(this.many2one) {
    //             this.many2one.destroy();
    //             this.many2one = undefined;
    //         }
    //     },
    //     get_render_data: function(ids){
    //         this.dataset.cancel_read();
    //         var fields = this.fields.color ? ['display_name', 'name', 'color'] : ['display_name', 'name']; // TODO master: remove useless 'name'
    //         return this.dataset.read_ids(ids, fields);
    //     },
    //     render_tag: function(data) {
    //         this.$('.badge').remove();
    //         this.$el.prepend(QWeb.render(this.tag_template, {elements: data, readonly: this.get('effective_readonly')}));
    //     },
    //     render_value: function() {
    //         var self = this;
    //         var values = this.get("value");
    //         var handle_names = function(_data) {
    //             _.each(_data, function(el) {
    //                 el.display_name = el.display_name.trim() ? _.str.escapeHTML(el.display_name) : data.noDisplayContent;
    //             });
    //             self.render_tag(_data);
    //         };
    //         if (!values || values.length > 0) {
    //             return this.alive(this.get_render_data(values)).done(handle_names);
    //         } else {
    //             handle_names([]);
    //         }
    //     },
    //     add_id: function(id) {
    //         this.set({'value': _.uniq(this.get('value').concat([id]))});
    //     },
    //
    //     remove_id: function(id) {
    //         this.set({'value': _.without(this.get("value"), id)});
    //     },
    //     focus: function () {
    //         if(!this.get("effective_readonly")) {
    //             return this.many2one.focus();
    //         }
    //         return false;
    //     },
    //     set_dimensions: function(height, width) {
    //         if(this.many2one) {
    //             this.many2one.$el.css('height', 'auto');
    //         }
    //         this.$el.css({
    //             width: width,
    //             minHeight: height,
    //         });
    //         if(this.many2one) {
    //             this.many2one.$el.css('height', this.$el.height());
    //         }
    //     },
    //     on_show_detail: function (ev) {
    //         var context = this.build_context().eval();
    //         var model_obj = new Model(this.field.relation);
    //         var id = parseInt($(ev.currentTarget).parent().attr("data-id"));
    //         var self = this;
    //         model_obj.call('get_formview_id', [[id], context]).then(function(view_id){
    //             var pop = new common.FormViewDialog(self, {
    //                 res_model: model_obj.name,
    //                 res_id: id,
    //                 context: context,
    //                 title: _t("Open: Car Information"),
    //                 view_id: view_id,
    //                 readonly: !self.can_write
    //             }).open();
    //             pop.on('write_completed', self, function(){
    //                 self.display_value = {};
    //                 self.display_value_backup = {};
    //                 self.render_value();
    //                 self.focus();
    //                 self.trigger('changed_value');
    //             });
    //         });
    //     },
    //     open_color_picker: function(ev){
    //         ev.preventDefault();
    //     },
    //     close_color_picker: function(){
    //         this.$color_picker.remove();
    //     },
    //     update_color: function(ev) {
    //         ev.preventDefault();
    //
    //         var color = $(ev.currentTarget).data('color');
    //         var id = $(ev.currentTarget).data('id');
    //
    //         var self = this;
    //         this.dataset.call('write', [id, {'color': color}]).done(function(){
    //             self.dataset.cache[id].from_read = {};
    //             self.dataset.evict_record(id);
    //             var tag = self.$el.find("span.badge[data-id='" + id + "']");
    //             var old_color = tag.data('color');
    //             tag.removeClass('o_tag_color_' + old_color);
    //             tag.data('color', color);
    //             tag.addClass('o_tag_color_' + color);
    //         });
    //     },
    // });

    core.form_widget_registry.add('my_kanban', MyKanban);
    core.form_widget_registry.add('field_ok', MyWidget);
    // core.form_widget_registry.add('my_many2many_tags', Many2ManyFleets);

});