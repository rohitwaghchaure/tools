cur_frm.add_fetch('item_code', 'item_name', 'item_name');

// cur_frm.add_fetch('serial_no', 'item_name', 'item_name');




cur_frm.cscript.serial_no = function(doc, cdt, cdn){
    var d = locals[cdt][cdn]
    get_server_fields('check_availabilty',d.serial_no,'',doc, cdt, cdn, 1 , function(doc, cdt, cdn){
   });
};


cur_frm.cscript.add= function(doc, cdt, cdn) {
	var d = locals[cdt][cdn];
	d.serial_nos=d.serial_no;
	refresh_field('serial_nos',d.name,'tool_maintainance');
};

// cur_frm.cscript.refresh = function(doc, cdt, cdn){
// 	get_server_fields('render_table_data','','', doc, cdt, cdn, 1 , function(){
// 		refresh_field('tool_maintainance')
// 	})
// }



cur_frm.cscript.process = function(doc, cdt, cdn){
	get_server_fields('get_maintenance_details','','', doc, cdt, cdn, 1 , function(){
		refresh_field('tool_maintainance')
	})
}

cur_frm.fields_dict.tool_maintainance.grid.get_field("serial_no").get_query = function(doc, cdt, cdn) {
	var d=locals[cdt][cdn]
	return {
		filters: {
			"item_code": d.item_code
		}
	}
}

// cur_frm.fields_dict.tool_maintainance.grid.get_field("item_code").get_query = function(doc) {
// 	var d=locals[cdt][cdn]
// 	return {
// 		filters: {
// 			"item_group": "Tools"
// 		}
// 	}
// }