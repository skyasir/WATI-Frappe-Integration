# Copyright (c) 2022, Yasir Shaikh and contributors
# For license information, please see license.txt

import json

import requests
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import nowdate, parse_val
from frappe.utils.safe_exec import get_safe_globals


class WatiMessageRule(Document):
	def validate(self):
		self.validate_mobile_no_field()
		if self.conditions:
			self.validate_condition()

	def validate_condition(self):
		temp_doc = frappe.new_doc(self.ref_doctype)
		if self.conditions:
			try:
				frappe.safe_eval(self.conditions, None, get_context(temp_doc.as_dict()))
			except Exception:
				frappe.throw(_("The Condition '{0}' is invalid").format(self.conditions))

	def validate_mobile_no_field(self):
		if not self.mobile_no_field:
			frappe.throw(_("Select Mobile No Field Name."))

	@frappe.whitelist()
	def set_variable(self):
		if self.message_template:
			template_doc = frappe.get_doc("Message Template", self.message_template)
			for variable in template_doc.template_variables.split(","):
				if not frappe.db.exists(
					"Template Variable",
					{
						"template_variable": variable,
						"parenttype": "Wati Message Rule",
						"ref_doctype": self.ref_doctype,
						"parent": self.name,
					},
				):
					self.append(
						"template_variable",
						dict(template_variable=variable, ref_doctype=self.ref_doctype),
					)
		else:
			self.template_variable = []


def get_context(doc):
	safe_globals = get_safe_globals()
	frappe_utils = safe_globals.get("frappe", {}).get("utils", {})
	return {
		"doc": doc,
		"nowdate": nowdate,
		"frappe": frappe._dict(utils=frappe_utils),
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
		event_map["on_change"] = "Value Change"

	based_on = event_map.get(method)
	if not based_on:
		return

	rules = frappe.get_all(
		"Wati Message Rule",
		filters={"based_on": based_on, "ref_doctype": doctype, "enable": 1},
		fields=["*"],
	)
	if rules:
		evalute_message_rule(self, based_on, rules)


def evalute_message_rule(self, based_on, rules):
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
				continue
			else:
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
	wati_setting = frappe.get_doc("Wati Setting", "Wati Setting")
	if (
		not wati_setting.url
		or not wati_setting.get("whatsapp_number")
		or not wati_setting.get("token")
	):
		frappe.throw(
			_(
				"URL, WhatsApp Number and Token are mandatory in Wati Setting to send WhatsApp messages"
			)
		)

	base_url = (
		wati_setting.get("url").rstrip("/")
		+ "/api/v1/sendTemplateMessage/"
		+ str(mobile)
		+ "?whatsappNumber="
		+ wati_setting.get("whatsapp_number")
	)
	payload = json.dumps(
		{
			"template_name": template,
			"broadcast_name": template,
			"parameters": data,
		}
	)
	headers = {
		"Authorization": "Bearer " + wati_setting.get("token"),
		"Content-Type": "application/json",
	}

	response = requests.post(base_url, data=payload, headers=headers)

	frappe.get_doc(
		dict(
			doctype="Wati Message Log",
			mobile_no=mobile,
			url=base_url,
			payload=payload,
			headers=json.dumps(headers),
			status_code=str(response.status_code),
			response=response.text,
			document=document,
			ref_doctype=doctype,
		)
	).insert(ignore_permissions=True)

	frappe.msgprint(
		_("WhatsApp message sent to {0}").format(mobile), alert=True, indicator="green"
	)
