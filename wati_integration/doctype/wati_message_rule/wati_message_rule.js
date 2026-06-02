// Copyright (c) 2024, Yasir Shaikh and contributors
// For license information, please see license.txt

frappe.ui.form.on("Wati Message Rule", {
	onload: function (frm) {
		frm.set_query("ref_doctype", function () {
			return { filters: { istable: 0 } };
		});
	},

	setup: function (frm) {
		frm.trigger("setup_fieldname_select");
	},

	refresh: function (frm) {
		frm.trigger("setup_fieldname_select");

		if (!frm.is_new() && !frappe.user.has_role("System Manager")) {
			const meta = frappe.get_meta("Wati Message Rule");
			(meta.fields || []).forEach(function (df) {
				if (!["Section Break", "Column Break"].includes(df.fieldtype)) {
					frm.set_df_property(df.fieldname, "read_only", 1);
				}
			});
		}
	},

	ref_doctype: function (frm) {
		frm.trigger("setup_fieldname_select");
		frm.set_value("message_template", "");
	},

	message_template: function (frm) {
		if (frm.doc.message_template) {
			frm.call("set_variable").then(() => {
				frm.refresh_field("template_variable");
			});
		}
	},

	setup_fieldname_select: function (frm) {
		if (!frm.doc.ref_doctype) {
			return;
		}

		frappe.model.with_doctype(frm.doc.ref_doctype, function () {
			const get_select_options = function (df, parent_field) {
				const value = parent_field ? df.fieldname + "," + parent_field : df.fieldname;
				return {
					value: value,
					label: df.fieldname + " (" + __(df.label) + ")",
				};
			};

			const fields = frappe.get_doc("DocType", frm.doc.ref_doctype).fields;
			const options = $.map(fields, function (d) {
				return in_list(frappe.model.no_value_type, d.fieldtype)
					? null
					: get_select_options(d);
			});

			frm.set_df_property("fields", "options", [""].concat(options));
			frm.set_df_property("mobile_no_field", "options", [""].concat(options));

			frappe.meta.get_docfield(
				"Template Variable",
				"document_variable",
				frm.doc.name
			).options = [""].concat(options);

			frm.fields_dict.template_variable.grid.refresh();
		});
	},
});
