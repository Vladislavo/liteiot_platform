var var_ctr = 1;
var raw_types = {
	"float" : {"type":"f", "size":4},
	"bool" : {"type":"?", "size":1},
	"string" : {"type":"s"},
	"uint8_t" : {"type":"B", "size":1},
	"uint16_t" : {"type":"H", "size":2},
	"uint32_t" : {"type":"I", "size":4},
	"uint64_t" : {"type":"Q", "size":8},
	"int8_t" : {"type":"b", "size":1},
	"int16_t" : {"type":"h", "size":2},
	"int32_t" : {"type":"i", "size":4},
	"int64_t" : {"type":"q", "size":8},
};
var json_types = ["number", "string", "boolean"];

function set_ctr(id) {
	var_ctr = id
}
function add_variable_name(id, type, name) {
	var div = document.createElement("div");
	var lg = 6;
	if (type == "raw") {
		lg = 4
	}
	div.setAttribute("class", "col-lg-"+lg);

	var div_fg = document.createElement("div");
	div_fg.setAttribute("class", "form-group");

	var label = document.createElement("label");
	label.setAttribute("for", "varname_"+id);
	label.innerHTML = "Variable name:";
	
	var input = document.createElement("input");
	input.setAttribute("type", "text");
	input.setAttribute("maxlength", "30");
	input.setAttribute("class", "form-control");
	input.setAttribute("id", "varname_"+id);
	input.setAttribute("name", "varname_"+id);
	input.setAttribute("required", "true");

	if (typeof name !== "undefined") {
		input.setAttribute("value", name);
	}

	div_fg.appendChild(label);
	div_fg.appendChild(input);
	div.appendChild(div_fg);

	return div;
}

function add_variable_type(id, type, typev) {
	var div = document.createElement("div");
	var lg = 5;
	if (type == "raw") {
		lg = 3;
	}
	div.setAttribute("class", "col-lg-"+lg);

	var div_fg = document.createElement("div");
	div_fg.setAttribute("class", "form-group");

	var label = document.createElement("label");
	label.setAttribute("for", "vartype_"+id);
	label.innerHTML = "Type:";
	
	var select = document.createElement("select");
	select.setAttribute("id", "vartype_"+id);
	select.setAttribute("name", "vartype_"+id);
	select.setAttribute("class", "form-control");
	select.setAttribute("onchange", "return onvartype('"+id+"');");
	if (type == "raw") {
		for (var t in raw_types) {
			var option = document.createElement("option");
			option.setAttribute("value", raw_types[t].type);
			option.text = t;
			select.appendChild(option);
		}
	} else if (type == "json" || type == "mpack") {
		json_types.forEach(function(t) {
			var option = document.createElement("option");
			option.setAttribute("value", t);
			option.text = t;
			select.appendChild(option);
		});
	}
	if (typeof typev !== "undefined") {
		if (typev[typev.length-1] == 's') {
			select.value = typev[typev.length-1];
		} else {
			select.value = typev;
		}
	}

	div_fg.appendChild(label);
	div_fg.appendChild(select);
	div.appendChild(div_fg);

	return div;
}

function add_variable_size(id, type, typev) {
	var div = document.createElement("div");
	div.setAttribute("class", "col-lg-3");

	var div_fg = document.createElement("div");
	div_fg.setAttribute("class", "form-group");

	var label = document.createElement("label");
	label.setAttribute("for", "varsize_"+id);
	label.innerHTML = "Size:";
	
	var input = document.createElement("input");
	input.setAttribute("type", "number");
	input.setAttribute("min", "1");
	input.setAttribute("max", "256");
	input.setAttribute("class", "form-control");
	input.setAttribute("id", "varsize_"+id);
	input.setAttribute("name", "varsize_"+id);
	input.setAttribute("disabled", "true");
	if (typeof typev !== "undefined") {
		if (typev[typev.length-1] == 's') {
			var size = typev.substring(0, typev.length-1);
			input.setAttribute("value", size);
			input.disabled = false;
		} else {
			for (var t in raw_types) {
				if (raw_types[t]['type'] == typev) {
					input.setAttribute("value", raw_types[t]['size']);
				}
			}
		}
	} else {
		input.setAttribute("value", "4");
	}

	div_fg.appendChild(label);
	div_fg.appendChild(input);
	div.appendChild(div_fg);

	return div;
}

function add_variable_rm(id) {
	var div = document.createElement("div");
	div.setAttribute("class", "col-lg-1");

	var a = document.createElement("a");
	a.setAttribute("href", "javascript:void(0)");
	a.setAttribute("onclick", "return remove_variable('"+id+"');");
	var span = document.createElement("span");
	span.setAttribute("class", "fa fa-remove");

	a.appendChild(span);
	div.appendChild(a);

	return div;
}

function add_variable(type, name, typev) {
	var row = document.createElement("div");
	row.setAttribute("class", "row");
	row.setAttribute("id", "variable"+var_ctr);

	var variable_name = add_variable_name(var_ctr, type, name);
	var variable_type = add_variable_type(var_ctr, type, typev);
	if (type == "raw") {	
		var variable_size = add_variable_size(var_ctr, type, typev);
	}
	var variable_rm = add_variable_rm(var_ctr);
	
	row.appendChild(variable_name);
	row.appendChild(variable_type);
	if (type == "raw") {	
		row.appendChild(variable_size);
	}
	row.appendChild(variable_rm);

	var_ctr++;

	return row;
}

function remove_variable(id) {
	$("#variable"+id).remove();
}

function add_variable_link() {
	var div = document.createElement("div");
	div.setAttribute("class", "col-lg-12");
	div.setAttribute("id", "addvarlink");

	var center = document.createElement("center");
	var a = document.createElement("a");
	a.setAttribute("href", "javascript:void(0)");
	a.onclick = add_new_variable;
	a.text = "Add variable";

	center.appendChild(a);
	div.appendChild(center);
	
	return div;
}

function add_endianness(ddm) {
	var div = document.createElement("div");
	div.setAttribute("class", "form-group");

	var label = document.createElement("label");
	label.setAttribute("for", "endianness");
	label.innerHTML = "Endianness:";

	var select = document.createElement("select");
	select.setAttribute("id", "endianness");
	select.setAttribute("name", "endianness");
	select.setAttribute("class", "form-control");
	
	var little = document.createElement("option");
	little.setAttribute("value", "<");
	little.text = "Little Endian"
	var big = document.createElement("option");
	big.setAttribute("value", ">");
	big.text = "Big Endian";

	if (typeof ddm !== "undefined") {
		select.value = ddm['endianness'];
	}

	select.appendChild(little);
	select.appendChild(big);

	div.appendChild(label);
	div.appendChild(select);

	return div;
}

function add_ddm_ext(type, ddm) {
	var ddm_div = document.createElement("div");
	ddm_div.setAttribute("id", "ddm_ext");

	if (type == "raw") {
		var endianness = add_endianness(ddm);
		ddm_div.appendChild(endianness);
	}
	if (typeof ddm !== "undefined") {
		for (var v in ddm['format'])  {
			var variable = add_variable(type, v, ddm['format'][v]);
			ddm_div.appendChild(variable);
		}
	} else {
		var variable = add_variable(type);
		ddm_div.appendChild(variable);
	}

	var div = document.getElementById("ddm_div");
	div.appendChild(ddm_div);

	var add_var = add_variable_link();
	div.appendChild(add_var);
}

function add_new_variable() {
	var ddm_div = document.getElementById("ddm_ext");
	var ddm_sel = document.getElementById("ddm");
	var sel_op = ddm_sel.options[ddm_sel.selectedIndex].value;
	ddm_div.appendChild(add_variable(sel_op));
}

function onddm() {
	$("#ddm_ext").remove();
	$("#addvarlink").remove();
	var ddm_sel = document.getElementById("ddm");
	var sel_op = ddm_sel.options[ddm_sel.selectedIndex].value;
	add_ddm_ext(sel_op);
}

function onddmsetting() {
	var ddm_sel = document.getElementById("ddm");
	ddm_sel.value = device_data_model['model'];
	add_ddm_ext(device_data_model['model'], device_data_model);
}

function onvartype(id) {
	var type_sel = document.getElementById("vartype_"+id);
	var sel_op = type_sel.options[type_sel.selectedIndex];
	if (sel_op.value == "s") {
		document.getElementById("varsize_"+id).disabled = false;
		document.getElementById("varsize_"+id).setAttribute("value", "");
	} else {
		document.getElementById("varsize_"+id).value = raw_types[sel_op.text].size; 
		document.getElementById("varsize_"+id).setAttribute("disabled", "true");
	}
}

$(document).ready(function () {
	if (typeof device_data_model === "undefined") {
		onddm();
	} else {
		onddmsetting();
	}
});
