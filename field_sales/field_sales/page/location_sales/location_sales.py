
import frappe



# @frappe.whitelist()
# def get_location_data(employee=None, date=None):
#     if not employee:
#         frappe.throw(_("Employee is required"))
#     if not date:
#         frappe.throw(_("Date is required"))

#     try:
#         logs = frappe.get_all(
#             "Employee Location Log",
#             filters={
#                 "employee": employee,
#                 "date": date
#             },
#             fields=["name"]
#         )

#         log_names = [log.name for log in logs]

#         if not log_names:
#             return []

#         entries = frappe.get_all(
#             "Employee Location Entry",
#             filters={"parent": ["in", log_names]},
#             fields=["parent", "latitude", "longitude", "creation", "time"],
#             order_by="creation asc"
#         )

#         for entry in entries:
#             if entry.get("time"):
#                 entry["time"] = frappe.utils.format_time(entry["time"])

#         return entries

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "get_employee_location_entries error")
#         frappe.throw(_("Failed to fetch employee location entries."))

# @frappe.whitelist()
# def get_location_data(employee=None, date=None):
#     if not employee:
#         frappe.throw(_("Employee is required"))
#     if not date:
#         frappe.throw(_("Date is required"))

#     try:
#         # Get Employee Location Logs for the date
#         logs = frappe.get_all(
#             "Employee Location Log",
#             filters={
#                 "employee": employee,
#                 "date": date
#             },
#             fields=["name"]
#         )

#         log_names = [log.name for log in logs]

#         location_entries = []
#         if log_names:
#             # Get Employee Location Entries
#             location_entries = frappe.get_all(
#                 "Employee Location Entry",
#                 filters={"parent": ["in", log_names]},
#                 fields=["parent", "latitude", "longitude", "creation", "time"],
#                 order_by="creation asc"
#             )

#             for entry in location_entries:
#                 if entry.get("time"):
#                     entry["time"] = frappe.utils.format_time(entry["time"])

#         # Get Customer Visit Log for the employee and date
#         visit_logs = frappe.get_all(
#             "Customer Visit Log",
#             filters={
#                 "employee": employee,
#                 "date": date
#             },
#             fields=["name", "customer_name","latitude", "longitude","time"]
#         )

#         return {
#             "location_entries": location_entries,
#             "customer_visits": visit_logs
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "get_employee_location_entries error")
#         frappe.throw(_("Failed to fetch employee location and visit data."))

import frappe
from frappe import _

@frappe.whitelist()
def get_location_data(sales_person=None, date=None):
    if not sales_person:
        frappe.throw(_("Sales Person is required"))
    if not date:
        frappe.throw(_("Date is required"))

    try:
        # Get Employee Location Logs for the date (employee field actually stores Sales Person ID)
        logs = frappe.get_all(
            "Employee Location Log",
            filters={
                "employee": sales_person,  # field is named 'employee' but stores sales_person
                "date": date
            },
            fields=["name"]
        )

        log_names = [log.name for log in logs]

        location_entries = []
        if log_names:
            # Get Location Entries from those logs
            location_entries = frappe.get_all(
                "Employee Location Entry",
                filters={"parent": ["in", log_names]},
                fields=["parent", "latitude", "longitude", "creation", "time","entry_type"],
                order_by="creation asc"
            )

            for entry in location_entries:
                if entry.get("time"):
                    entry["time"] = frappe.utils.format_time(entry["time"])

        # Get Customer Visit Logs (same logic)
        visit_logs = frappe.get_all(
            "Customer Visit Log",
            filters={
                "employee": sales_person,  # field is named 'employee' but stores sales_person
                "date": date
            },
            fields=["name", "customer_name", "latitude", "longitude", "time"]
        )

        return {
            "location_entries": location_entries,
            "customer_visits": visit_logs
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_location_data error")
        frappe.throw(_("Failed to fetch location and visit data for Sales Person."))
