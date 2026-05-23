"""Permanently remove the two Item custom Link fields (`custom_finish` and
`custom_size`) that were auto-rendering as filters in ERPNext's built-in
"Select Item" / "Get Items From" dialog on Sales Invoice, Sales Order,
Quotation, Purchase Order, Purchase Receipt and Purchase Invoice forms.

This patch:
  1. Deletes both Custom Field rows by their canonical names.
  2. Clears the cached meta for Item so the next form load no longer
     advertises them.
  3. Logs whether each field was actually present (idempotent — safe to
     re-run on installs where the fields are already gone).

Data loss note: any values previously stored on Item rows in the
custom_finish / custom_size columns are NOT migrated elsewhere. The
column itself stays in `tabItem` until the schema sync drops it, but
once the Custom Field is gone the values are no longer surfaced or
editable from the desk. If you need the values, export them BEFORE
running this patch.
"""

import frappe


FIELDS_TO_REMOVE = [
    "Item-custom_finish",
    "Item-custom_size",
]


def execute():
    removed = []
    skipped = []

    for cf_name in FIELDS_TO_REMOVE:
        if frappe.db.exists("Custom Field", cf_name):
            try:
                frappe.delete_doc(
                    "Custom Field",
                    cf_name,
                    ignore_permissions=True,
                    force=True,
                )
                removed.append(cf_name)
            except Exception:
                frappe.log_error(
                    frappe.get_traceback(),
                    "field_sales.patches.remove_item_custom_size_and_finish",
                )
                skipped.append(cf_name)
        else:
            skipped.append(cf_name)

    if removed:
        frappe.clear_cache(doctype="Item")

    print(
        "field_sales: removed Custom Fields {} (skipped {})".format(
            removed, skipped
        )
    )
