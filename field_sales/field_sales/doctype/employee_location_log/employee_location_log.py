# Copyright (c) 2025, vijila@teambackoffice.com and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document
from frappe.utils import nowdate
import frappe

class EmployeeLocationLog(Document):
    def autoname(self):
        # Get employee name from linked Employee record
        if self.employee:
            employee_name = frappe.db.get_value("Employee", self.employee, "employee_name")
            employee_part = employee_name.replace(" ", "").upper() if employee_name else "EMP"
        else:
            employee_part = "EMP"

        today = nowdate()  # e.g., "2025-08-04"
        self.name = f"{employee_part}-{today}"
