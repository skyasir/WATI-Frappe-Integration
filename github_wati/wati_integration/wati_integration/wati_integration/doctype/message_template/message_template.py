# Copyright (c) 2022, Yasir Shaikh and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document


class MessageTemplate(Document):
	def validate(self):
		if not self.template_message:
			frappe.throw(_("Template Message is required."))
		try:
			self.template_message.format()
		except Exception:
			frappe.throw(_("Invalid Message Format"))

		res = re.findall(r"\{.*?\}", self.template_message)
		variables = []
		for variable in res:
			variable = variable.strip("{}")
			if variable and variable not in variables:
				variables.append(variable)
		self.template_variables = ",".join(variables)
