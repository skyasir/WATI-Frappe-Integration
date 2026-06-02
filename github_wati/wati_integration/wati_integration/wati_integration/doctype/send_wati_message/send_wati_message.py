# Copyright (c) 2022, Yasir Shaikh and contributors
# For license information, please see license.txt

import json
from datetime import timedelta

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime

from wati_integration.wati_integration.doctype.wati_message_rule.wati_message_rule import (
	send_whatsapp_message,
)


class SendWatiMessage(Document):
	@frappe.whitelist()
	def get_variables(self):
		if self.message_template:
			self.send_message_variables = []
			message_template_doc = frappe.get_doc("Message Template", self.message_template)
			if message_template_doc.template_variables:
				for row in message_template_doc.template_variables.split(","):
					self.append("send_message_variables", dict(template_variable=row.strip()))
		else:
			self.send_message_variables = []

	def on_submit(self):
		if self.when_to_send == "Now":
			send_message(self)
		else:
			frappe.db.set_value("Send Wati Message", self.name, "status", "Scheduled")


@frappe.whitelist()
def cron_job_for_schedule_message():
	from_time = now_datetime()
	send_sms_data = frappe.db.sql(
		"""SELECT name
		FROM `tabSend Wati Message`
		WHERE docstatus=1
		  AND sent=0
		  AND schedule_date_and_time < %s""",
		from_time,
		as_dict=1,
	)
	frappe.enqueue(enqueue_send_message, send_sms_data=send_sms_data, queue="long")


def enqueue_send_message(send_sms_data):
	for row in send_sms_data:
		send_sms_doc = frappe.get_doc("Send Wati Message", row.name)
		send_message(send_sms_doc)
		frappe.db.set_value("Send Wati Message", row.name, "sent", 1)


def send_message(doc):
	if doc.message_send_to == "All Supplier":
		send_message_supplier(doc)
	elif doc.message_send_to == "All Employee":
		send_message_employee(doc)
	elif doc.message_send_to == "All Customer":
		send_message_customer(doc)
	elif doc.message_send_to == "All Lead":
		send_message_lead(doc)
	elif doc.message_send_to == "Group":
		send_message_group(doc)


def send_message_supplier(doc):
	for row in frappe.get_all("Supplier", filters={"disabled": 0}, fields=["name", "mobile_no"]):
		if row.get("mobile_no"):
			send_whatsapp_message(
				doc.message_template,
				row.get("mobile_no"),
				get_template_data(doc),
				doc.name,
				doc.doctype,
			)


def send_message_employee(doc):
	for row in frappe.get_all(
		"Employee",
		filters={"status": "Active"},
		fields=["name", "cell_number as mobile_no"],
	):
		if row.get("mobile_no"):
			send_whatsapp_message(
				doc.message_template,
				row.get("mobile_no"),
				get_template_data(doc),
				doc.name,
				doc.doctype,
			)


def send_message_customer(doc):
	for row in frappe.get_all("Customer", filters={"disabled": 0}, fields=["name", "mobile_no"]):
		if row.get("mobile_no"):
			send_whatsapp_message(
				doc.message_template,
				row.get("mobile_no"),
				get_template_data(doc),
				doc.name,
				doc.doctype,
			)


def send_message_lead(doc):
	for row in frappe.get_all("Lead", filters={}, fields=["name", "mobile_no"]):
		if row.get("mobile_no"):
			send_whatsapp_message(
				doc.message_template,
				row.get("mobile_no"),
				get_template_data(doc),
				doc.name,
				doc.doctype,
			)


def send_message_group(doc):
	group_doc = frappe.get_doc("Wati Group", doc.group)
	for row in group_doc.wati_group_details:
		if row.enable and row.get("mobile_no"):
			send_whatsapp_message(
				doc.message_template,
				row.get("mobile_no"),
				get_template_data(doc),
				doc.name,
				doc.doctype,
			)


def get_template_data(doc):
	data = []
	for field in doc.send_message_variables:
		data.append({"name": field.get("template_variable"), "value": field.get("value")})
	return json.dumps(data)
