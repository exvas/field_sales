
import frappe


@frappe.whitelist()
def get_location_data(employee=None, date=None):
    if not employee:
        frappe.throw(_("Employee is required"))
    if not date:
        frappe.throw(_("Date is required"))

    try:
        # Step 1: Fetch logs for the employee on the given date
        logs = frappe.get_all(
            "Employee Location Log",
            filters={
                "employee": employee,
                "date": date  # assumes you have a 'date' field in your Log doctype
            },
            fields=["name"]
        )

        log_names = [log.name for log in logs]

        if not log_names:
            return []

        # Step 2: Fetch child location entries
        entries = frappe.get_all(
            "Employee Location Entry",
            filters={"parent": ["in", log_names]},
            fields=["parent", "latitude", "longitude", "creation"],
            order_by="creation asc"
        )

        # Optional: Format time
        for entry in entries:
            entry["time"] = frappe.utils.format_time(entry["creation"])

        return entries

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_employee_location_entries error")
        frappe.throw(_("Failed to fetch employee location entries."))
