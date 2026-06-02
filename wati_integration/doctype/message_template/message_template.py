# Copyright (c) 2024, Yasir Shaikh and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document


class MessageTemplate(Document):
	def validate(self):
		self.set_template_variables()

	def set_template_variables(self):
		"""Auto-detect {variable} placeholders in the message body."""
		self.template_variables = ""

		if not self.template_message:
			return

		# Validate the placeholders form a valid format string
		try:
			self.template_message.format()
		except (KeyError, IndexError):
			# Placeholders like {name} are expected here; that's fine.
			pass
		except Exception:
			frappe.throw(_("Invalid Message Format"))

		variables = re.findall(r"\{(.*?)\}", self.template_message)
		self.template_variables = ",".join(v.strip() for v in variables if v.strip())
