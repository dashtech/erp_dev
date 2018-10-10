function selected_sheet(selected_button_id) {
        var e_div = document.getElementById('content_sheet');
        var button_list = document.getElementById('button_list');
        for (var i = 0; i < e_div.childNodes.length; i++){
            var sheet_content = e_div.childNodes[i];
            var e_button = button_list.childNodes[i];

            var button_id = e_button.id;

            if (selected_button_id != button_id){
                sheet_content.className = 'sheet-content hidden-panel';
                e_button.className = 'sheet-button';
            }
            else {
                sheet_content.className = 'sheet-content';
                e_button.className = 'sheet-button selected_button';
            }
        }
    };

$(document).ready(function(){
    $('.sheet-button').click(function() {
        var selected_sheet_id = this.id;
        selected_sheet(selected_sheet_id);
    });
});

// odoo.define('btek_summary_dashboard.chart', function (require) {
//     "use strict";
//
//     window.onload = function(){
//         selected_sheet('sheet1');
//     };
//
// });