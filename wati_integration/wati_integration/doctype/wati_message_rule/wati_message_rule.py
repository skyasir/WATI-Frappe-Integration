# Copyright (c) 2024, Yasir Shaikh and contributors
# For license information, please see license.txt

import json

import frappe
import requests
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate, parse_val
from frappe.utils.safe_exec import get_safe_globals

REQUEST_TIMEOUT = 30


class WatiMessageRule(Document):
	def validate(self):
		self.validate_mobile_no_field()
		if self.conditions:
			self.validate_condition()

	def validate_condition(self):
		temp_doc = frappe.new_doc(self.ref_doctype)
		try:
			frappe.safe_eval(self.conditions, None, get_context(temp_doc.as_dict()))
		except Exception:
			frappe.throw(_("The Condition '{0}' is invalid").format(self.conditions))

	def validate_mobile_no_field(self):
		if not self.mobile_no_field:
			frappe.throw(_("Select Mobile No Field Name."))

	@frappe.whitelist()
	def set_variable(self):
		"""Populate template variable rows from the selected Message Template."""
		if not self.message_template:
			self.template_variable = []
			return

		template_doc = frappe.get_doc("Message Template", self.message_template)
		if not template_doc.template_variables:
			return

		for variable in template_doc.template_variables.split(","):
			exists = frappe.db.exists(
				"Template Variable",
				{
					"template_variable": variable,
					"parenttype": "Wati Message Rule",
					"ref_doctype": self.ref_doctype,
					"parent": self.name,
				},
			)
			if not exists:
				self.append(
					"template_variable",
					{"template_variable": variable, "ref_doctype": self.ref_doctype},
				)


def get_context(doc):
	return {
		"doc": doc,
		"nowdate": nowdate,
		"frappe": frappe._dict(utils=get_safe_globals().get("frappe").get("utils")),
	}


def send_message_for_event(doc, method):
	try:
		if (
			(frappe.flags.in_import and frappe.flags.mute_emails)
			or frappe.flags.in_patch
			or frappe.flags.in_install
		):
			return
		get_message_rule(doc, doc.doctype, method)
	except Exception:
		frappe.log_error(title="Wati Error Log", message=frappe.get_traceback())


def get_message_rule(self, doctype, method):
	event_map = {
		"on_submit": "Submit",
		"after_insert": "New",
		"on_cancel": "Cancel",
		"after_save": "Save",
	}
	if not self.flags.in_insert:
		# value change is not applicable on insert
		event_map["on_change"] = "Value Change"

	based_on = event_map.get(method)
	if not based_on:
		return

	rules = frappe.get_all(
		"Wati Message Rule",
		filters={"based_on": based_on, "ref_doctype": doctype, "enable": 1},
		fields=["name", "conditions", "fields"],
	)
	if rules:
		evaluate_message_rule(self, based_on, rules)


def evaluate_message_rule(self, based_on, rules):
	for rule in rules:
		context = get_context(self)
		if context and rule.conditions:
			if not frappe.safe_eval(rule.conditions, None, context):
				continue

		if based_on == "Value Change" and not self.is_new():
			if not frappe.db.has_column(self.doctype, rule.fields):
				continue

			doc_before_save = self.get_doc_before_save()
			field_value_before_save = doc_before_save.get(rule.fields) if doc_before_save else None
			field_value_before_save = parse_val(field_value_before_save)

			if self.get(rule.fields) == field_value_before_save:
				# value not changed
				continue
			send_message_using_template(self, rule)
		else:
			send_message_using_template(self, rule)


def send_message_using_template(self, rule):
	rule = frappe.get_doc("Wati Message Rule", rule.name)
	data = []
	for field in rule.template_variable:
		data.append(
			{
				"name": field.get("template_variable"),
				"value": self.get(field.get("document_variable")),
			}
		)
	send_whatsapp_message(
		rule.message_template,
		self.get(rule.mobile_no_field),
		json.dumps(data),
		self.name,
		self.doctype,
	)


def send_whatsapp_message(template, mobile, data, document, doctype):
	wati_setting = frappe.get_single("Wati Setting")
	if not wati_setting.url or not wati_setting.whatsapp_number or not wati_setting.token:
		frappe.throw(
			_("URL, WhatsApp Number and Token are mandatory in Wati Setting to send a WhatsApp message")
		)

	if not mobile:
		return

	base_url = wati_setting.url.rstrip("/") + "/api/v1/sendTemplateMessage"
	params = {"whatsappNumber": str(mobile)}

	payload = json.dumps(
		{
			"template_name": template,
			"broadcast_name": template,
			"parameters": json.loads(data) if isinstance(data, str) else data,
		}
	)
	headers = {
		"Authorization": "Bearer " + wati_setting.token,
		"Content-Type": "application/json",
	}

	response = requests.post(
		base_url, params=params, data=payload, headers=headers, timeout=REQUEST_TIMEOUT
	)

	frappe.get_doc(
		{
			"doctype": "Wati Message Log",
			"mobile_no": mobile,
			"url": response.url,
			"payload": payload,
			"headers": json.dumps(headers),
			"status_code": response.status_code,
			"response": response.text,
			"document": document,
			"ref_doctype": doctype,
		}
	).insert(ignore_permissions=True)

	frappe.msgprint(
		_("WhatsApp message sent to {0}").format(mobile), alert=True, indicator="green"
	)
