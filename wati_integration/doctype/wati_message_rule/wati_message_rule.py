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


def get_wati_setting():
	"""Return the Wati Setting single doc, validating that creds are present."""
	wati_setting = frappe.get_single("Wati Setting")
	if not wati_setting.url or not wati_setting.token:
		frappe.throw(_("URL and Token are mandatory in Wati Setting."))
	return wati_setting


def get_wati_headers(wati_setting):
	"""Build the auth headers, tolerating a token pasted with a 'Bearer ' prefix."""
	token = (wati_setting.token or "").strip()
	if token.lower().startswith("bearer "):
		token = token[7:].strip()
	return {
		"Authorization": "Bearer " + token,
		"Content-Type": "application/json",
	}


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


@frappe.whitelist()
def get_send_button_doctypes():
	"""Doctypes that have an enabled rule with an Additional Message template.

	The global form script uses this to decide where to show the
	'Send to WhatsApp' button.
	"""
	rows = frappe.get_all(
		"Wati Message Rule",
		filters={"enable": 1, "additional_message_template": ["is", "set"]},
		fields=["ref_doctype"],
	)
	return sorted({r.ref_doctype for r in rows if r.ref_doctype})


@frappe.whitelist()
def send_for_document(rule_doctype, docname):
	"""Send the configured Additional Message template for one document.

	Recipient comes from the rule's `mobile_no_field` read off the document.
	"""
	rules = frappe.get_all(
		"Wati Message Rule",
		filters={
			"enable": 1,
			"ref_doctype": rule_doctype,
			"additional_message_template": ["is", "set"],
		},
		fields=["name", "mobile_no_field", "additional_message_template"],
	)
	if not rules:
		frappe.throw(
			_("No enabled Wati Message Rule with an Additional Message template exists for {0}.").format(
				rule_doctype
			)
		)

	doc = frappe.get_doc(rule_doctype, docname)
	sent = 0
	for rule in rules:
		if not rule.mobile_no_field:
			frappe.throw(_("Rule {0} has no Mobile No Field set.").format(rule.name))

		mobile = doc.get(rule.mobile_no_field)
		if not mobile:
			frappe.throw(
				_("No mobile number found in field '{0}' on this {1}.").format(
					rule.mobile_no_field, rule_doctype
				)
			)

		send_whatsapp_message(
			rule.additional_message_template,
			mobile,
			json.dumps([]),
			docname,
			rule_doctype,
		)
		sent += 1

	return {"sent": sent}


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
	wati_setting = get_wati_setting()

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
	headers = get_wati_headers(wati_setting)

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
