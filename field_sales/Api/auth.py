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

    user = frappe.db.get_value("User", {filter_field: usr}, ["name", "username", "email", "mobile_no", "api_key"], as_dict=True)

    if not user:
        frappe.local.response["message"] = {
            "success_key": 0,
            "message": f"{filter_field.capitalize()} {usr} Does Not Exist!",
        }
        frappe.local.response.http_status_code = 404
        frappe.log_error(
            title="Login Failed", message=f"{filter_field.capitalize()} {usr} Does Not Exist!"
        )
        return

    try:
        login_manager = frappe.auth.LoginManager()
        frappe.form_dict.device = "mobile"
        login_manager.authenticate(user=user.name, pwd=pwd)
        login_manager.post_login()

        # Generate API key/secret
        api_key, api_secret = generate_keys(user.name)

        # Fetch user branch
        branch = frappe.db.get_value(
            "UserBranchSettings",
            {"user": user.name},
            "branch"
        )

        # ✅ Fetch user roles
        roles = frappe.get_roles(user.name)

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
            "roles": roles  # 👈 Add roles here
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
    if not frappe.db.exists("Customer", customer_name):
        return {
            "status": "error",
            "message": f"Customer '{customer_name}' does not exist."
        }

    # ✅ Create Sales Order
    so = frappe.get_doc({
        "doctype": "Sales Order",
        "customer": customer_name,
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
def get_sales_orders_with_details():
    sales_order_names = frappe.get_all("Sales Order", fields=["name"])
    
    sales_orders = []
    for so in sales_order_names:
        doc = frappe.get_doc("Sales Order", so.name)
        sales_orders.append({
            "name": doc.name,
            "customer": doc.customer,
            "delivery_date": doc.delivery_date,
            "Total":doc.total,
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
import frappe
from frappe import _

@frappe.whitelist(allow_guest=False)
def get_sales_invoice_list():
    invoices = frappe.get_all("Sales Invoice", filters={"docstatus": 1}, fields=[
        "name", "customer", "posting_date", "due_date", "grand_total", "outstanding_amount", "status"
    ], order_by="posting_date desc")

    result = []

    for inv in invoices:
        items = frappe.get_all("Sales Invoice Item", filters={"parent": inv.name}, fields=[
            "item_code", "item_name", "qty", "rate", "amount", "description"
        ])

        result.append({
            "invoice_id": inv.name,
            "customer": inv.customer,
            "posting_date": inv.posting_date,
            "due_date": inv.due_date,
            "grand_total": inv.grand_total,
            "outstanding_amount": inv.outstanding_amount,
            "status": inv.status,
            "items": items
        })

    return {"invoices": result}
