odoo.define('btek_hr_working_day.btek_timesheet', function (require) {
"use strict";

var core = require('web.core');
var data = require('web.data');
var form_common = require('web.form_common');
var formats = require('web.formats');
var Model = require('web.DataModel');
var time = require('web.time');
var utils = require('web.utils');
var ajax = require('web.ajax');
var View = require('web.View');

var QWeb = core.qweb;
var _t = core._t;

// var gui = require('point_of_sale.gui');
// var PopupWidget = require('point_of_sale.popups');

// var BaveErrorPopup = PopupWidget.extend({
//     template:'BaveErrorPopup',
//     show: function(options){
//         this._super(options);
//         this.gui.play_sound('error');
//     },
// });
// gui.define_popup({name:'bave_error', widget: BaveErrorPopup});

var BtekWeeklyTimesheet = form_common.FormWidget.extend(form_common.ReinitializeWidgetMixin, {
    defaults: {
        // list rows can be deleted
        deletable: false
    },
    events: {
        "click .oe_timesheet_weekly_account a": "go_to",
        "click .o_list_working_remove" : "delete_day_line",
        // "click .o_form_input_dropdown" : "onchange_department"
    },

    onchange_department: function (ev) {
        ev.preventDefault();
        this.init_add_employee();
        // return this._super();
    },

    delete_day_line: function (e) {
        e.stopPropagation();
        var row = $(e.target).closest('td');
        // var emp_line = $(".o_list_view > tbody > tr").attr("data-id");
        $("td a[data-id=" + $(row).attr("data-employee") + "]").remove();
        $("td [data-employee=" + $(row).attr("data-employee") + "]").remove();
        $("td [data-employee-total=" + $(row).attr("data-employee") + "]").remove();
        var tr_parent = $(e.target).closest('tr');
        tr_parent.remove();

        // var working_day_id = this.field_manager.dataset.context.params.id;
        var employee_id = $(row).attr("data-employee");
        var date_from = this.dates[0];
        var date_to = this.dates[this.dates.length-1];
        ajax.jsonRpc('/api/timesheet_unlink', 'call', {
            'employee_id': employee_id,
            'date_from': date_from,
            'date_to': date_to
        }).then(function () {
            console.log('success')
        }
        );
    },
    ignore_fields: function() {
        return ['line_id'];
    },
    init: function(options) {
        this._super.apply(this, arguments);
        this.set({
            sheets: [],
            date_from: false,
            date_to: false
        });

        this.field_manager.on("field_changed:timesheet_ids", this, this.query_sheets);
        this.field_manager.on("field_changed:date_from", this, function() {
            this.set({"date_from": time.str_to_date(this.field_manager.get_field_value("date_from"))});
        });
        this.field_manager.on("field_changed:date_to", this, function() {
            this.set({"date_to": time.str_to_date(this.field_manager.get_field_value("date_to"))});
        });

        this.on("change:sheets", this, this.update_sheets);
        this.res_o2m_drop = new utils.DropMisordered();
        this.render_drop = new utils.DropMisordered();
        this.description_line = _t("/");
    },
    go_to: function(event) {
        var id = JSON.parse($(event.target).data("id"));
        this.do_action({
            type: 'ir.actions.act_window',
            res_model: "hr.employee",
            res_id: id,
            views: [[false, 'form']],
        });
    },
    query_sheets: function() {
        if (this.updating) {
            return;
        }
        this.querying = true;
        var commands = this.field_manager.get_field_value("timesheet_ids");
        var self = this;
        this.res_o2m_drop.add(new Model(this.view.model).call("resolve_2many_commands",
                ["timesheet_ids", commands, [], new data.CompoundContext()]))
            .done(function(result) {
                self.set({sheets: result});
                self.querying = false;
            });
    },
    // update day line
    update_sheets: function() {
        if(this.querying) {
            return;
        }
        this.updating = true;

        var commands = [form_common.commands.delete_all()];
        _.each(this.get("sheets"), function (_data) {
            var data = _.clone(_data);
            if(data.id) {
                commands.push(form_common.commands.link_to(data.id));
                commands.push(form_common.commands.update(data.id, data));
            } else {
                commands.push(form_common.commands.create(data));
            }
        });

        var self = this;
        this.field_manager.set_values({'timesheet_ids': commands}).done(function() {
            self.updating = false;
        });
    },
    initialize_field: function() {
        form_common.ReinitializeWidgetMixin.initialize_field.call(this);
        this.on("change:sheets", this, this.initialize_content);
        this.on("change:date_to", this, this.initialize_content);
        this.on("change:date_from", this, this.initialize_content);
        // this.on("change:user_id", this, this.initialize_content);
    },
    initialize_content: function() {
        if(this.setting) {
            return;
        }

        // don't render anything until we have date_to and date_from
        if (!this.get("date_to") || !this.get("date_from")) {
            return;
        }

        // it's important to use those vars to avoid race conditions
        var dates;
        var employees;
        var employee_names;
        var default_get;
        var self = this;
        return this.render_drop.add(new Model("hr.working.day.employee.line").call("default_get", [
            ['date', 'name', 'unit_amount', 'employee_id'],
            // new data.CompoundContext({'user_id': self.get('user_id')})
        ]).then(function(result) {
            default_get = result;
            // calculating dates
            dates = [];
            var start = self.get("date_from");
            var end = self.get("date_to");
            while (start <= end) {
                dates.push(start);
                var m_start = moment(start).add(1, 'days');
                start = m_start.toDate();
            }
            // group by employee
            employees = _.chain(self.get("sheets"))
            .map(_.clone)
            .each(function(el) {
                // much simpler to use only the id in all cases
                if (typeof(el.employee_id) === "object") {
                    el.employee_id = el.employee_id[0];
                }
            })
            .groupBy("employee_id").value();

            var employee_ids = _.map(_.keys(employees), function(el) { return el === "false" ? false : Number(el); });

            employees = _(employees).chain().map(function(lines, employee_id) {
                var employees_defaults = _.extend({}, default_get, (employees[employee_id] || {}).value || {});
                // group by days
                employee_id = (employee_id === "false")? false : Number(employee_id);
                var index = _.groupBy(lines, "date");
                var days = _.map(dates, function(date) {
                    var day = {day: date, lines: index[time.date_to_str(date)] || []};
                    // add line where we will insert/remove hours
                    var to_add = _.find(day.lines, function(line) { return line.name === self.description_line; });
                    if (to_add) {
                        day.lines = _.without(day.lines, to_add);
                        day.lines.unshift(to_add);
                    } else {
                        day.lines.unshift(_.extend(_.clone(employees_defaults), {
                            name: self.description_line,
                            unit_amount: 0,
                            date: time.date_to_str(date),
                            employee_id: employee_id,
                        }));
                    }
                    return day;
                });
                return {employee: employee_id, days: days, employees_defaults: employees_defaults};
            }).value();

            // we need the name_get of the employees
            return new Model("hr.employee").call("name_get", [_.pluck(employees, "employee"),
                new data.CompoundContext()]).then(function(result) {
                employee_names = {};
                _.each(result, function(el) {
                    employee_names[el[0]] = el[1];
                });
                employees = _.sortBy(employees, function(el) {
                    return employee_names[el.employee];
                });
            });
        })).then(function(result) {
            // we put all the gathered data in self, then we render
            self.dates = dates;
            self.employees = employees;
            self.employee_names = employee_names;
            self.default_get = default_get;
            //real rendering
            self.display_data();
        });
    },
    destroy_content: function() {
        if (this.dfm) {
            this.dfm.destroy();
            this.dfm = undefined;
        }
    },

    display_data: function() {
        var self = this;
        self.$el.html(QWeb.render("btek_hr_working_day.BtekWeeklyTimesheet", {widget: self}));
        _.each(self.employees, function(employee) {
            _.each(_.range(employee.days.length), function(day_count) {
                if (!self.get('effective_readonly')) {
                    self.get_box(employee, day_count).val(self.sum_box(employee, day_count, true)).change(function() {
                        var num = $(this).val();
                        if (num > 1 || num < 0){
                            // self.gui.show_popup('error',{
                            //     title: _t('Validate Days Data'),
                            //     body:  _t('Days can not be greater 1 and less than 0'),
                            // });
                            return confirm('Days can not be greater 1 and less than 0');
                        }
                        // if (self.is_valid_value(num)) {
                        //     num = Number(num);
                        // }
                        if (isNaN(num)) {
                            $(this).val(self.sum_box(employee, day_count, true));
                        } else {
                            employee.days[day_count].lines[0].unit_amount += num - self.sum_box(employee, day_count);
                            if(!isNaN($(this).val())){
                                $(this).val(self.sum_box(employee, day_count, true));
                            }
                            self.display_totals();
                            self.sync();
                        }
                    });
                } else {
                    self.get_box(employee, day_count).html(self.sum_box(employee, day_count, true));
                }
            });
        });
        self.display_totals();
        if(!this.get('effective_readonly')) {
            this.init_add_employee();
        }
    },
    init_add_employee: function() {
        if (this.dfm) {
            this.dfm.destroy();
        }

        var self = this;
        this.$(".oe_timesheet_weekly_add_row").show();
        this.dfm = new form_common.DefaultFieldManager(this);
        this.dfm.extend_field_desc({
            employee: {
                relation: "hr.employee"
            },
        });
        var FieldMany2One = core.form_widget_registry.get('many2one');
        // var department_ids = self.field_manager.datarecord.department_ids;
        var departmentList = $(".o_tag_color_10").map(function() {
            return $(this).data("id");
        }).get();
        if (!_.isEmpty(departmentList)) {
            this.employee_m2o = new FieldMany2One(this.dfm, {
                attrs: {
                    name: "employee",
                    type: "many2one",
                    domain: [
                        ['id', 'not in', _.pluck(this.employees, "employee")],
                        ['department_id', 'in', departmentList],
                        // ['company_id', '=', self.field_manager.datarecord.company_id]
                    ],
                    modifiers: '{"required": true}',
                },
            });
        }
        else{
            this.employee_m2o = new FieldMany2One(this.dfm, {
                attrs: {
                    name: "employee",
                    type: "many2one",
                    domain: [
                        ['id', 'not in', _.pluck(this.employees, "employee")],
                        // ['company_id', '=', self.field_manager.datarecord.company_id]
                    ],
                    modifiers: '{"required": true}',
                },
            });
        }

        this.employee_m2o.prependTo(this.$(".o_add_timesheet_line > div")).then(function() {
            self.employee_m2o.$el.addClass('oe_edit_only');
        });
        this.$(".oe_timesheet_button_add").click(function() {
            var id = self.employee_m2o.get_value();
            if (id === false) {
                self.dfm.set({display_invalid_fields: true});
                return;
            }
            var emp_id = id;
            var date_from = self.dates[0];
            var date_to = self.dates[self.dates.length-1];
            ajax.jsonRpc('/api/timesheet_autofill', 'call', {
                'emp_id': emp_id,
                'date_from': date_from,
                'date_to': date_to
            }).then(function (data) {
                if (!_.isEmpty(data)) {
                    if (!_.isEmpty(self.employees)) {
                        _.each(self.employees, function (emp) {
                            _.each(emp['days'], function (record) {
                                data.push({
                                    date: record['lines'][0]['date'],
                                    employee_id: record['lines'][0]['employee_id'],
                                    unit_amount: record['lines'][0]['unit_amount'],
                                    name: self.description_line
                                })
                            });
                        });
                    }
                    self.set({sheets: data});
                }
                else{
                    var ops = self.generate_o2m_value();
                    ops.push(_.extend({}, self.default_get, {
                        name: self.description_line,
                        unit_amount: 1,
                        date: time.date_to_str(self.dates[0]),
                        employee_id: id
                    }));
                    self.set({sheets: ops});
                }
                }
            );
            self.destroy_content();
        });
    },
    get_box: function(employee, day_count) {
        return this.$('[data-employee="' + employee.employee + '"][data-day-count="' + day_count + '"]');
    },
    sum_box: function(employee, day_count, show_value_in_hour) {
        var line_total = 0;
        _.each(employee.days[day_count].lines, function(line) {
            line_total += line.unit_amount;
        });
        return (show_value_in_hour && line_total !== 0)?line_total:line_total;
    },
    display_totals: function() {
        var self = this;
        var day_tots = _.map(_.range(self.dates.length), function() { return 0; });
        var super_tot = 0;
        _.each(self.employees, function(employee) {
            var acc_tot = 0;
            _.each(_.range(self.dates.length), function(day_count) {
                var sum = self.sum_box(employee, day_count);
                acc_tot += sum;
                day_tots[day_count] += sum;
                super_tot += sum;
            });
            self.$('[data-employee-total="' + employee.employee + '"]').html(acc_tot);
        });
        _.each(_.range(self.dates.length), function(day_count) {
            self.$('[data-day-total="' + day_count + '"]').html(day_tots[day_count]);
        });
        this.$('.oe_timesheet_weekly_supertotal').html(super_tot);
    },
    sync: function() {
        this.setting = true;
        this.set({sheets: this.generate_o2m_value()});
        this.setting = false;
    },
    //converts hour value to float
    // parse_client: function(value) {
    //     return formats.parse_value(value, { type:"float" });
    // },
    //converts float value to hour
    // format_client:function(value){
    //     return formats.format_value(value, { type:"float" });
    // },
    generate_o2m_value: function() {
        var ops = [];
        var ignored_fields = this.ignore_fields();
        _.each(this.employees, function(employee) {
            _.each(employee.days, function(day) {
                _.each(day.lines, function(line) {
                    if (line.unit_amount !== 0) {
                        var tmp = _.clone(line);
                        _.each(line, function(v, k) {
                            if (v instanceof Array) {
                                tmp[k] = v[0];
                            }
                        });
                        // we remove line_id as the reference to the _inherits field will no longer exists
                        tmp = _.omit(tmp, ignored_fields);
                        ops.push(tmp);
                    }
                });
            });
        });
        return ops;
    },
});

core.form_custom_registry.add('btek_weekly_timesheet', BtekWeeklyTimesheet);
});