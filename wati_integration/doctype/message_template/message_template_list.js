// Copyright (c) 2024, Yasir Shaikh and contributors
// For license information, please see license.txt

frappe.listview_settings["Message Template"] = {
	onload: function (listview) {
		listview.page.add_inner_button(__("Fetch from WATI"), function () {
			frappe.dom.freeze(__("Fetching approved templates from WATI..."));
			frappe
				.call("wati_integration.wati_integration.doctype.wati_setting.wati_setting.fetch_templates")
				.then((r) => {
					frappe.dom.unfreeze();
					if (r.exc) {
						return;
					}
					const m = r.message || {};
					frappe.msgprint({
						title: __("Templates Synced"),
						indicator: "green",
						message: __("Created: {0}, Updated: {1}, Skipped: {2}", [
							m.created || 0,
							m.updated || 0,
							m.skipped || 0,
						]),
					});
					listview.refresh();
				})
				.catch(() => frappe.dom.unfreeze());
		});
	},
};
