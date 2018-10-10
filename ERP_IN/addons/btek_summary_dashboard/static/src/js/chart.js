// http://tobiasahlin.com/blog/chartjs-charts-to-get-you-started/
var url = window.location.href;
var arr = url.split("/");
var home_url = arr[0] + "//" + arr[2];
// var home_url = window.location.protocol+ '//' + window.location.hostname;
// var home_url = '';

//set company
var set_user_company_url = home_url + '/set-user-company';

var revenue_url = home_url + '/get_revenue_area_chart_datas/';

//car in
var car_in_url = home_url + '/get_car_in_area_chart_datas/';
var pie_car_in_url = home_url + '/get_car_in_pie_chart_datas/';

// var revenue_cost_product_type_url = home_url + '/revenue_cost_product_type_pie_chart/';
var revenue_cost_product_type_url = home_url + '/revenue-cost-product-type-pie-chart/';

//top revenue customer
var top_revenue_customer = home_url + '/top_revenue_customer_url/';

//customer
var pie_customer_url = home_url + '/get_customer_pie_chart_datas/';
var multi_line_customer_url = home_url + '/get_customer_multi_line_chart_datas/';
var return_customer_rate_url = home_url + '/get_return_customer_rate/';
var customer_number_times_url = home_url + '/customer-number-times/'

//product and service
var pie_product_service_rate_url = home_url + '/product_service_rate/';
var top10_service_package_rate_url = home_url + '/top10_service_package_rate/';
var top10_service_rate_url = home_url + '/top10_service_rate/';
var top10_product_rate_url = home_url + '/top10_product_rate/';

//inventory
var qty_inventory_by_warehouse_rate_url = home_url + '/qty_inventory_by_warehouse_rate/';
var value_inventory_by_warehouse_rate_url = home_url + '/value_inventory_by_warehouse_rate/';
var top_inventory_value_url = home_url + '/top_inventory_value/';
var top_inventory_qty_url = home_url + '/top_inventory_qty/';

//purchase
var top_purchase_qty_chart_url = home_url + '/top_purchase_qty_chart/';
var top_purchase_value_item_url = home_url + '/top_purchase_value_item/';

//supplier
var top_supplier_qty_chart_url = home_url + '/top_supplier_qty_chart/';
var top_supplier_value_chart_url = home_url + '/top_supplier_value_chart/';

//sale again
var top_sale_again_url = home_url + '/top_sale_again/';

//top_delivery
var top_delivery_url = home_url + '/top_delivery/';

function clear_chart(ElementId) {
    var e = document.getElementById(ElementId);
    var we = e.parentNode;
    we.removeChild(e);
    we.innerHTML = '<canvas id="' + ElementId + '"></canvas>';
};

function drawRevenueChart(type, period) {
    var revenue_url_param = revenue_url + type + '/' + period;
    var chart_element = "revenue-line-chart";
    if (type == 'cost') {
        chart_element = "cost-line-chart";
    };

    $.getJSON(revenue_url_param,
       function(revenue_area_chart_datas) {
           new Chart(document.getElementById(chart_element), {
              type: 'line',
              data: revenue_area_chart_datas,
              options: {
                title: {
                  display: true,
                  text: ''
                }
              }
            });
       });
};

function drawMultiBarChart(data, ElementId) {
    var ctx = document.getElementById(ElementId).getContext("2d");
		var myBarChart = new Chart(ctx, {
			type: 'bar',
			data: data,
			options: {
				barValueSpacing: 10,
				scales: {
					yAxes: [{
						ticks: {
							min: 0,
						}
					}]
				},
                animation: {
                    duration: 1,
                    onComplete: function () {
                        var chartInstance = this.chart,
                            ctx = chartInstance.ctx;
                        ctx.font = Chart.helpers.fontString(Chart.defaults.global.defaultFontSize, Chart.defaults.global.defaultFontStyle, Chart.defaults.global.defaultFontFamily);
                        ctx.textAlign = 'center';
                        ctx.textBaseline = 'bottom';

                        this.data.datasets.forEach(function (dataset, i) {
                            var meta = chartInstance.controller.getDatasetMeta(i);
                            meta.data.forEach(function (bar, index) {
                                ctx.font = "15pt Courier";
								ctx.fillStyle = '#000009';

								var data = dataset.data[index];
								ctx.fillText(data, bar._model.x, bar._model.y - 5);
								var percent = dataset.percent[index]
								var percent_text = percent + "%";
								ctx.fillText(percent_text, bar._model.x, bar._model.y + 35);
                            });
                        });
                    }
                }
			}
		});
};

function drawMultiLineChart(data, ElementId) {
    clear_chart(ElementId);

    new Chart(document.getElementById(ElementId), {
              type: 'line',
              data: data,
              options: {
                title: {
                  display: true,
                  text: ''
                }
              }
            });
};

function drawCarInChart(period) {
    var car_in_url_param = car_in_url + period;
    $.getJSON(car_in_url_param,
       function(car_in_line_chart_datas) {
           var ElementId = "car-in-line-chart";
           drawMultiLineChart(car_in_line_chart_datas, ElementId);

           var e = document.getElementById("car-in-line-chart-item");
           var e_html = "<ul>";

           for (var line in car_in_line_chart_datas["datasets"]){
               var total = car_in_line_chart_datas["datasets"][line]["total"];
               var percent = car_in_line_chart_datas["datasets"][line]["percent"];
               var label = car_in_line_chart_datas["datasets"][line]["label"];

               e_html = e_html + '<li id="';
               e_html = e_html + total + '" ';
               e_html = e_html + 'percent="' + percent + '">';
               e_html = e_html + label + "</li>";
           }
           e_html = e_html + "</ul>";
           e.innerHTML = e_html;
       });
};

function drawCustomerMultiLineChart(period) {
    var multi_line_customer_url_param = multi_line_customer_url + period;

    $.getJSON(multi_line_customer_url_param,
       function(multi_line_customer_datas) {
           var ElementId = "customer-multi-line-chart";
           drawMultiLineChart(multi_line_customer_datas, ElementId);

           var e = document.getElementById("customer-multi-line-item");
           var e_html = "<ul>";

           for (var line in multi_line_customer_datas["datasets"]){
               var total_line = multi_line_customer_datas["datasets"][line]["total_line"];
               var percent = multi_line_customer_datas["datasets"][line]["percent"];
               var label = multi_line_customer_datas["datasets"][line]["label"];

               e_html = e_html + '<li id="';
               e_html = e_html + total_line + '" ';
               e_html = e_html + 'percent="' + percent + '">';
               e_html = e_html + label + "</li>";
           }
           e_html = e_html + "</ul>";

           e.innerHTML = e_html;

       });
};

function draw_return_customer_rate_bar_chart() {
    var ElementId = "return-customer-rate-bar-chart";

    $.getJSON(return_customer_rate_url,
       function(return_customer_rate_data) {
           drawMultiBarChart(return_customer_rate_data, ElementId);
       });

};

function draw_customer_number_times_chart() {
    var ElementId = "customer-number-times";

    $.getJSON(customer_number_times_url,
       function(ChartData) {
           var inside_text = ChartData["inside_text"];

           var options = get_default_options_Doughnut_Pie_chart(inside_text);
           drawDoughnutChartjs(ChartData, options, ElementId);
       });

};

function fill_top_revenue_customer() {
    var ElementId = "top_revenue_customer";

    var e = document.getElementById(ElementId);

    var period = get_selectedIndex("top_revenue_customer_period");

    var top_revenue_customer_param = top_revenue_customer + period;

    $.getJSON(top_revenue_customer_param,
       function(data) {
           var e_html = '<ul class="list-left-right">';
           for (var customer in data){
               e_html = e_html + '<li>';
               e_html = e_html + data[customer]['name'];
               e_html = e_html + '<span>';
               e_html = e_html + data[customer]['revenue'];
               e_html = e_html + data[customer]['categ'];
               e_html = e_html + '</span></li>';

           };
           e_html = e_html + '</ul>';

           e.innerHTML = e_html;
       });

}

function drawPieChart(chartData, total, current, Element) {
    var chart = AmCharts.makeChart(Element, {
              "type": "pie",
              "theme": "light",
              "dataProvider": [],
              "valueField": "size",
              "titleField": "sector",
              "startDuration": 0,
              "innerRadius": 40,
              "pullOutRadius": 5,
              "marginTop": 0,
              "titles": [{
                "text": ""
              }],
              "allLabels": [{
                "y": "54%",
                "align": "center",
                "size": 12,
                "bold": false,
                "text": "1995",
                "color": "#555"
              }, {
                "y": "49%",
                "align": "center",
                "size": 14,
                  "bold": true,
                "text": total,
                "color": "#555"
              }],
              "listeners": [ {
                "event": "init",
                "method": function( e ) {
                  var chart = e.chart;

                  function getCurrentData() {
                    var data = chartData[current];
                    return data;
                  }

                  function loop() {
                    chart.allLabels[0].text = current;
                    var data = getCurrentData();
                    chart.animateData(data, {
                      duration: 1000,
                      complete: function() {
                        // setTimeout( loop, 3000 );
                      }
                    } );
                  }

                  loop();
                }
              } ],
               "export": {
               "enabled": true
              }
           });
};

function drawCustomerPieChart() {
    $.getJSON(pie_customer_url,
       function(chartData) {
           var currentYear = "Khách";
           var Element = "customer_pie_chart";
           drawPieChart(chartData[0], chartData[1], currentYear, Element);

       });
};

function drawDoughnutChartjs(data, options, ElementId) {
    // if (data['datasets'][0]['data'].length == 0){
    //            clear_chart(ElementId);
    //            return ;
    //        };

    clear_chart(ElementId);

    //get the doughnut chart canvas
    var e = document.getElementById(ElementId);

    //create Chart class object
    new Chart(e, {
        type: "doughnut",
        data: data,
        options: options
    });
};

function drawPieChartjs(data, options, ElementId) {
    // if (data['datasets'][0]['data'].length == 0){
    //            clear_chart(ElementId);
    //            return ;
    //        };

    clear_chart(ElementId);

    var e = document.getElementById(ElementId);

    new Chart(e, {
        type: "pie",
        data: data,
        options: options
    });
};

function get_default_options_Doughnut_Pie_chart(inside_text) {
    var options = {
               responsive: true,
               title: {
                   display: false,
                   position: "top",
                   text: "",
                   fontSize: 18,
                   fontColor: "#646e83"
               },
               legend: {
                   display: true,
                   position: "bottom",
                   labels: {
                       fontColor: "#646e83",
                       fontSize: 14
                   }
               },
               elements: {
                   center: {
                       text: inside_text,
                       color: '#646e83', //Default black
                       fontStyle: '"Helvetica Neue", Helvetica, Arial, sans-serif', //Default Arial
                       sidePadding: 15 //Default 20 (as a percentage)
                   }
               },
                animation: {
                    duration: 500,
                    easing: "easeOutQuart",
                    onComplete: function () {
                      var ctx = this.chart.ctx;
                      ctx.font = Chart.helpers.fontString(Chart.defaults.global.defaultFontFamily, 'normal', Chart.defaults.global.defaultFontFamily);
                      ctx.textAlign = 'center';
                      ctx.textBaseline = 'bottom';

                      this.data.datasets.forEach(function (dataset) {

                        for (var i = 0; i < dataset.data.length; i++) {
                          var model = dataset._meta[Object.keys(dataset._meta)[0]].data[i]._model,
                              total = dataset._meta[Object.keys(dataset._meta)[0]].total,
                              mid_radius = model.innerRadius + (model.outerRadius - model.innerRadius)/2,
                              start_angle = model.startAngle,
                              end_angle = model.endAngle,
                              mid_angle = start_angle + (end_angle - start_angle)/2;

                          var x = mid_radius * Math.cos(mid_angle);
                          var y = mid_radius * Math.sin(mid_angle);

                          ctx.fillStyle = '#fff';
                          if (i == 3){ // Darker text color for lighter background
                            ctx.fillStyle = '#444';
                          }
                          var percent = String(Math.round(dataset.data[i]/total*100)) + "%";
                          // ctx.fillText(dataset.data[i], model.x + x, model.y + y);
                          // Display percent in another line, line break doesn't work for fillText
                          ctx.fillText(percent, model.x + x, model.y + y + 15);
                        }
                      });
                    }
                  }
           };

    return options;
};

function drawProductServiceRatePieChart() {
    var ProductServiceRateElementId = "product_service_rate";

    var period_id = "product_and_service_period";

    var e = document.getElementById(period_id);
    var period = e.options[e.selectedIndex].value;

    var pie_product_service_rate_url_param = pie_product_service_rate_url + period;

    $.getJSON(pie_product_service_rate_url_param,
       function(product_service_rate_chartData) {
           var inside_text = product_service_rate_chartData["inside_text"];

           var options = get_default_options_Doughnut_Pie_chart(inside_text);
           drawPieChartjs(
               product_service_rate_chartData,
               options, ProductServiceRateElementId);
       });
};

function drawtop10_service_package_ratePieChart() {
    var top10_service_package_rateElementId = "top10_service_package_rate";

    var period_id = "product_and_service_period";

    var e = document.getElementById(period_id);
    var period = e.options[e.selectedIndex].value;

    var top10_service_package_rate_url_param = top10_service_package_rate_url + period;

    $.getJSON(top10_service_package_rate_url_param,
       function(top10_service_package_rate_chartData) {
           var inside_text = top10_service_package_rate_chartData["inside_text"];

           var options = get_default_options_Doughnut_Pie_chart(inside_text);
           drawDoughnutChartjs(
               top10_service_package_rate_chartData,
               options, top10_service_package_rateElementId);

       });
};

function drawtop10_service_ratePieChart() {
    var top10_service_rateElementId = "top10_service_rate";

    var period_id = "product_and_service_period";

    var e = document.getElementById(period_id);
    var period = e.options[e.selectedIndex].value;

    var top10_service_rate_url_param = top10_service_rate_url + period;

    $.getJSON(top10_service_rate_url_param,
       function(top10_service_rate_chartData) {
           var inside_text = top10_service_rate_chartData["inside_text"];

           var options = get_default_options_Doughnut_Pie_chart(inside_text);
           drawDoughnutChartjs(
               top10_service_rate_chartData,
               options, top10_service_rateElementId);

       });
};

function top10_product_ratePieChart() {
    var top10_product_rateElementId = "top10_product_rate";

    var period_id = "product_and_service_period";

    var e = document.getElementById(period_id);
    var period = e.options[e.selectedIndex].value;

    var top10_product_rate_url_param = top10_product_rate_url + period;

    $.getJSON(top10_product_rate_url_param,
       function(top10_product_rate_chartData) {
           var inside_text = top10_product_rate_chartData["inside_text"];

           var options = get_default_options_Doughnut_Pie_chart(inside_text);
           drawDoughnutChartjs(
               top10_product_rate_chartData,
               options, top10_product_rateElementId);
       });
};

function draw_qty_inventory_by_warehouse_rate() {
    var ElementId = "qty_inventory_by_warehouse_rate";

    $.getJSON(qty_inventory_by_warehouse_rate_url,
       function(chartData) {
           var inside_text = chartData["inside_text"];

           var options = get_default_options_Doughnut_Pie_chart(inside_text);
           drawPieChartjs(
               chartData,
               options, ElementId);
       });
};

function draw_value_inventory_by_warehouse_rate() {
    var ElementId = "value_inventory_by_warehouse_rate";

    $.getJSON(value_inventory_by_warehouse_rate_url,
       function(chartData) {
           var inside_text = chartData["inside_text"];

           var options = get_default_options_Doughnut_Pie_chart(inside_text);
           drawPieChartjs(
               chartData,
               options, ElementId);
       });
};

function get_selectedIndex(ElementId) {
    var e = document.getElementById(ElementId);
    var selected_value = e.options[e.selectedIndex].value;
    return selected_value;
};

function draw_top_inventory_qty() {
    var ElementId = "top_inventory_qty";

    var stock_id = get_selectedIndex("stock_location_selection");

    var top_inventory_qty_url_param = top_inventory_qty_url + stock_id;

    $.getJSON(top_inventory_qty_url_param,
       function(chartData) {
           var inside_text = chartData["inside_text"];

           var options = get_default_options_Doughnut_Pie_chart(inside_text);
           drawDoughnutChartjs(
               chartData,
               options, ElementId);
       });
};

function draw_top_inventory_value() {
    var ElementId = "top_inventory_value";

    var stock_id = get_selectedIndex("stock_location_selection");

    var top_inventory_value_url_param = top_inventory_value_url + stock_id;

    $.getJSON(top_inventory_value_url_param,
       function(chartData) {
           var inside_text = chartData["inside_text"];

           var options = get_default_options_Doughnut_Pie_chart(inside_text);
           drawDoughnutChartjs(
               chartData,
               options, ElementId);
       });
};

function draw_top_purchase_qty_chart() {
    var ElementId = "top_purchase_qty_chart";

    var period = get_selectedIndex("top_purchase_qty_period");

    var top_purchase_qty_chart_url_param = top_purchase_qty_chart_url + period;

    $.getJSON(top_purchase_qty_chart_url_param,
       function(chartData) {
           var inside_text = chartData["inside_text"];

           var options = get_default_options_Doughnut_Pie_chart(inside_text);
           drawPieChartjs(
               chartData,
               options, ElementId);
       });
};

function set_top_purchase_value_item() {
    var ElementId = "top_purchase_value_item";
    var e = document.getElementById(ElementId);

    var period = get_selectedIndex("top_purchase_value_period");

    var top_purchase_value_item_url_param = top_purchase_value_item_url + period;

    $.getJSON(top_purchase_value_item_url_param,
       function(itemData) {
           var e_html = "";
           for (var item in itemData){
               e_html = e_html + '<div class="item-top-purchase">';
               e_html = e_html + '<div class="row">';
               e_html = e_html + '<div class="col-md-6 top-purchase-value-name">';
               e_html = e_html + itemData[item]["name"];
               e_html = e_html + '</div>';

               e_html = e_html + '<div class="col-md-2 top-purchase-value-qty">';
               e_html = e_html + itemData[item]["qty"];
               e_html = e_html + '</div>';

               e_html = e_html + '<div class="col-md-4 top-purchase-value-value">';
               e_html = e_html + itemData[item]["value"];
               e_html = e_html + '</div>';
               e_html = e_html + '</div>';
               e_html = e_html + '</div>';

           };
           e.innerHTML = e_html;
           // jQuery('#top_purchase_value_item').append(e_html);
       });
};

function draw_top_supplier_qty_chart() {
    var ElementId = "top_supplier_qty_chart";

    var period = get_selectedIndex("top_supplier_period");

    var top_supplier_qty_chart_url_param = top_supplier_qty_chart_url + period;

    $.getJSON(top_supplier_qty_chart_url_param,
       function(chartData) {
           var inside_text = chartData["inside_text"];

           var options = get_default_options_Doughnut_Pie_chart(inside_text);
           drawDoughnutChartjs(
               chartData,
               options, ElementId);
       });
};

function draw_top_supplier_value_chart() {
    var ElementId = "top_supplier_value_chart";

    var period = get_selectedIndex("top_supplier_period");

    var top_supplier_value_chart_url_param = top_supplier_value_chart_url + period;

    $.getJSON(top_supplier_value_chart_url_param,
       function(chartData) {
           var inside_text = chartData["inside_text"];

           var options = get_default_options_Doughnut_Pie_chart(inside_text);
           drawDoughnutChartjs(
               chartData,
               options, ElementId);
       });
};

function fill_top_sale_again() {
    var ElementId = 'top_sale_again';
    var period = get_selectedIndex('top_sale_again_period');
    var e = document.getElementById(ElementId);

    var top_sale_again_url_param = top_sale_again_url + period;

    $.getJSON(top_sale_again_url_param,
       function(Data) {
           var e_html = '';

           for (var item in Data){
               var name = Data[item]['name'];
               var qty = Data[item]['qty'];

               e_html = e_html + '<li>';
               e_html = e_html + name;

               e_html = e_html + '<span>';
               e_html = e_html + qty;
               e_html = e_html + '</span>';
               e_html = e_html + '</li>';
           };

           e.innerHTML = e_html;
           // jQuery('#top_sale_again').append( e_html );
       });
};

function fill_top_delivery() {
    var ElementId = 'top_delivery';
    var period = get_selectedIndex('top_delivery_period');
    var e = document.getElementById(ElementId);

    var top_delivery_url_param = top_delivery_url + period;

    $.getJSON(top_delivery_url_param,
       function(Data) {
           var e_html = '';

           for (var item in Data){
               var name = Data[item]['name'];
               var qty = Data[item]['for'];

               e_html = e_html + '<li>';
               e_html = e_html + name;

               e_html = e_html + '<span>';
               e_html = e_html + qty;
               e_html = e_html + '</span>';
               e_html = e_html + '</li>';
           };

           e.innerHTML = e_html;
           // jQuery('#top_delivery').append(e_html);
       });
};

function drawCarInPieChart() {
    $.getJSON(pie_car_in_url,
       function(car_in_chartData) {
           var Elementid = "car_in_pie_chart";

           var inside_text = car_in_chartData["inside_text"];

           var options = get_default_options_Doughnut_Pie_chart(inside_text);

           drawDoughnutChartjs(car_in_chartData, options, Elementid)
       });

};

function set_button_color(type, period) {
    var ElementId = period + "_" + type + "_button";
    var revenue_button = document.getElementById(ElementId);
    var classname = type + "_" + period;
    revenue_button.className = "selected_button " + classname;
}

function unset_button_color(type, period) {
    var ElementId = period + "_" + type + "_button";
    var revenue_button = document.getElementById(ElementId);
    var classname = type + "_" + period;
    revenue_button.className = classname;
}

function draw_revenue_cost_product_type_pie_chart(type, period) {
    var ElementId = type + "_product_type_pie_chart";

    var revenue_cost_product_type_url_param = revenue_cost_product_type_url + type + '/' + period;

    $.getJSON(revenue_cost_product_type_url_param,
       function(chartData) {
           var inside_text = chartData["inside_text"];

           var options = get_default_options_Doughnut_Pie_chart(inside_text);
           drawDoughnutChartjs(
               chartData,
               options, ElementId);
       });
};

function reset_product_revenue_cost_period(type) {
    var period_id = type + '_period_week_month_quarter';
    var period = document.getElementById(period_id);
    var period_value = period.options[period.selectedIndex].value;

    var url = '/product-revenue-cost-period/';
    var param_url = url + type + '/' + period_value;

    var period_label = "TUẦN";
    if (period_value == 'month'){
        period_label = "THÁNG";
    };
    if (period_value == 'quarter'){
        period_label = "QUÝ";
    };
    if (period_value == 'year'){
        period_label = "NĂM";
    };

    $.getJSON(param_url,
       function(product_datas) {
           if (type == 'revenue'){
               var period_revenue_element = document.getElementById('period_revenue_value');
               period_revenue_element.innerHTML = "Doanh thu " + period_label + ": " + product_datas['period_value'];
           }
           if (type == 'cost'){
               var period_cost_element = document.getElementById('period_cost_value');
               period_cost_element.innerHTML = "Chi phí " + period_label + ": " + product_datas['period_value'];
           }

       });

};

function PieChartExtend() {
    Chart.pluginService.register({
  beforeDraw: function (chart) {
    if (chart.config.options.elements.center) {
      //Get ctx from string
      var ctx = chart.chart.ctx;

      //Get options from the center object in options
      var centerConfig = chart.config.options.elements.center;
      var fontStyle = centerConfig.fontStyle || 'Arial';
      var txt = centerConfig.text;
      var color = centerConfig.color || '#000';
      var sidePadding = centerConfig.sidePadding || 20;
      var sidePaddingCalculated = (sidePadding/100) * (chart.innerRadius * 2)
      //Start with a base font of 30px
      ctx.font = "30px " + fontStyle;

      //Get the width of the string and also the width of the element minus 10 to give it 5px side padding
      var stringWidth = ctx.measureText(txt).width;
      var elementWidth = (chart.innerRadius * 2) - sidePaddingCalculated;

      // Find out how much the font can grow in width.
      var widthRatio = elementWidth / stringWidth;
      var newFontSize = Math.floor(30 * widthRatio);
      var elementHeight = (chart.innerRadius * 2);

      // Pick a new font size so it will not be larger than the height of label.
      var fontSizeToUse = Math.min(newFontSize, elementHeight);

      //Set font settings to draw it correctly.
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      var centerX = ((chart.chartArea.left + chart.chartArea.right) / 2);
      var centerY = ((chart.chartArea.top + chart.chartArea.bottom) / 2);
      ctx.font = fontSizeToUse+"px " + fontStyle;
      ctx.fillStyle = color;

      //Draw text in center
      ctx.fillText(txt, centerX, centerY);
    }
  }
});
};

$(document).ready(function(){
    //change company
    $('#company_selectbox').change(function() {
        var e = document.getElementById("company_selectbox");
        var company_id = e.options[e.selectedIndex].value;

        var param_url = set_user_company_url + '/' + company_id;

        $.getJSON(param_url,
       function(result) {
           if (result == true){
               location.reload();
           }
       });

    });
    //select block
    $('.choose_block_button').click(function () {
        var selected_id = this.id;
        var selected_block_class = selected_id.replace("_button", "");
        
        var block_class_list = ["summary_block",
            "customer_block",
            "product_and_service_block",
            "inventory_block",
            "purchase_block"];

        for (var block_class in block_class_list){
            var b = document.getElementById(block_class_list[block_class] + "_button");
            var e = document.getElementById(block_class_list[block_class]);

            //show panel ~ selected button, change style selected button
            if (block_class_list[block_class] == selected_block_class){
                if (!b.classList.contains('selected_button')){
                    b.classList.add('selected_button');
                }

                if (e.classList.contains('hidden-panel')){
                    e.classList.remove('hidden-panel');
                }
                continue;
            }

            //hide panel ~ unselected button, change style unselected button
            if (b.classList.contains('selected_button')){
                    b.classList.remove('selected_button');
                }

            if (!e.classList.contains('hidden-panel')){
                e.classList.add('hidden-panel');
            }
        }

    });

    //customer
    $('.car_in_week').click(function() {
        var period = 'week';
        drawCarInChart(period);

        var type = "car_in";

        //set button color
        set_button_color(type, period);
        unset_button_color(type, "month");
        unset_button_color(type, "quarter");
    });

    $('.car_in_month').click(function() {
        var period = 'month';
        drawCarInChart(period);

        var type = "car_in";

        //set button color
        set_button_color(type, period);
        unset_button_color(type, "week");
        unset_button_color(type, "quarter");
    });

    $('.car_in_quarter').click(function() {
        var period = 'quarter';
        drawCarInChart(period);

        var type = "car_in";

        //set button color
        set_button_color(type, period);
        unset_button_color(type, "month");
        unset_button_color(type, "week");
    });

    $('#car_in_period').change(function() {
        var type = 'revenue';

        var e = document.getElementById("car_in_period");
        var period = e.options[e.selectedIndex].value;

        drawCarInChart(period);

        // var type = "car_in";
        //
        // //set button color
        // set_button_color(type, period);
        // unset_button_color(type, "month");
        // unset_button_color(type, "week");
    });

    $('#customer_multi_line_period').change(function() {

        var e = document.getElementById("customer_multi_line_period");
        var period = e.options[e.selectedIndex].value;

        drawCustomerMultiLineChart(period);
    });

    // revenue
    $('.revenue_week').click(function() {
        var type = 'revenue';
        var period = 'week';
        drawRevenueChart(type, period);
        draw_revenue_cost_product_type_pie_chart(type, period);

        //set button color
        set_button_color(type, period);
        unset_button_color(type, "month");
        unset_button_color(type, "quarter");
        unset_button_color(type, "year");

    //    change revenue_period_week_month_quarter value
        var revenue_period = document.getElementById("revenue_period_week_month_quarter");
        revenue_period.value = period;

        reset_product_revenue_cost_period(type);
    });

    $('.revenue_month').click(function() {
        var type = 'revenue';
        var period = 'month';
        drawRevenueChart(type, period);
        draw_revenue_cost_product_type_pie_chart(type, period);

        //set button color
        set_button_color(type, period);
        unset_button_color(type, "week");
        unset_button_color(type, "quarter");
        unset_button_color(type, "year");

        //    change revenue_period_week_month_quarter value
        var revenue_period = document.getElementById("revenue_period_week_month_quarter");
        revenue_period.value = period;

        reset_product_revenue_cost_period(type);
    });

    $('.revenue_quarter').click(function() {
        var type = 'revenue';
        var period = 'quarter';
        drawRevenueChart(type, period);
        draw_revenue_cost_product_type_pie_chart(type, period);

        //set button color
        set_button_color(type, period);
        unset_button_color(type, "week");
        unset_button_color(type, "month");
        unset_button_color(type, "year");

        //    change revenue_period_week_month_quarter value
        var revenue_period = document.getElementById("revenue_period_week_month_quarter");
        revenue_period.value = period;

        reset_product_revenue_cost_period(type);
    });

    $('.revenue_year').click(function() {
        var type = 'revenue';
        var period = 'year';
        drawRevenueChart(type, period);
        draw_revenue_cost_product_type_pie_chart(type, period);

        //set button color
        set_button_color(type, period);
        unset_button_color(type, "week");
        unset_button_color(type, "month");
        unset_button_color(type, "quarter");

        //    change revenue_period_week_month_quarter value
        var revenue_period = document.getElementById("revenue_period_week_month_quarter");
        revenue_period.value = period;

        reset_product_revenue_cost_period(type);
    });

    $('#revenue_period_week_month_quarter').change(function() {
        var type = 'revenue';

        var e = document.getElementById("revenue_period_week_month_quarter");
        var period = e.options[e.selectedIndex].value;

        drawRevenueChart(type, period);
        reset_product_revenue_cost_period(type);
        draw_revenue_cost_product_type_pie_chart(type, period);
    });

    $('#cost_period_week_month_quarter').change(function() {
        var type = 'cost';

        var e = document.getElementById("cost_period_week_month_quarter");
        var period = e.options[e.selectedIndex].value;

        drawRevenueChart(type, period);
        reset_product_revenue_cost_period(type);
        draw_revenue_cost_product_type_pie_chart(type, period);
    });

    $('#revenue_product_type').change(function() {
        var type = 'revenue';
        reset_product_revenue_cost_period(type);
    });

    // cost
    $('.cost_week').click(function() {
        var type = 'cost';
        var period = 'week';
        drawRevenueChart(type, period);
        draw_revenue_cost_product_type_pie_chart(type, period);

        //set button color
        set_button_color(type, period);
        unset_button_color(type, "quarter");
        unset_button_color(type, "month");
        unset_button_color(type, "year");

        //    change cost_period_week_month_quarter value
        var cost_period = document.getElementById("cost_period_week_month_quarter");
        cost_period.value = period;

        reset_product_revenue_cost_period(type);
    });

    $('.cost_month').click(function() {
        var type = 'cost';
        var period = 'month';
        drawRevenueChart(type, period);
        draw_revenue_cost_product_type_pie_chart(type, period);

        //set button color
        set_button_color(type, period);
        unset_button_color(type, "week");
        unset_button_color(type, "quarter");
        unset_button_color(type, "year");

        //    change cost_period_week_month_quarter value
        var cost_period = document.getElementById("cost_period_week_month_quarter");
        cost_period.value = period;

        reset_product_revenue_cost_period(type);
    });

    $('.cost_quarter').click(function() {
        var type = 'cost';
        var period = 'quarter';
        drawRevenueChart(type, period);
        draw_revenue_cost_product_type_pie_chart(type, period);

        //set button color
        set_button_color(type, period);
        unset_button_color(type, "week");
        unset_button_color(type, "month");
        unset_button_color(type, "year");

        //    change cost_period_week_month_quarter value
        var cost_period = document.getElementById("cost_period_week_month_quarter");
        cost_period.value = period;

        reset_product_revenue_cost_period(type);
    });

    $('.cost_year').click(function() {
        var type = 'cost';
        var period = 'year';
        drawRevenueChart(type, period);
        draw_revenue_cost_product_type_pie_chart(type, period);

        //set button color
        set_button_color(type, period);
        unset_button_color(type, "week");
        unset_button_color(type, "month");
        unset_button_color(type, "quarter");

        //    change cost_period_week_month_quarter value
        var cost_period = document.getElementById("cost_period_week_month_quarter");
        cost_period.value = period;

        reset_product_revenue_cost_period(type);
    });

    $('#cost_product_type').change(function() {
        var type = 'cost';
        reset_product_revenue_cost_period(type);
    });

    // revenue or cost
    $('.revenue').click(function() {
        //change hidden panel
        var revenue_tab = document.getElementById("revenue_tab");
        revenue_tab.className = "";

        var revenue_tab = document.getElementById("cost_tab");
        revenue_tab.className = "hidden-panel";

        // change button color
        var revenue_button = document.getElementById("revenue");
        revenue_button.className = "revenue selected_button";

        var cost_button = document.getElementById("cost");
        cost_button.className = "cost";
    });

    $('.cost').click(function() {
        //change hidden panel
        var revenue_tab = document.getElementById("revenue_tab");
        revenue_tab.className = "hidden-panel";

        var revenue_tab = document.getElementById("cost_tab");
        revenue_tab.className = "";

        // change button color
        var revenue_button = document.getElementById("revenue");
        revenue_button.className = "revenue";

        var cost_button = document.getElementById("cost");
        cost_button.className = "cost selected_button";
    });

    $('#product_and_service_period').change(function () {
        drawProductServiceRatePieChart();
        drawtop10_service_package_ratePieChart();
        drawtop10_service_ratePieChart();
        top10_product_ratePieChart();
    });

    $('#stock_location_selection').change(function () {
        draw_top_inventory_value();
        draw_top_inventory_qty();
    });

    $('#top_purchase_qty_period').change(function () {
        draw_top_purchase_qty_chart();
    });

    $('#top_purchase_value_period').change(function () {
        set_top_purchase_value_item();
    });

    $('#top_supplier_period').change(function () {
        draw_top_supplier_qty_chart();
        draw_top_supplier_value_chart();
    });

    $('#top_revenue_customer_period').change(function () {
        fill_top_revenue_customer();
    });

    $('#top_sale_again_period').change(function () {
        fill_top_sale_again();
    });

    $('#top_delivery_period').change(function () {
        fill_top_delivery();
    });

});

odoo.define('btek_summary_dashboard.chart', function (require) {
    "use strict";

    function drawChart() {
        var period = 'week';
        var type = 'revenue';
        drawCarInChart(period);
        drawCarInPieChart();
        drawRevenueChart(type, period);
        draw_revenue_cost_product_type_pie_chart(type, period);
        type = 'cost';
        drawRevenueChart(type, period);
        draw_revenue_cost_product_type_pie_chart(type, period);
        drawCustomerPieChart();
        drawCustomerMultiLineChart(period);
        draw_return_customer_rate_bar_chart();
        draw_customer_number_times_chart();

        //top revenue customer
        $('#top_revenue_customer_period').change();

        //product and service block
        $('#product_and_service_period').change();

        // drawtop10_service_package_ratePieChart();
        // drawProductServiceRatePieChart();

        // inventory block
        draw_qty_inventory_by_warehouse_rate();
        draw_value_inventory_by_warehouse_rate();
        draw_top_inventory_qty();
        draw_top_inventory_value();

        //purchase block
        $('#top_purchase_qty_period').change();
        $('#top_purchase_value_period').change();

        //supplier block
        $('#top_supplier_period').change();

        //sale again
        $('#top_sale_again_period').change();

        //top delivery
        $('#top_delivery_period').change();

    };

    window.onload = function(){
        PieChartExtend();
        drawChart();
    };

});
