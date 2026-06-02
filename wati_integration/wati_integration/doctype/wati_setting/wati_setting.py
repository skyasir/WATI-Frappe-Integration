# Copyright (c) 2024, Yasir Shaikh and contributors
# For license information, please see license.txt

import frappe
import requests
from frappe import _
from frappe.model.document import Document

from wati_integration.wati_integration.doctype.wati_message_rule.wati_message_rule import (
	REQUEST_TIMEOUT,
	get_wati_headers,
	get_wati_setting,
)


class WatiSetting(Document):
	@frappe.whitelist()
	def fetch_templates(self):
		"""Pull Meta-approved templates from WATI and upsert Message Template records."""
		return fetch_templates()


@frappe.whitelist()
def fetch_templates():
	wati_setting = get_wati_setting()
	url = wati_setting.url.rstrip("/") + "/api/v1/getMessageTemplates"
	headers = get_wati_headers(wati_setting)

	response = requests.get(
		url,
		params={"pageSize": 200, "pageNumber": 1},
		headers=headers,
		timeout=REQUEST_TIMEOUT,
	)
	if response.status_code != 200:
		frappe.throw(
			_("WATI returned {0} while fetching templates: {1}").format(
				response.status_code, response.text or "(empty response)"
			)
		)

	data = response.json() or {}
	# WATI has used a few keys across versions; check each.
	templates = (
		data.get("messageTemplates")
		or data.get("messageTemplateList")
		or data.get("result")
		or []
	)
	if not isinstance(templates, list):
		templates = []

	created, updated, skipped = 0, 0, 0
	for tpl in templates:
		status = (tpl.get("status") or "").upper()
		if status != "APPROVED":
			skipped += 1
			continue

		name = tpl.get("elementName") or tpl.get("templateName") or tpl.get("name")
		if not name:
			skipped += 1
			continue

		body = tpl.get("bodyOriginal") or tpl.get("body") or tpl.get("bodyText") or ""
		# WATI uses {{variable}}; the Message Template doctype detects {variable}.
		body = body.replace("{{", "{").replace("}}", "}")

		if frappe.db.exists("Message Template", name):
			doc = frappe.get_doc("Message Template", name)
			doc.template_message = body
			doc.save(ignore_permissions=True)
			updated += 1
		else:
			frappe.get_doc(
				{
					"doctype": "Message Template",
					"template_name": name,
					"template_message": body,
				}
			).insert(ignore_permissions=True)
			created += 1

	frappe.db.commit()
	return {"created": created, "updated": updated, "skipped": skipped, "total": len(templates)}
