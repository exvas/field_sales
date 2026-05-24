"""Add the `custom_cheque_bounce_count` Int field to Customer so the
Cheque Bounce DocType can roll up repeat-bouncer history per customer.

Idempotent: safe to re-run; create_custom_field is a no-op when the
field already exists with matching properties.
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field


def execute():
    create_custom_field(
        "Customer",
        {
            "fieldname": "custom_cheque_bounce_count",
            "label": "Cheque Bounce Count",
            "fieldtype": "Int",
            "default": 0,
            "insert_after": "represents_company",
            "read_only": 1,
            "in_list_view": 0,
            "in_standard_filter": 1,
            "description": "Number of times this customer's cheques have bounced. Incremented automatically by the Cheque Bounce DocType.",
            "module": "Field Sales",
        },
    )
    frappe.clear_cache(doctype="Customer")
    print("field_sales: Customer.custom_cheque_bounce_count ensured")
