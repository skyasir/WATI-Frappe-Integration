// Copyright (c) 2024, Yasir Shaikh and contributors
// For license information, please see license.txt

frappe.ui.form.on("Send Wati Message", {
	message_template: function (frm) {
		if (!frm.doc.message_template) {
			return;
		}
		frm.call({
			method: "get_variables",
			doc: frm.doc,
			callback: function () {
				frm.refresh_field("send_message_variables");
			},
		});
	},
});
