import json
import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def response(message, data, success, status_code):
    '''method to generates responses of an API
       args:
            message : response message string
            data : json object of the data
            success : True or False depending on the API response
            status_code : status of the request'''
    frappe.clear_messages()
    frappe.local.response["message"] = message
    frappe.local.response["data"] = data
    frappe.local.response["success"] = success
    frappe.local.response["http_status_code"] = status_code
    return

# @frappe.whitelist(allow_guest=True, methods=["GET", "POST"])
# def user_login(usr, pwd, device_id=None):
#     if not usr or not pwd:
#         frappe.local.response["message"] = {
#             "success_key": 0,
#             "message": "Both User and Password are required!",
#         }
#         frappe.local.response.http_status_code = 400
#         return

#     filter_field = "email" if "@" in usr else ("mobile_no" if usr.isdigit() else "username")

#     user = frappe.db.get_value("User", {filter_field: usr}, ["name", "username", "email", "mobile_no", "api_key"], as_dict=True)

#     if not user:
#         frappe.local.response["message"] = {
#             "success_key": 0,
#             "message": f"{filter_field.capitalize()} {usr} Does Not Exist!",
#         }
#         frappe.local.response.http_status_code = 404
#         frappe.log_error(
#             title="Login Failed", message=f"{filter_field.capitalize()} {usr} Does Not Exist!"
#         )
#         return

#     try:
#         login_manager = frappe.auth.LoginManager()
#         frappe.form_dict.device = "mobile"
#         login_manager.authenticate(user=user.name, pwd=pwd)
#         login_manager.post_login()

#         # Generate API key/secret
#         api_key, api_secret = generate_keys(user.name)

#         # Fetch user branch
#         branch = frappe.db.get_value(
#             "UserBranchSettings",
#             {"user": user.name},
#             "branch"
#         )

#         # ✅ Fetch user roles
#         roles = frappe.get_roles(user.name)

#         frappe.response["message"] = {
#             "success_key": 1,
#             "message": "Authentication success",
#             "sid": frappe.session.sid,
#             "api_key": api_key,
#             "api_secret": api_secret,
#             "username": user.username,
#             "email": user.email,
#             "mobile_no": user.mobile_no,
#             "branch": branch or "Not Assigned",
#             "roles": roles  # 👈 Add roles here
#         }

#     except frappe.exceptions.AuthenticationError:
#         frappe.clear_messages()
#         frappe.local.response["message"] = {
#             "success_key": 0,
#             "message": "Incorrect password!",
#         }
#         frappe.local.response.http_status_code = 401

@frappe.whitelist(allow_guest=True, methods=["GET", "POST"])
def user_login(usr, pwd, device_id=None):
    if not usr or not pwd:
        frappe.local.response["message"] = {
            "success_key": 0,
            "message": "Both User and Password are required!",
        }
        frappe.local.response.http_status_code = 400
        return

    filter_field = "email" if "@" in usr else ("mobile_no" if usr.isdigit() else "username")

    user = frappe.db.get_value(
        "User",
        {filter_field: usr},
        ["name", "username", "email", "mobile_no", "api_key"],
        as_dict=True
    )

    if not user:
        frappe.local.response["message"] = {
            "success_key": 0,
            "message": f"{filter_field.capitalize()} {usr} does not exist!",
        }
        frappe.local.response.http_status_code = 404
        frappe.log_error(
            title="Login Failed",
            message=f"{filter_field.capitalize()} {usr} does not exist!"
        )
        return

    try:
        login_manager = frappe.auth.LoginManager()
        frappe.form_dict.device = "mobile"
        login_manager.authenticate(user=user.name, pwd=pwd)
        login_manager.post_login()

        api_key, api_secret = generate_keys(user.name)

        branch = frappe.db.get_value(
            "UserBranchSettings",
            {"user": user.name},
            "branch"
        )

        roles = frappe.get_roles(user.name)

        employee_id = ""
        employee_name = ""
        sales_person_id = ""

        # ✅ Check if user has "Sales Person" role before proceeding
        if "Sales Person" not in roles:
            frappe.local.response["message"] = {
                "success_key": 0,
                "message": "Access denied! You do not have the Sales Person role assigned.",
            }
            frappe.local.response.http_status_code = 403
            return

        # ✅ Now fetch sales person ID if the role exists
        emp = frappe.db.get_value(
            "Employee",
            {"user_id": user.name},
            ["name", "employee_name"],
            as_dict=True
        )
        if emp:
            employee_id = emp.name
            employee_name = emp.employee_name
            sales_person_id = frappe.db.get_value(
                "Sales Person",
                {"employee": emp.name},
                "name"
            ) or ""

        frappe.response["message"] = {
            "success_key": 1,
            "message": "Authentication success",
            "sid": frappe.session.sid,
            "api_key": api_key,
            "api_secret": api_secret,
            "username": user.username,
            "email": user.email,
            "mobile_no": user.mobile_no,
            "branch": branch or "Not Assigned",
            "roles": roles,
            "employee_id": employee_id,
            "employee_name": employee_name,
            "sales_person_id": sales_person_id
        }

    except frappe.exceptions.AuthenticationError:
        frappe.clear_messages()
        frappe.local.response["message"] = {
            "success_key": 0,
            "message": "Incorrect password!",
        }
        frappe.local.response.http_status_code = 401

def set_device_to_mobile():
    # Ensure session exists before modifying
    if hasattr(frappe.local, 'session') and frappe.local.session.data:
        # Set the device in session data to 'mobile'
        frappe.local.session.data['device'] = 'mobile'
        # Commit the session change
        frappe.local.session.save()
    else:
        frappe.throw("Session not found.")

def generate_device_id(user, device_id):
    user_deveice_id = frappe.db.get_value("User Device",{'user':user},'device_id')
    if not user_deveice_id:
        user_details = frappe.new_doc("User Device")
        user_details.device_id = device_id
        user_details.user = user
        user_details.save(ignore_permissions=True)
        frappe.db.commit()
        user_deveice_id = user_details.device_id
    else:
        user_details = frappe.get_doc("User Device",{'user':user})
        user_details.device_id = device_id
        user_details.save(ignore_permissions=True)
        frappe.db.commit()
        user_deveice_id = user_details.device_id
    return user_deveice_id

from frappe.utils import nowdate
from frappe.utils.password import set_encrypted_password

def generate_keys(user):
    user_doc = frappe.get_doc("User", user)

    # Always generate new API secret
    new_api_secret = frappe.generate_hash(length=15)
    set_encrypted_password("User", user, new_api_secret, fieldname="api_secret")

    # Generate API key if not already set
    if not user_doc.api_key:
        user_doc.api_key = frappe.generate_hash(length=15)

    user_doc.save(ignore_permissions=True)
    frappe.db.commit()

    return user_doc.api_key, new_api_secret
 # Return both!

@frappe.whitelist(methods=["GET", "POST"], allow_guest=True)
def logout(usr):
    users_list = ["Administrator"]
    users = frappe.get_all("User")
    for user in users:
        users_list.append(user)

    if usr in users_list:
        try:
            logout_manager = frappe.auth.LoginManager()
            logout_manager.logout(usr)
            frappe.local.response["message"] = {
                "success_key": 1,
                "message": "Logged out successfully!",
            }
            frappe.local.response.http_status_code = 200

        except Exception as e:
            frappe.local.response["message"] = {
                "success_key": 0,
                "message": "Error logging out!",
                "Exception": e,
            }
            frappe.local.response.http_status_code = 400

    else:
        frappe.local.response["message"] = {
            "success_key": 0,
            "message": "User not found!",
        }
        frappe.local.response.http_status_code = 404



@frappe.whitelist(allow_guest=True)
def get_items(price_list="Standard Selling"):
    items = frappe.get_all(
        "Item",
        filters={"disabled": 0},
        fields=["name", "item_name", "description", "stock_uom", "is_stock_item"]
    )

    result = []

    for item in items:
        # Get price from Item Price
        price = frappe.db.get_value(
            "Item Price",
            filters={"item_code": item.name, "price_list": price_list},
            fieldname="price_list_rate"
        )

        result.append({
            "item_code": item.name,
            "item_name": item.item_name,
            "description": item.description,
            "uom": item.stock_uom,
            "price": price or 0.0,
            "maintain_stock": item.is_stock_item  # True or False
        })

    return result

@frappe.whitelist()
def get_customers():
    customers = frappe.get_all(
        "Customer",
        fields=[
            "name",
            "customer_name",
            "customer_type",
            "customer_group",
            "territory",
            "mobile_no",
            "email_id",
            "gstin"  # Include GSTIN field
        ]
    )

    # Add a flag for each customer indicating if GSTIN is present
    for customer in customers:
        if customer.get("gstin"):
            customer["has_gstin"] = True
        else:
            customer["has_gstin"] = False

    return {"message": customers}

@frappe.whitelist()
def create_sales_order():
    data=frappe.request.get_json()
    customer_name=data.get("customer")
    sales_person=data.get("sales_person")
    
    if not frappe.db.exists("Customer", customer_name):
        return {
            "status": "error",
            "message": f"Customer '{customer_name}' does not exist."
        }

    # ✅ Create Sales Order
    so = frappe.get_doc({
        "doctype": "Sales Order",
        "customer": customer_name,
        "custom_sales_person":sales_person,
        "delivery_date": data.get("delivery_date"),
        "items": data.get("items")
    })
    so.insert(ignore_permissions=True)
    so.submit()

    return {
        "status": "success",
        "sales_order": so.name
    }

@frappe.whitelist()
def get_sales_orders_with_details(sales_person_id=None):
    if not sales_person_id:
        return {
            "status": "error",
            "message": "Sales Person ID is required"
        }

    # ✅ Filter directly with the custom_sales_person field in Sales Order
    sales_order_names = frappe.get_all(
        "Sales Order",
        filters={
            "custom_sales_person": sales_person_id,
            "docstatus": 1  # Only submitted orders
        },
        pluck="name"
    )

    sales_orders = []
    for so_name in sales_order_names:
        doc = frappe.get_doc("Sales Order", so_name)
        sales_orders.append({
            "name": doc.name,
            "customer": doc.customer,
            "delivery_date": doc.delivery_date,
            "Total": doc.total,
            "items": [
                {
                    "item_code": item.item_code,
                    "qty": item.qty,
                    "rate": item.rate,
                    "amount": item.amount
                } for item in doc.items
            ]
        })

    return {
        "status": "success",
        "sales_orders": sales_orders
    }

import frappe
from frappe import _

@frappe.whitelist()
def get_employee_location_entries(employee=None):
    if not employee:
        frappe.throw(_("Employee is required"))

    try:
        results = []
        
        # Get all parent Employee Location Log records for this employee
        logs = frappe.get_all(
            "Employee Location Log",
            filters={"employee": employee},
            fields=["name"]
        )

        if not logs:
            return []

        log_names = [log.name for log in logs]

        # Get child entries from Employee Location Entry where parent is in log_names
        entries = frappe.get_all(
            "Employee Location Entry",
            filters={"parent": ["in", log_names]},
            fields=["parent", "latitude", "longitude", "creation"]
        )

        return entries

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_employee_location_entries error")
        frappe.throw(_("Failed to fetch employee location entries."))
# frappe_app/api/sales_invoice.py
# import frappe
# from frappe import _

# @frappe.whitelist(allow_guest=False)
# def get_sales_invoice_lists():
#     invoices = frappe.get_all("Sales Invoice", filters={"docstatus": 1}, fields=[
#         "name", "customer", "posting_date", "due_date", "grand_total", "outstanding_amount", "status"
#     ], order_by="posting_date desc")

#     result = []

#     for inv in invoices:
#         items = frappe.get_all("Sales Invoice Item", filters={"parent": inv.name}, fields=[
#             "item_code", "item_name", "qty", "rate", "amount", "description"
#         ])

#         result.append({
#             "invoice_id": inv.name,
#             "customer": inv.customer,
#             "posting_date": inv.posting_date,
#             "due_date": inv.due_date,
#             "grand_total": inv.grand_total,
#             "outstanding_amount": inv.outstanding_amount,
#             "status": inv.status,
#             "items": items
#         })

#     return {"invoices": result}

import frappe

@frappe.whitelist(allow_guest=False)
def get_sales_invoice_list():
    # Get sales_person from URL params
    sales_person = frappe.request.args.get("sales_person")
    if not sales_person:
        return {
            "status": "error",
            "message": "Missing sales_person parameter"
        }

    # Fetch only invoices matching this sales person
    invoices = frappe.get_all(
        "Sales Invoice",
        filters={
            "docstatus": 1,
            "custom_sales_person": sales_person  # ✅ Filter by custom field
        },
        fields=[
            "name", "customer", "posting_date", "due_date",
            "grand_total", "outstanding_amount", "status"
        ],
        order_by="posting_date desc"
    )

    result = []

    for inv in invoices:
        # Fetch Sales Invoice Items
        items = frappe.get_all(
            "Sales Invoice Item",
            filters={"parent": inv.name},
            fields=[
                "item_code", "item_name", "qty", "rate", "amount", "description"
            ]
        )

        # Fetch Payment Entry References linked to this Sales Invoice
        payment_refs = frappe.get_all(
            "Payment Entry Reference",
            filters={
                "reference_doctype": "Sales Invoice",
                "reference_name": inv.name
            },
            fields=["parent", "allocated_amount"]
        )

        # Fetch full Payment Entry details
        payments = []
        for ref in payment_refs:
            try:
                payment = frappe.get_doc("Payment Entry", ref.parent)
                payments.append({
                    "payment_entry": payment.name,
                    "posting_date": payment.posting_date,
                    "mode_of_payment": payment.mode_of_payment,
                    "paid_amount": payment.paid_amount,
                    "allocated_amount": ref.allocated_amount,
                    "status": payment.status
                })
            except frappe.DoesNotExistError:
                continue  # If payment entry is deleted or missing

        result.append({
            "invoice_id": inv.name,
            "customer": inv.customer,
            "posting_date": inv.posting_date,
            "due_date": inv.due_date,
            "grand_total": inv.grand_total,
            "outstanding_amount": inv.outstanding_amount,
            "status": inv.status,
            "items": items,
            "payments": payments
        })

    return {
        "status": "success",
        "sales_person": sales_person,
        "invoice_count": len(result),
        "invoices": result
    }

# import frappe
# from frappe.utils import nowdate
# from frappe import _

# # In your custom app .py file
# @frappe.whitelist(allow_guest=True)
# def create_payment_entry():
#     data = frappe.request.get_json()
    
#     sales_invoice_id = data.get("sales_invoice_id")
#     amount = data.get("amount")
#     mode_of_payment = data.get("mode_of_payment")  # Should be "Cash" or "Card"

#     if not sales_invoice_id or not amount or not mode_of_payment:
#         return {
#             "status": "error",
#             "message": "sales_invoice_id, amount, and mode_of_payment are required."
#         }

#     # Get the related Sales Invoice
#     sales_invoice = frappe.get_doc("Sales Invoice", sales_invoice_id)
    
#     # Create Payment Entry
#     pe = frappe.get_doc({
#         "doctype": "Payment Entry",
#         "payment_type": "Receive",
#         "party_type": "Customer",
#         "party": sales_invoice.customer,
#         "posting_date": frappe.utils.nowdate(),
#         "paid_amount": amount,
#         "received_amount": amount,
#         "mode_of_payment": mode_of_payment,
#         "reference_no": frappe.generate_hash(length=10),  # Random reference
#         "reference_date": frappe.utils.nowdate(),
#         "references": [
#             {
#                 "reference_doctype": "Sales Invoice",
#                 "reference_name": sales_invoice.name,
#                 "allocated_amount": amount
#             }
#         ]
#     })

#     pe.insert(ignore_permissions=True)
#     pe.submit()

#     return {
#         "status": "success",
#         "payment_entry": pe.name
#     }

@frappe.whitelist(methods=["POST"])
def pay_sales_invoice():
    data = frappe.request.get_json()

    invoice_name = data.get("invoice_name")
    payment_amount = float(data.get("payment_amount", 0))
    mode_of_payment = data.get("mode_of_payment", "Cash")
    reference_no = data.get("reference_no", "")
    reference_date = data.get("reference_date", frappe.utils.nowdate())
    posting_date = data.get("posting_date", frappe.utils.nowdate())

    if not invoice_name or payment_amount <= 0:
        return {
            "status": "error",
            "message": "Invoice name and valid payment amount are required",
            "code": 400
        }

    invoice = frappe.get_doc("Sales Invoice", invoice_name)

    if invoice.docstatus != 1:
        return {
            "status": "error",
            "message": "Invoice is not submitted",
            "code": 400
        }

    if invoice.outstanding_amount <= 0:
        return {
            "status": "error",
            "message": "Invoice already paid",
            "code": 400
        }

    # Get Paid To Account based on mode of payment and company
    paid_to = frappe.db.get_value("Mode of Payment Account", {
        "parent": mode_of_payment,
        "company": invoice.company
    }, "default_account")

    if not paid_to:
        return {
            "status": "error",
            "message": f"Account not found for Mode of Payment '{mode_of_payment}' in company '{invoice.company}'",
            "code": 400
        }

    payment_entry = frappe.get_doc({
        "doctype": "Payment Entry",
        "payment_type": "Receive",
        "party_type": "Customer",
        "party": invoice.customer,
        "company": invoice.company,
        "posting_date": posting_date,
        "mode_of_payment": mode_of_payment,
        "paid_to": paid_to,
        "paid_amount": payment_amount,
        "received_amount": payment_amount,
        "reference_no": reference_no,
        "reference_date": reference_date,
        "references": [
            {
                "reference_doctype": "Sales Invoice",
                "reference_name": invoice.name,
                "total_amount": invoice.grand_total,
                "outstanding_amount": invoice.outstanding_amount,
                "allocated_amount": payment_amount
            }
        ]
    })

    payment_entry.insert(ignore_permissions=True)
    # payment_entry.submit()

    return {
        "status": "success",
        "payment_entry": payment_entry.name
    }

# @frappe.whitelist(allow_guest=True)
# def get_customer_sales_invoices(customer):
#     try:
#         invoices = frappe.get_all(
#             "Sales Invoice",
#             filters={"customer": customer, "docstatus": 1},
#             fields=["name", "posting_date", "due_date", "grand_total", "outstanding_amount"],
#             order_by="posting_date desc"
#         )

#         invoice_data = []

#         for inv in invoices:
#             items = frappe.get_all(
#                 "Sales Invoice Item",
#                 filters={"parent": inv.name},
#                 fields=["item_code", "item_name", "qty", "rate", "amount"]
#             )

#             invoice_data.append({
#                 "invoice_name": inv.name,
#                 "posting_date": inv.posting_date,
#                 "due_date": inv.due_date,
#                 "grand_total": inv.grand_total,
#                 "outstanding_amount": inv.outstanding_amount,
#                 "items": items
#             })

#         return {
#             "status": "success",
#             "customer": customer,
#             "invoice_count": len(invoice_data),
#             "invoices": invoice_data
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "get_customer_sales_invoices")
#         return {
#             "status": "error",
#             "message": str(e)
#         }

@frappe.whitelist()
def get_customer_sales_invoices_by_salesperson(sales_person=None, customer=None):
    if not sales_person:
        frappe.throw("Sales Person ID is required")

    # Build filters
    filters = {
        "docstatus": 1,  # Submitted invoices only
        "custom_sales_person": sales_person
    }

    if customer:
        filters["customer"] = customer

    try:
        # Fetch invoices based on filters
        invoices = frappe.get_all(
            "Sales Invoice",
            filters=filters,
            fields=[
                "name",
                "customer",
                "posting_date",
                "due_date",
                "grand_total",
                "outstanding_amount",
                "status"
            ],
            order_by="posting_date desc"
        )

        invoice_data = []
        total_outstanding = 0

        for inv in invoices:
            # Get items for each invoice
            items = frappe.get_all(
                "Sales Invoice Item",
                filters={"parent": inv.name},
                fields=["item_code", "item_name", "qty", "rate", "amount"]
            )

            total_outstanding += inv.outstanding_amount or 0

            invoice_data.append({
                "invoice_name": inv.name,
                "customer": inv.customer,
                "posting_date": inv.posting_date,
                "due_date": inv.due_date,
                "grand_total": inv.grand_total,
                "outstanding_amount": inv.outstanding_amount,
                "status": inv.status,
                "items": items
            })

        return {
            "status": "success",
            "sales_person": sales_person,
            "customer": customer,
            "invoice_count": len(invoice_data),
            "total_outstanding_amount": total_outstanding,
            "invoices": invoice_data
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_customer_sales_invoices_by_salesperson")
        return {
            "status": "error",
            "message": str(e)
        }


# @frappe.whitelist(allow_guest=True)
# def get_customer_sales_invoices(customer):
#     try:
#         invoices = frappe.get_all(
#             "Sales Invoice",
#             filters={"customer": customer, "docstatus": 1},
#             fields=["name", "posting_date", "due_date", "grand_total", "outstanding_amount"],
#             order_by="posting_date desc"
#         )

#         invoice_data = []
#         total_outstanding = 0

#         for inv in invoices:
#             # Fetch items in the invoice
#             items = frappe.get_all(
#                 "Sales Invoice Item",
#                 filters={"parent": inv.name},
#                 fields=["item_code", "item_name", "qty", "rate", "amount"]
#             )

#             # Fetch Payment Entries linked to this Sales Invoice
#             payment_refs = frappe.get_all(
#                 "Payment Entry Reference",
#                 filters={
#                     "reference_doctype": "Sales Invoice",
#                     "reference_name": inv.name
#                 },
#                 fields=["parent", "allocated_amount"]
#             )

#             # Now get the details of those payment entries
#             payments = []
#             for ref in payment_refs:
#                 payment = frappe.get_doc("Payment Entry", ref.parent)

#                 payments.append({
#                     "payment_entry": payment.name,
#                     "posting_date": payment.posting_date,
#                     "mode_of_payment": payment.mode_of_payment,
#                     "paid_amount": payment.paid_amount,
#                     "allocated_amount": ref.allocated_amount,
#                     "status": payment.status
#                 })

#             total_outstanding += inv.outstanding_amount or 0

#             invoice_data.append({
#                 "invoice_name": inv.name,
#                 "posting_date": inv.posting_date,
#                 "due_date": inv.due_date,
#                 "grand_total": inv.grand_total,
#                 "outstanding_amount": inv.outstanding_amount,
#                 "items": items,
#                 "payments": payments  # <- included here
#             })

#         return {
#             "status": "success",
#             "customer": customer,
#             "invoice_count": len(invoice_data),
#             "total_outstanding_amount": total_outstanding,
#             "invoices": invoice_data
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "get_customer_sales_invoices")
#         return {
#             "status": "error",
#             "message": str(e)
#         }

@frappe.whitelist()
def get_location_data(employee=None, date=None):
    if not employee:
        frappe.throw(_("Employee is required"))
    if not date:
        frappe.throw(_("Date is required"))

    try:
        # Get Employee Location Logs for the date
        logs = frappe.get_all(
            "Employee Location Log",
            filters={
                "employee": employee,
                "date": date
            },
            fields=["name"]
        )

        log_names = [log.name for log in logs]

        location_entries = []
        if log_names:
            # Get Employee Location Entries
            location_entries = frappe.get_all(
                "Employee Location Entry",
                filters={"parent": ["in", log_names]},
                fields=["parent", "latitude", "longitude", "creation", "time"],
                order_by="creation asc"
            )

            for entry in location_entries:
                if entry.get("time"):
                    entry["time"] = frappe.utils.format_time(entry["time"])

        # Get Customer Visit Log for the employee and date
        visit_logs = frappe.get_all(
            "Customer Visit Log",
            filters={
                "employee": employee,
                "date": date
            },
            fields=["name", "customer_name","latitude", "longitude","time"]
        )

        return {
            "location_entries": location_entries,
            "customer_visits": visit_logs
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_employee_location_entries error")
        frappe.throw(_("Failed to fetch employee location and visit data."))

@frappe.whitelist()
def get_mode_of_payment():
    try:
        mode=frappe.get_all(
            "Mode of Payment",
            fields=["name","execute"]
                          )
        for m in mode:
            m["execute"]=bool(m.get("execute"))

        return mode



    except Exception as e:
        frappe.throw("failed to fetch"+str(e))

import frappe
from frappe import _
from frappe.utils import now
from frappe.model.document import Document

@frappe.whitelist(allow_guest=False)
def create_payment_entry_from_sales_invoices():
    import json
    data = frappe.local.form_dict

    if frappe.request and frappe.request.data:
        data = json.loads(frappe.request.data)

    customer = data.get("customer")
    # sales_person=data.get("sales_person")
    total_allocated_amount = data.get("total_allocated_amount")
    mode_of_payment = data.get("mode_of_payment")
    invoice_allocations = data.get("invoice_allocations", [])

    if not customer or not total_allocated_amount or not mode_of_payment or not invoice_allocations:
        frappe.throw(_("Missing required fields"))

    # Create Payment Entry
    pe = frappe.new_doc("Payment Entry")
    pe.payment_type = "Receive"
    pe.party_type = "Customer"
    pe.party = customer
    pe.posting_date = now()
    pe.custom_sales_person=data.get("sales_person")
    pe.mode_of_payment = mode_of_payment
    pe.paid_amount = total_allocated_amount
    pe.received_amount = total_allocated_amount
    pe.target_exchange_rate = 1
    pe.paid_to = frappe.get_value("Mode of Payment Account", {
        "parent": mode_of_payment
    }, "default_account")

    for alloc in invoice_allocations:
        pe.append("references", {
            "reference_doctype": "Sales Invoice",
            "reference_name": alloc["invoice"],
            "allocated_amount": alloc["amount"]
        })

    pe.insert()
    frappe.db.commit()

    return {
        "message": "Payment Entry created",
        "payment_entry": pe.name
    }

@frappe.whitelist(methods=["POST"])
def create_sales_return():
    data = frappe.request.get_json()

    invoice_name = data.get("invoice_name")
    sales_person=data.get("sales_person")
    product_name = data.get("product_name")
    qty = data.get("qty")
    reason = data.get("reason")
    buying_date = data.get("buying_date")
    notes = data.get("notes")

    # ✅ FIXED validation
    if not (invoice_name and product_name and qty and reason and buying_date):
        return {
            "status": "error",
            "message": "Please fill all required fields.",
            "code": 400
        }

    try:
        doc = frappe.new_doc("Sales Return")
        doc.sales_invoice_id = invoice_name
        doc.product_name = product_name
        doc.qty = qty
        doc.reason = reason
        doc.date = buying_date
        doc.notes = notes
        doc.sales_person_id=sales_person
        doc.status = "Open"
        doc.insert()
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Sales Return created",
            "sales_return_id": doc.name
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Sales Return API Error")
        return {
            "status": "error",
            "message": f"An error occurred: {str(e)}",
            "code": 500
        }

@frappe.whitelist(allow_guest=True)
def get_sales_returns(sales_person=None):
    try:
        # Make sales_person_id mandatory
        if not sales_person:
            return {
                "status": "error",
                "message": "Sales Person ID is required",
                "code": 400
            }

        filters = {
            "sales_person_id": sales_person
        }

        sales_returns = frappe.get_all(
            "Sales Return",
            filters=filters,
            fields=[
                "name", 
                "sales_invoice_id", 
                "product_name", 
                "qty", 
                "reason", 
                "date", 
                "notes", 
                "status", 
                "sales_person_id"
            ],
            order_by="creation desc"
        )

        return {
            "status": "success",
            "data": sales_returns
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Sales Return API Error")
        return {
            "status": "error",
            "message": f"An error occurred: {str(e)}",
            "code": 500
        }

@frappe.whitelist()
def payment_entry_status():
    # Get parameters from URL query string
    customer_name = frappe.request.args.get("customer_name")
    sales_person = frappe.request.args.get("sales_person")

    # Validate required parameters
    if not customer_name:
        return {"status": "error", "message": "Missing customer_name"}
    if not sales_person:
        return {"status": "error", "message": "Missing sales_person"}

    # Fetch Draft Payment Entries for given customer & sales person
    payment_entries = frappe.get_all(
        "Payment Entry",
        filters={
            "party_type": "Customer",
            "party": customer_name,
            "custom_sales_person": sales_person,  # ✅ Filter by custom_sales_person
            "docstatus": 0  # Draft only
        },
        fields=["name", "posting_date", "paid_amount", "reference_no"]
    )

    result = []
    total_allocated = 0

    for pe in payment_entries:
        # Fetch related invoice references
        references = frappe.get_all(
            "Payment Entry Reference",
            filters={"parent": pe.name},
            fields=["reference_name", "allocated_amount", "reference_doctype"]
        )

        ref_list = []
        for ref in references:
            total_allocated += ref.allocated_amount or 0
            ref_list.append({
                "reference_doctype": ref.reference_doctype,
                "reference_name": ref.reference_name,
                "allocated_amount": ref.allocated_amount
            })

        result.append({
            "payment_entry": pe.name,
            "posting_date": pe.posting_date,
            "paid_amount": pe.paid_amount,
            "reference_no": pe.reference_no,
            "status": "Draft",
            "references": ref_list
        })

    return {
        "status": "success",
        "data": result,
        "total_allocated_amount": total_allocated
    }


# for return request
@frappe.whitelist(allow_guest=False)
def save_fcm_token(fcm_token):
    employee = frappe.session.user
    if not employee:
        frappe.throw("Not logged in")

    doc = frappe.get_doc({
        "doctype": "FCM Token",
        "user": employee,
        "token": fcm_token
    })
    doc.insert(ignore_permissions=True)
    return {"status": "success", "message": "Token saved"}


@frappe.whitelist(methods=["POST"])
def location_entry():
    data = frappe.request.get_json()

    employee_id = data.get("employee_id")
    employee_name = data.get("employee_name")
    date = data.get("date")
    time = data.get("time")
    longitude = data.get("longitude")
    latitude = data.get("latitude")

    if not (employee_id and employee_name and date and time and longitude and latitude):
        return {
            "status": "error",
            "message": "Please fill all required fields.",
            "code": 400
        }

    try:
        # Step 1: Check if parent log already exists
        log_name = frappe.db.get_value("Employee Location Log", {
            "employee_id": employee_id,
            "date": date
        }, "name")

        if log_name:
            # Step 2: Add entry to existing log
            doc = frappe.get_doc("Employee Location Log", log_name)
        else:
            # Step 3: Create new log
            doc = frappe.new_doc("Employee Location Log")
            doc.employee_id = employee_id
            doc.employee_name = employee_name
            doc.date = date
            doc.insert()

        # Step 4: Append location to child table
        doc.append("employee_location_entry", {
            "time": time,
            "longitude": longitude,
            "latitude": latitude
        })

        doc.save()
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Location entry saved.",
            "log_id": doc.name
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Location Entry API Error")
        return {
            "status": "error",
            "message": f"An error occurred: {str(e)}",
            "code": 500
        }
    


@frappe.whitelist(methods=["POST"])
def create_location_log():
    data = frappe.request.get_json()
    employee_id = data.get("employee_id")
    print("employeee_id",employee_id)
    employee_name = data.get("employee_name")
    date = data.get("date")

    if not (employee_id and employee_name and date):
        return {
            "status": "error",
            "message": "All fields required.",
            "code": 400
        }

    if frappe.db.exists("Employee Location Log", {"employee_id": employee_id, "date": date}):
        return {
            "status": "error",
            "message": "Log already exists for this employee and date.",
            "code": 409
        }

    doc = frappe.new_doc("Employee Location Log")
    doc.employee = employee_id
    doc.employee_name = employee_name
    doc.date = date
    doc.insert()
    frappe.db.commit()

    return {
        "status": "success",
        "log_id": doc.name,
        "empl_id":doc.employee_id ,
        "empl_name": doc.employee_name
    }
@frappe.whitelist(methods=["POST"])
def append_location_entry():
    data = frappe.request.get_json()
    employee_id = data.get("employee_id")
    date = data.get("date")
    entries = data.get("entries")

    if not (employee_id and date and isinstance(entries, list) and entries):
        return {
            "status": "error",
            "message": "Required fields missing or invalid entries.",
            "code": 400
        }

    log_name = frappe.db.get_value("Employee Location Log", {
        "employee": employee_id,
        "date": date
    })

    if not log_name:
        return {
            "status": "error",
            "message": "Parent log does not exist. Check-in required first.",
            "code": 404
        }

    doc = frappe.get_doc("Employee Location Log", log_name)

    for entry in entries:
        if "time" in entry and "latitude" in entry and "longitude" in entry:
            doc.append("locations", {
                "time": entry["time"],
                "latitude": entry["latitude"],
                "longitude": entry["longitude"]
            })

    doc.save()
    frappe.db.commit()

    return {
        "status": "success",
        "message": f"{len(entries)} entries saved.",
        "log_id": log_name
    }

@frappe.whitelist(methods=["POST"])
def save_salesperson_location_log():
    data = frappe.request.get_json()
    salesperson_id = data.get("sales_person_id")  # Now expect this field directly
    date = data.get("date")
    entries = data.get("entries", [])

    if not (salesperson_id and date):
        return {
            "status": "error",
            "message": "Sales Person ID and Date are required.",
            "code": 400
        }

    # 🔍 Check for existing log by sales_person_id and date
    log_name = frappe.db.get_value("Employee Location Log", {
        "employee": salesperson_id,
        "date": date
    })

    if log_name:
        doc = frappe.get_doc("Employee Location Log", log_name)
        new_log_created = False
    else:
        doc = frappe.new_doc("Employee Location Log")
        doc.employee = salesperson_id
        doc.date = date
        new_log_created = True

    # ➕ Append valid entries
   # ➕ Append valid entries
    added = 0
    for entry in entries:
        if "time" in entry and "latitude" in entry and "longitude" in entry:
            doc.append("locations", {
                "time": entry["time"],
                "latitude": entry["latitude"],
                "longitude": entry["longitude"],
                "entry_type": entry.get("entry_type", "Track")  # Default to 'Track' if not provided
            })
            added += 1


    doc.save(ignore_permissions=True)
    frappe.db.commit()

    return {
        "status": "success",
        "message": f"{'Log created. ' if new_log_created else ''}{added} location entries saved.",
        "log_id": doc.name,
        "sales_person_id": salesperson_id
    }



@frappe.whitelist(allow_guest=False)
def log_customer_visit():
    import json
    data = json.loads(frappe.request.data)

    required_fields = ["sales_person", "date", "time", "longitude", "latitude", "customer_name"]
    for field in required_fields:
        if not data.get(field):
            frappe.throw(_("Missing required field: {0}").format(field))

    doc = frappe.new_doc("Customer Visit Log")
    doc.employee = data["sales_person"]
    doc.date = data["date"]
    doc.time = data["time"]
    doc.longitude = data["longitude"]
    doc.latitude = data["latitude"]
    doc.customer_name = data["customer_name"]
    doc.description = data.get("description", "")
    doc.insert()

    return {
        "success": True,
        "message": "Customer Visit Log created successfully",
        "name": doc.name
    }

@frappe.whitelist(allow_guest=False)
def get_all_sales_invoice_ids():
    try:
        invoices = frappe.get_all(
            "Sales Invoice",
            filters={"docstatus": 1},  # Only submitted invoices
            pluck="name"  # Returns only the "name" field (invoice ID)
        )

        return {
            "status": "success",
            "code": 200,
            "message": "Successfully fetched all sales invoice IDs",
            "data": invoices
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "API Error: get_all_sales_invoice_ids")
        return {
            "status": "error",
            "code": 500,
            "message": f"An unexpected error occurred: {str(e)}",
            "data": None
        }

@frappe.whitelist()
def sales_invoice_detail_by_ids():
    try:
        invoice_id = frappe.form_dict.get("invoice_id")

        # Check if invoice_id is provided
        if not invoice_id:
            return {
                "status": "error",
                "code": 400,
                "message": "invoice_id is required",
                "data": None
            }

        # Try to get the Sales Invoice
        try:
            invoice = frappe.get_doc("Sales Invoice", invoice_id)
        except frappe.DoesNotExistError:
            return {
                "status": "error",
                "code": 404,
                "message": f"Sales Invoice '{invoice_id}' does not exist",
                "data": None
            }

        # Prepare data
        data = {
            "posting_date": invoice.posting_date,
            "customer": invoice.customer,
            "items": [
                {
                    "item_code": item.item_code,
                    "item_name": item.item_name,
                    "qty": item.qty,
                    "rate": item.rate,
                    "amount": item.amount
                }
                for item in invoice.items
            ]
        }

        # Success response
        return {
            "status": "success",
            "code": 200,
            "message": "Sales Invoice fetched successfully",
            "data": data
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "API Error: sales_invoice_detail_by_ids")
        return {
            "status": "error",
            "code": 500,
            "message": f"An unexpected error occurred: {str(e)}",
            "data": None
        }
@frappe.whitelist()
def get_location_update_interval():
    try:
        data=frappe.get_doc("Location Update Settings","Location Update Settings")
        return{
            "status":"success",
            "code":200,
            "message":f"successfully fetch location update interval",
            "data":data
        }
    except Exception as e:
        return{
            "status":"error",
            "code":500,
            "message":f"an error occured,{str(e)}"

        }