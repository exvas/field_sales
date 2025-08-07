# Copyright (c) 2025, vijila@teambackoffice.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
from frappe.utils import nowdate
import frappe

class EmployeeLocationLog(Document):
    def autoname(self):
        if self.employee:
            salesperson_part = self.employee  # Already the Sales Person ID like "SP-0001"
        else:
            salesperson_part = "SP-UNKNOWN"

        today = nowdate()
        self.name = f"{salesperson_part}-{today}"
