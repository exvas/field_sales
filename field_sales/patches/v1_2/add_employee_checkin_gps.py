"""Add `custom_latitude` and `custom_longitude` Float fields to
`Employee Checkin` so the mobile app's Check-In/Out flow can persist
GPS at the moment of each check event.

Idempotent: `create_custom_field` no-ops when the field already exists.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field


def execute():
    create_custom_field(
        "Employee Checkin",
        {
            "fieldname": "custom_latitude",
            "label": "Latitude",
            "fieldtype": "Float",
            "precision": 6,
            "insert_after": "device_id",
            "module": "Field Sales",
        },
    )
    create_custom_field(
        "Employee Checkin",
        {
            "fieldname": "custom_longitude",
            "label": "Longitude",
            "fieldtype": "Float",
            "precision": 6,
            "insert_after": "custom_latitude",
            "module": "Field Sales",
        },
    )
    frappe.clear_cache(doctype="Employee Checkin")
    print("field_sales: Employee Checkin custom_latitude/custom_longitude ensured")
