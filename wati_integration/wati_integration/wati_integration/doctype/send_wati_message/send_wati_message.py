# Copyright (c) 2024, Yasir Shaikh and contributors
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
		"""Populate variable rows from the selected Message Template."""
		self.send_message_variables = []
		if not self.message_template:
			return

		message_template_doc = frappe.get_doc("Message Template", self.message_template)
		if not message_template_doc.template_variables:
			return

		for row in message_template_doc.template_variables.split(","):
			self.append("send_message_variables", {"template_variable": row})

	def on_submit(self):
		# "Now" sends immediately; "Schedule" is picked up by the cron job
		# based on the `sent` flag and `schedule_date_and_time`.
		if self.when_to_send == "Now":
			send_message(self)


@frappe.whitelist()
def cron_job_for_schedule_message():
	from_time = now_datetime()

	scheduled = frappe.get_all(
		"Send Wati Message",
		filters={
			"docstatus": 1,
			"sent": 0,
			"when_to_send": "Schedule",
			"schedule_date_and_time": ["<", from_time],
		},
		pluck="name",
	)
	if scheduled:
		frappe.enqueue(enqueue_send_message, send_sms_data=scheduled, queue="long")


def enqueue_send_message(send_sms_data):
	for name in send_sms_data:
		doc = frappe.get_doc("Send Wati Message", name)
		send_message(doc)
		frappe.db.set_value("Send Wati Message", name, "sent", 1)


def send_message(doc):
	dispatch = {
		"All Supplier": send_message_supplier,
		"All Employee": send_message_employee,
		"All Customer": send_message_customer,
		"All Lead": send_message_lead,
		"Group": send_message_group,
	}
	handler = dispatch.get(doc.message_send_to)
	if handler:
		handler(doc)


def send_message_supplier(doc):
	rows = frappe.get_all("Supplier", filters={"disabled": 0}, fields=["name", "mobile_no"])
	_broadcast(doc, [(r.name, r.mobile_no) for r in rows])


def send_message_employee(doc):
	rows = frappe.get_all("Employee", filters={"status": "Active"}, fields=["name", "cell_number"])
	_broadcast(doc, [(r.name, r.cell_number) for r in rows])


def send_message_customer(doc):
	rows = frappe.get_all("Customer", filters={"disabled": 0}, fields=["name", "mobile_no"])
	_broadcast(doc, [(r.name, r.mobile_no) for r in rows])


def send_message_lead(doc):
	rows = frappe.get_all("Lead", fields=["name", "mobile_no"])
	_broadcast(doc, [(r.name, r.mobile_no) for r in rows])


def send_message_group(doc):
	group_doc = frappe.get_doc("Wati Group", doc.group)
	recipients = [
		(row.group_member, row.mobile_no)
		for row in group_doc.wati_group_details
		if row.enable and row.mobile_no
	]
	_broadcast(doc, recipients)


def _broadcast(doc, recipients):
	template_data = get_template_data(doc)
	for _name, mobile in recipients:
		if mobile:
			send_whatsapp_message(doc.message_template, mobile, template_data, doc.name, doc.doctype)


def get_template_data(doc):
	data = [
		{"name": field.get("template_variable"), "value": field.get("value")}
		for field in doc.send_message_variables
	]
	return json.dumps(data)
