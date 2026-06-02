// Copyright (c) 2024, Yasir Shaikh and contributors
// For license information, please see license.txt

frappe.ui.form.on("Wati Setting", {
	refresh: function (frm) {
		frm.add_custom_button(__("Fetch Templates"), function () {
			frappe.dom.freeze(__("Fetching approved templates from WATI..."));
			frm.call("fetch_templates")
				.then((r) => {
					frappe.dom.unfreeze();
					if (r.exc) {
						return;
					}
					const m = r.message || {};
					frappe.msgprint({
						title: __("Templates Synced"),
						indicator: "green",
						message: __(
							"Approved templates imported.<br>Created: {0}<br>Updated: {1}<br>Skipped (not approved): {2}",
							[m.created || 0, m.updated || 0, m.skipped || 0]
						),
					});
				})
				.catch(() => frappe.dom.unfreeze());
		});
	},
});
