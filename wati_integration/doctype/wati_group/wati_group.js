// Copyright (c) 2024, Yasir Shaikh and contributors
// For license information, please see license.txt

frappe.ui.form.on("Wati Group", {
	reference_doctype: function (frm) {
		frm.clear_table("wati_group_details");
		(frm.doc.wati_group_details || []).forEach(function (d) {
			d.document_type = frm.doc.reference_doctype;
		});
		frm.refresh_field("wati_group_details");
	},
});

frappe.ui.form.on("Wati Group Details", {
	wati_group_details_add: function (frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		if (frm.doc.reference_doctype) {
			row.document_type = frm.doc.reference_doctype;
			frm.refresh_field("wati_group_details");
		} else {
			frm.script_manager.copy_from_first_row("wati_group_details", row, ["document_type"]);
		}
	},
	group_member: function (frm, cdt, cdn) {
		const row = locals[cdt][cdn];
		frappe.model.set_value(cdt, cdn, "mobile_no", "");
		if (!row.group_member) {
			return;
		}
		frappe.call({
			method: "wati_integration.wati_integration.doctype.wati_group.wati_group.get_mobile_no",
			args: {
				group_member: row.group_member,
				document_type: row.document_type,
			},
			callback: function (r) {
				if (r.message) {
					frappe.model.set_value(cdt, cdn, "mobile_no", r.message);
				}
			},
		});
	},
});
