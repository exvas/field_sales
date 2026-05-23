# Copyright (c) 2026, vijila@teambackoffice.com and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CustomerFeedback(Document):
    def validate(self):
        # Honeypot - bots fill all fields; if this is set, drop the doc.
        if (self.honeypot or "").strip():
            frappe.throw("Submission rejected.")
        if not self.submitted_at:
            from frappe.utils import now_datetime
            self.submitted_at = now_datetime()
