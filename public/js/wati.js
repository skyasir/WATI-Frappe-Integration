// Copyright (c) 2024, Yasir Shaikh and contributors
// For license information, please see license.txt
//
// Global form script: shows a "Send to WhatsApp" button on any Document Type
// that has an enabled Wati Message Rule with an Additional Message template.

frappe.provide("wati_integration");

wati_integration._doctypes = null; // cache: array of doctype names
wati_integration._loading = null; // in-flight promise

wati_integration.load_doctypes = function () {
	if (wati_integration._doctypes !== null) {
		return Promise.resolve(wati_integration._doctypes);
	}
	if (wati_integration._loading) {
		return wati_integration._loading;
	}
	wati_integration._loading = frappe
		.call(
			"wati_integration.wati_integration.doctype.wati_message_rule.wati_message_rule.get_send_button_doctypes"
		)
		.then((r) => {
			wati_integration._doctypes = (r && r.message) || [];
			return wati_integration._doctypes;
		})
		.catch(() => {
			wati_integration._doctypes = [];
			return [];
		});
	return wati_integration._loading;
};

$(document).on("form-refresh", function (e, frm) {
	if (!frm || frm.is_new() || frm.doc.__islocal) {
		return;
	}
	wati_integration.load_doctypes().then((doctypes) => {
		if (!doctypes || !doctypes.includes(frm.doctype)) {
			return;
		}
		frm.add_custom_button(__("Send to WhatsApp"), function () {
			frappe.dom.freeze(__("Sending WhatsApp message..."));
			frappe
				.call(
					"wati_integration.wati_integration.doctype.wati_message_rule.wati_message_rule.send_for_document",
					{ rule_doctype: frm.doctype, docname: frm.doc.name }
				)
				.then((r) => {
					frappe.dom.unfreeze();
					if (!r.exc) {
						frappe.show_alert(
							{ message: __("WhatsApp message sent"), indicator: "green" },
							5
						);
					}
				})
				.catch(() => frappe.dom.unfreeze());
		});
	});
});
