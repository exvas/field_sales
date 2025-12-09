# import json
# import frappe
# from frappe import _
# from frappe.utils import now, nowdate, flt
# from frappe.model.document import Document
# from frappe.utils.password import set_encrypted_password
# from bs4 import BeautifulSoup

# @frappe.whitelist(allow_guest=True)
# def response(message, data, success, status_code):
#     '''method to generates responses of an API'''
#     frappe.clear_messages()
#     frappe.local.response["message"] = message
#     frappe.local.response["data"] = data
#     frappe.local.response["success"] = success
#     frappe.local.response["http_status_code"] = status_code
#     return

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

#     user = frappe.db.get_value(
#         "User",
#         {filter_field: usr},
#         ["name", "username", "email", "mobile_no", "api_key"],
#         as_dict=True
#     )

#     if not user:
#         frappe.local.response["message"] = {
#             "success_key": 0,
#             "message": f"{filter_field.capitalize()} {usr} does not exist!",
#         }
#         frappe.local.response.http_status_code = 404
#         frappe.log_error(
#             title="Login Failed",
#             message=f"{filter_field.capitalize()} {usr} does not exist!"
#         )
#         return

#     try:
#         login_manager = frappe.auth.LoginManager()
#         frappe.form_dict.device = "mobile"
#         login_manager.authenticate(user=user.name, pwd=pwd)
#         login_manager.post_login()

#         api_key, api_secret = generate_keys(user.name)

#         branch = frappe.db.get_value(
#             "UserBranchSettings",
#             {"user": user.name},
#             "branch"
#         )

#         roles = frappe.get_roles(user.name)

#         employee_id = ""
#         employee_name = ""
#         sales_person_id = ""

#         # ✅ Check if user has "Sales Person" role before proceeding
#         if "Sales Person" not in roles:
#             frappe.local.response["message"] = {
#                 "success_key": 0,
#                 "message": "Access denied! You do not have the Sales Person role assigned.",
#             }
#             frappe.local.response.http_status_code = 403
#             return

#         # ✅ Now fetch sales person ID if the role exists
#         emp = frappe.db.get_value(
#             "Employee",
#             {"user_id": user.name},
#             ["name", "employee_name"],
#             as_dict=True
#         )
#         if emp:
#             employee_id = emp.name
#             employee_name = emp.employee_name
#             sales_person_id = frappe.db.get_value(
#                 "Sales Person",
#                 {"employee": emp.name},
#                 "name"
#             ) or ""

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
#             "roles": roles,
#             "employee_id": employee_id,
#             "employee_name": employee_name,
#             "sales_person_id": sales_person_id
#         }

#     except frappe.exceptions.AuthenticationError:
#         frappe.clear_messages()
#         frappe.local.response["message"] = {
#             "success_key": 0,
#             "message": "Incorrect password!",
#         }
#         frappe.local.response.http_status_code = 401

# def set_device_to_mobile():
#     if hasattr(frappe.local, 'session') and frappe.local.session.data:
#         frappe.local.session.data['device'] = 'mobile'
#         frappe.local.session.save()
#     else:
#         frappe.throw("Session not found.")

# def generate_device_id(user, device_id):
#     user_deveice_id = frappe.db.get_value("User Device",{'user':user},'device_id')
#     if not user_deveice_id:
#         user_details = frappe.new_doc("User Device")
#         user_details.device_id = device_id
#         user_details.user = user
#         user_details.save(ignore_permissions=True)
#         frappe.db.commit()
#         user_deveice_id = user_details.device_id
#     else:
#         user_details = frappe.get_doc("User Device",{'user':user})
#         user_details.device_id = device_id
#         user_details.save(ignore_permissions=True)
#         frappe.db.commit()
#         user_deveice_id = user_details.device_id
#     return user_deveice_id

# def generate_keys(user):
#     user_doc = frappe.get_doc("User", user)

#     # Always generate new API secret
#     new_api_secret = frappe.generate_hash(length=15)
#     set_encrypted_password("User", user, new_api_secret, fieldname="api_secret")

#     # Generate API key if not already set
#     if not user_doc.api_key:
#         user_doc.api_key = frappe.generate_hash(length=15)

#     user_doc.save(ignore_permissions=True)
#     frappe.db.commit()

#     return user_doc.api_key, new_api_secret

# @frappe.whitelist(methods=["GET", "POST"], allow_guest=True)
# def logout(usr):
#     users_list = ["Administrator"]
#     users = frappe.get_all("User")
#     for user in users:
#         users_list.append(user)

#     if usr in users_list:
#         try:
#             logout_manager = frappe.auth.LoginManager()
#             logout_manager.logout(usr)
#             frappe.local.response["message"] = {
#                 "success_key": 1,
#                 "message": "Logged out successfully!",
#             }
#             frappe.local.response.http_status_code = 200

#         except Exception as e:
#             frappe.local.response["message"] = {
#                 "success_key": 0,
#                 "message": "Error logging out!",
#                 "Exception": e,
#             }
#             frappe.local.response.http_status_code = 400

#     else:
#         frappe.local.response["message"] = {
#             "success_key": 0,
#             "message": "User not found!",
#         }
#         frappe.local.response.http_status_code = 404

# @frappe.whitelist(allow_guest=True)
# def get_items(price_list="Standard Selling"):
#     items = frappe.get_all(
#         "Item",
#         filters={"disabled": 0},
#         fields=["name", "item_name", "description", "stock_uom", "is_stock_item"]
#     )

#     result = []

#     for item in items:
#         # Get price from Item Price
#         price = frappe.db.get_value(
#             "Item Price",
#             filters={"item_code": item.name, "price_list": price_list},
#             fieldname="price_list_rate"
#         )
    
#         # Get tax template from Item Taxes table
#         tax_template = frappe.db.get_value(
#             "Item Tax",
#             filters={"parent": item.name},
#             fieldname="item_tax_template"
#         )

#         result.append({
#             "item_code": item.name,
#             "item_name": item.item_name,
#             "description": item.description,
#             "uom": item.stock_uom,
#             "price": price or 0.0,
#             "maintain_stock": item.is_stock_item,
#             "tax_template": tax_template or ""
#         })

#     return result

# @frappe.whitelist()
# def get_customers():
#     customers = frappe.get_all(
#         "Customer",
#         fields=[
#             "name",
#             "customer_name",
#             "customer_type",
#             "customer_group",
#             "territory",
#             "mobile_no",
#             "email_id",
#             "gstin"
#         ]
#     )

#     for customer in customers:
#         if customer.get("gstin"):
#             customer["has_gstin"] = True
#         else:
#             customer["has_gstin"] = False

#     return {"message": customers}


# # ==========================================
# #  ✅ CORRECTED FUNCTION
# # ==========================================
# @frappe.whitelist(methods=["POST"])
# def create_sales_order():
#     try:
#         data = frappe.request.get_json()
#         if not data:
#             return {"status": "error", "message": "Invalid request data", "code": 400}

#         customer = data.get("customer")
#         items = data.get("items")

#         if not customer:
#             return {"status": "error", "message": "Customer is required", "code": 400}
#         if not items or not isinstance(items, list):
#             return {"status": "error", "message": "At least one item is required", "code": 400}

#         # ✅ Check if customer exists
#         if not frappe.db.exists("Customer", customer):
#             return {"status": "error", "message": f"Customer '{customer}' does not exist.", "code": 404}

#         # ✅ Fetch a company dynamically
#         company_name = frappe.get_all("Company", fields=["name"], limit=1)[0].name
#         default_currency = frappe.get_cached_value("Company", company_name, "default_currency")

#         # ✅ Fetch default Sales Taxes and Charges Template
#         tax_template = frappe.db.get_value(
#             "Sales Taxes and Charges Template",
#             {"is_default": 1, "company": company_name},
#             "name"
#         )

#         # Fallback if no default is set
#         if not tax_template:
#             fallback_template = "Output GST In-state"
#             if frappe.db.exists("Sales Taxes and Charges Template", fallback_template):
#                 tax_template = fallback_template

#         # ✅ Read setting from Chundakkadan Settings
#         enable_stock_validation = frappe.db.get_single_value(
#             "Chundakadan Settings", "enable_stock_validation"
#         )

#         # ✅ Prepare insufficient stock list
#         insufficient_items = []

#         # ✅ Initialize Sales Order document
#         so = frappe.get_doc({
#             "doctype": "Sales Order",
#             "customer": customer,
#             "company": company_name,
#             "currency": data.get("currency") or default_currency,
#             "custom_sales_person": data.get("sales_person"),
#             "delivery_date": data.get("delivery_date") or nowdate(),
#             "transaction_date": data.get("transaction_date") or nowdate(),
#             "items": []
#         })

#         # ✅ Process Items
#         for item in items:
#             item_code = item.get("item_code")
#             req_qty = flt(item.get("qty", 1))
            
#             # Logic to find the correct warehouse
#             warehouse = item.get("warehouse") 
            
#             # 1. Try Item Defaults (Company specific)
#             if not warehouse:
#                 warehouse = frappe.db.get_value("Item Default", {"parent": item_code, "company": company_name}, "default_warehouse")
            
#             # 2. Try Item Master default
#             if not warehouse:
#                 warehouse = frappe.db.get_value("Item", item_code, "default_warehouse")

#             if not warehouse:
#                 return {"status": "error", "message": f"Warehouse not specified for item {item_code}", "code": 400}

#             # ✅ Validate stock availability only if setting is enabled
#             if enable_stock_validation:
#                 available_qty = flt(
#                     frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty") or 0
#                 )

#                 if req_qty > available_qty:
#                     insufficient_items.append(
#                         f"Insufficient stock: Item {item_code} - only {available_qty} in stock in warehouse {warehouse}, but {req_qty} requested."
#                     )

#             # ✅ Append item with BOTH price_list_rate AND rate to prevent NoneType error
#             so.append("items", {
#                 "item_code": item_code,
#                 "warehouse": warehouse,
#                 "qty": req_qty,
#                 "description": item.get("description", ""),
#                 "discount_amount": flt(item.get("discount_amount", 0.0)),
#                 "price_list_rate": flt(item.get("rate", 0.0)), 
#                 "rate": flt(item.get("rate", 0.0)),  # <--- CRITICAL FIX
#             })

#         # ✅ Stop if any stock issues found
#         if insufficient_items:
#             if len(insufficient_items) == 1:
#                 return {
#                     "status": "error",
#                     "message": f"Insufficient stock: {insufficient_items[0]}",
#                     "code": 400
#                 }
#             else:
#                 return {
#                     "status": "error",
#                     "message": insufficient_items,
#                     "code": 400
#                 }

#         # ✅ Apply Taxes & Calculations
#         # We call set_missing_values first to populate UOMs and conversion factors
#         so.run_method("set_missing_values")

#         if tax_template:
#             so.taxes_and_charges = tax_template
#             so.set_taxes()

#         so.run_method("set_other_charges")
#         so.run_method("calculate_taxes_and_totals")

#         # ✅ Insert and Submit
#         so.insert()
#         so.submit()

#         response_data = {
#             "sales_order_id": so.name,
#             "delivery_date": so.delivery_date,
#             "customer": customer,
#             "company": so.company,
#             "items": items,
#             "taxes_and_charges": so.taxes_and_charges,
#             "total": so.total,
#             "grand_total": so.grand_total,
#             "status": so.status,
#         }

#         return {
#             "status": "success",
#             "message": "Sales Order created successfully",
#             "data": response_data,
#             "code": 201
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Sales Order Creation Error")
#         return {"status": "error", "message": str(e), "code": 417}


# @frappe.whitelist()
# def get_sales_orders_with_details(sales_person_id=None):
#     if not sales_person_id:
#         return {
#             "status": "error",
#             "message": "Sales Person ID is required"
#         }

#     sales_order_names = frappe.get_all(
#         "Sales Order",
#         filters={
#             "custom_sales_person": sales_person_id,
#             "docstatus": 1
#         },
#         pluck="name"
#     )

#     sales_orders = []
#     for so_name in sales_order_names:
#         doc = frappe.get_doc("Sales Order", so_name)
#         sales_orders.append({
#             "name": doc.name,
#             "customer": doc.customer,
#             "delivery_date": doc.delivery_date,
#             "total": doc.total,
#             "total_taxes_and_charges": doc.total_taxes_and_charges,
#             "grand_total": doc.grand_total,
#             "rounded total":doc.rounded_total,
#             "items": [
#                 {
#                     "item_code": item.item_code,
#                     "qty": item.qty,
#                     "rate": item.rate,
#                     "amount": item.amount
#                 } for item in doc.items
#             ]
#         })

#     return {
#         "status": "success",
#         "sales_orders": sales_orders
#     }

# @frappe.whitelist()
# def get_employee_location_entries(employee=None):
#     if not employee:
#         frappe.throw(_("Employee is required"))

#     try:
#         results = []
#         logs = frappe.get_all(
#             "Employee Location Log",
#             filters={"employee": employee},
#             fields=["name"]
#         )

#         if not logs:
#             return []

#         log_names = [log.name for log in logs]

#         entries = frappe.get_all(
#             "Employee Location Entry",
#             filters={"parent": ["in", log_names]},
#             fields=["parent", "latitude", "longitude", "creation"]
#         )

#         return entries

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "get_employee_location_entries error")
#         frappe.throw(_("Failed to fetch employee location entries."))

# @frappe.whitelist(allow_guest=False)
# def get_sales_invoice_list():
#     sales_person = frappe.request.args.get("sales_person")
#     if not sales_person:
#         return {
#             "status": "error",
#             "message": "Missing sales_person parameter"
#         }

#     invoices = frappe.get_all(
#         "Sales Invoice",
#         filters={
#             "docstatus": 1,
#             "custom_sales_person": sales_person,
#             "is_return": 0 
#         },
#         fields=[
#             "name", "customer", "posting_date", "due_date",
#             "grand_total", "outstanding_amount", "status"
#         ],
#         order_by="creation desc"     )

#     result = []

#     for inv in invoices:
#         items = frappe.get_all(
#             "Sales Invoice Item",
#             filters={"parent": inv.name},
#             fields=[
#                 "item_code", "item_name", "qty", "rate", "amount", "description"
#             ]
#         )

#         payment_refs = frappe.get_all(
#             "Payment Entry Reference",
#             filters={
#                 "reference_doctype": "Sales Invoice",
#                 "reference_name": inv.name
#             },
#             fields=["parent", "allocated_amount"],
#         )

#         payments = []
#         for ref in payment_refs:
#             try:
#                 payment = frappe.get_doc("Payment Entry", ref.parent)
#                 payments.append({
#                     "payment_entry": payment.name,
#                     "posting_date": payment.posting_date,
#                     "mode_of_payment": payment.mode_of_payment,
#                     "paid_amount": payment.paid_amount,
#                     "allocated_amount": ref.allocated_amount,
#                     "status": payment.status
#                 })
#             except frappe.DoesNotExistError:
#                 continue

#         result.append({
#             "invoice_id": inv.name,
#             "customer": inv.customer,
#             "posting_date": inv.posting_date,
#             "due_date": inv.due_date,
#             "grand_total": inv.grand_total,
#             "outstanding_amount": inv.outstanding_amount,
#             "status": inv.status,
#             "items": items,
#             "payments": payments
#         })

#     return {
#         "status": "success",
#         "sales_person": sales_person,
#         "invoice_count": len(result),
#         "invoices": result
#     }

# @frappe.whitelist(methods=["POST"])
# def pay_sales_invoice():
#     data = frappe.request.get_json()

#     invoice_name = data.get("invoice_name")
#     payment_amount = float(data.get("payment_amount", 0))
#     mode_of_payment = data.get("mode_of_payment", "Cash")
#     reference_no = data.get("reference_no", "")
#     reference_date = data.get("reference_date", nowdate())
#     posting_date = data.get("posting_date", nowdate())

#     if not invoice_name or payment_amount <= 0:
#         return {
#             "status": "error",
#             "message": "Invoice name and valid payment amount are required",
#             "code": 400
#         }

#     invoice = frappe.get_doc("Sales Invoice", invoice_name)

#     if invoice.docstatus != 1:
#         return {
#             "status": "error",
#             "message": "Invoice is not submitted",
#             "code": 400
#         }

#     if invoice.outstanding_amount <= 0:
#         return {
#             "status": "error",
#             "message": "Invoice already paid",
#             "code": 400
#         }

#     paid_to = frappe.db.get_value("Mode of Payment Account", {
#         "parent": mode_of_payment,
#         "company": invoice.company
#     }, "default_account")

#     if not paid_to:
#         return {
#             "status": "error",
#             "message": f"Account not found for Mode of Payment '{mode_of_payment}' in company '{invoice.company}'",
#             "code": 400
#         }

#     payment_entry_data = {
#         "doctype": "Payment Entry",
#         "payment_type": "Receive",
#         "party_type": "Customer",
#         "party": invoice.customer,
#         "company": invoice.company,
#         "posting_date": posting_date,
#         "mode_of_payment": mode_of_payment,
#         "paid_to": paid_to,
#         "paid_amount": payment_amount,
#         "received_amount": payment_amount,
#         "reference_no": reference_no,
#         "reference_date": reference_date,
#         "references": [
#             {
#                 "reference_doctype": "Sales Invoice",
#                 "reference_name": invoice.name,
#                 "total_amount": invoice.grand_total,
#                 "outstanding_amount": invoice.outstanding_amount,
#                 "allocated_amount": payment_amount
#             }
#         ]
#     }

#     if mode_of_payment.lower() in ["Cheque", "Bank Draft"]:
#         if not reference_no or not reference_date:
#             return {
#                 "status": "error",
#                 "message": f"{mode_of_payment} requires Reference No and Reference Date",
#                 "code": 400
#             }

#         if mode_of_payment.lower() == "cheque":
#             payment_entry_data.update({
#                 "cheque_no": reference_no,
#                 "cheque_date": reference_date
#             })

#         if mode_of_payment.lower() == "bank transfer":
#             payment_entry_data.update({
#                 "reference_no": reference_no,
#                 "reference_date": reference_date
#             })

#     payment_entry = frappe.get_doc(payment_entry_data)
#     payment_entry.insert(ignore_permissions=True)

#     return {
#         "status": "success",
#         "payment_entry": payment_entry.name
#     }

# @frappe.whitelist()
# def get_customer_sales_invoices_by_salesperson(sales_person=None, customer=None):
#     if not sales_person:
#         frappe.throw("Sales Person ID is required")

#     filters = {
#         "docstatus": 1,
#         "custom_sales_person": sales_person,
#         "is_return": 0   
#     }

#     if customer:
#         filters["customer"] = customer

#     try:
#         invoices = frappe.get_all(
#             "Sales Invoice",
#             filters=filters,
#             fields=[
#                 "name",
#                 "customer",
#                 "posting_date",
#                 "due_date",
#                 "grand_total",
#                 "outstanding_amount",
#                 "status"
#             ],
#             order_by="posting_date desc"
#         )

#         invoice_data = []
#         total_outstanding = 0

#         for inv in invoices:
#             items = frappe.get_all(
#                 "Sales Invoice Item",
#                 filters={"parent": inv.name},
#                 fields=["item_code", "item_name", "qty", "rate", "amount"]
#             )

#             total_outstanding += inv.outstanding_amount or 0

#             invoice_data.append({
#                 "invoice_name": inv.name,
#                 "customer": inv.customer,
#                 "posting_date": inv.posting_date,
#                 "due_date": inv.due_date,
#                 "grand_total": inv.grand_total,
#                 "outstanding_amount": inv.outstanding_amount,
#                 "status": inv.status,
#                 "items": items
#             })

#         return {
#             "status": "success",
#             "sales_person": sales_person,
#             "customer": customer,
#             "invoice_count": len(invoice_data),
#             "total_outstanding_amount": total_outstanding,
#             "invoices": invoice_data
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "get_customer_sales_invoices_by_salesperson")
#         return {
#             "status": "error",
#             "message": str(e)
#         }

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

#         location_entries = []
#         if log_names:
#             location_entries = frappe.get_all(
#                 "Employee Location Entry",
#                 filters={"parent": ["in", log_names]},
#                 fields=["parent", "latitude", "longitude", "creation", "time"],
#                 order_by="creation asc"
#             )

#             for entry in location_entries:
#                 if entry.get("time"):
#                     entry["time"] = frappe.utils.format_time(entry["time"])

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

# @frappe.whitelist()
# def get_mode_of_payment():
#     try:
#         mode=frappe.get_all(
#             "Mode of Payment",
#             fields=["name","execute"]
#         )
#         for m in mode:
#             m["execute"]=bool(m.get("execute"))

#         return mode

#     except Exception as e:
#         frappe.throw("failed to fetch"+str(e))

# @frappe.whitelist(allow_guest=False)
# def create_payment_entry_from_sales_invoices():
#     data = frappe.local.form_dict

#     if frappe.request and frappe.request.data:
#         data = json.loads(frappe.request.data)

#     customer = data.get("customer")
#     total_allocated_amount = data.get("total_allocated_amount")
#     mode_of_payment = data.get("mode_of_payment")
#     invoice_allocations = data.get("invoice_allocations", [])
#     reference_no = data.get("reference_no")
#     reference_date = data.get("reference_date")

#     if not customer or not total_allocated_amount or not mode_of_payment :
#         frappe.throw(_("Missing required fields"))

#     if mode_of_payment in ["Cheque", "Bank Transfer"]:
#         if not reference_no or not reference_date:
#             frappe.throw(_("Reference No and Reference Date are required for Cheque or Bank Transfer payments."))

#     pe = frappe.new_doc("Payment Entry")
#     pe.payment_type = "Receive"
#     pe.party_type = "Customer"
#     pe.party = customer
#     pe.posting_date = now()
#     pe.custom_sales_person = data.get("sales_person")
#     pe.mode_of_payment = mode_of_payment
#     pe.paid_amount = total_allocated_amount
#     pe.received_amount = total_allocated_amount
#     pe.target_exchange_rate = 1
#     pe.paid_to = frappe.get_value("Mode of Payment Account", {
#         "parent": mode_of_payment
#     }, "default_account")

#     if mode_of_payment in ["Cheque", "Bank Draft"]:
#         pe.reference_no = reference_no
#         pe.reference_date = reference_date

#     allocated_total = 0

#     for alloc in invoice_allocations:
#         invoice_outstanding = frappe.get_value("Sales Invoice", alloc["invoice"], "outstanding_amount") or 0
#         allocation_amount = min(float(alloc["amount"]), invoice_outstanding)

#         if allocation_amount > 0:
#             pe.append("references", {
#                 "reference_doctype": "Sales Invoice",
#                 "reference_name": alloc["invoice"],
#                 "allocated_amount": allocation_amount
#             })
#             allocated_total += allocation_amount

#     if float(total_allocated_amount) > allocated_total:
#         pe.unallocated_amount = float(total_allocated_amount) - allocated_total

#     pe.insert()
#     frappe.db.commit()

#     return {
#         "message": "Payment Entry created",
#         "payment_entry": pe.name
#     }

# @frappe.whitelist(allow_guest=True)
# def get_sales_returns(sales_person=None, invoice_id=None):
#     try:
#         if not sales_person:
#             return {
#                 "status": "error",
#                 "message": "Sales Person ID is required",
#                 "code": 400
#             }

#         filters = {
#             "is_return": 1,
#             "custom_sales_person": sales_person
#         }

#         if invoice_id:
#             filters["return_against"] = invoice_id

#         sales_returns = frappe.get_all(
#             "Sales Invoice",
#             filters=filters,
#             fields=[
#                 "name",
#                 "return_against",
#                 "customer",
#                 "company",
#                 "posting_date",
#                 "workflow_state",
#                 "custom_sales_person",
#                 "custom_return_reason"
#             ],
#             order_by="creation desc"
#         )

#         for sr in sales_returns:
#             sr["items"] = frappe.get_all(
#                 "Sales Invoice Item",
#                 filters={"parent": sr["name"]},
#                 fields=["item_code", "item_name", "qty", "rate", "amount"]
#             )

#         return {
#             "status": "success",
#             "data": sales_returns
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Get Sales Returns API Error")
#         return {
#             "status": "error",
#             "message": f"An error occurred: {str(e)}",
#             "code": 500
#         }

# @frappe.whitelist()
# def payment_entry_status():
#     customer_name = frappe.request.args.get("customer_name")
#     sales_person = frappe.request.args.get("sales_person")

#     if not customer_name:
#         return {"status": "error", "message": "Missing customer_name"}
#     if not sales_person:
#         return {"status": "error", "message": "Missing sales_person"}

#     payment_entries = frappe.get_all(
#         "Payment Entry",
#         filters={
#             "party_type": "Customer",
#             "party": customer_name,
#             "custom_sales_person": sales_person,
#             "docstatus": 0
#         },
#         fields=["name", "posting_date", "paid_amount", "reference_no"]
#     )

#     result = []
#     total_allocated = 0

#     for pe in payment_entries:
#         references = frappe.get_all(
#             "Payment Entry Reference",
#             filters={"parent": pe.name},
#             fields=["reference_name", "allocated_amount", "reference_doctype"]
#         )

#         ref_list = []
#         for ref in references:
#             total_allocated += ref.allocated_amount or 0
#             ref_list.append({
#                 "reference_doctype": ref.reference_doctype,
#                 "reference_name": ref.reference_name,
#                 "allocated_amount": ref.allocated_amount
#             })

#         result.append({
#             "payment_entry": pe.name,
#             "posting_date": pe.posting_date,
#             "paid_amount": pe.paid_amount,
#             "reference_no": pe.reference_no,
#             "status": "Draft",
#             "references": ref_list
#         })

#     return {
#         "status": "success",
#         "data": result,
#         "total_allocated_amount": total_allocated
#     }

# @frappe.whitelist(allow_guest=False)
# def save_fcm_token(fcm_token):
#     employee = frappe.session.user
#     if not employee:
#         frappe.throw("Not logged in")

#     doc = frappe.get_doc({
#         "doctype": "FCM Token",
#         "user": employee,
#         "token": fcm_token
#     })
#     doc.insert(ignore_permissions=True)
#     return {"status": "success", "message": "Token saved"}

# @frappe.whitelist(methods=["POST"])
# def location_entry():
#     data = frappe.request.get_json()

#     employee_id = data.get("employee_id")
#     employee_name = data.get("employee_name")
#     date = data.get("date")
#     time = data.get("time")
#     longitude = data.get("longitude")
#     latitude = data.get("latitude")

#     if not (employee_id and employee_name and date and time and longitude and latitude):
#         return {
#             "status": "error",
#             "message": "Please fill all required fields.",
#             "code": 400
#         }

#     try:
#         log_name = frappe.db.get_value("Employee Location Log", {
#             "employee_id": employee_id,
#             "date": date
#         }, "name")

#         if log_name:
#             doc = frappe.get_doc("Employee Location Log", log_name)
#         else:
#             doc = frappe.new_doc("Employee Location Log")
#             doc.employee_id = employee_id
#             doc.employee_name = employee_name
#             doc.date = date
#             doc.insert()

#         doc.append("employee_location_entry", {
#             "time": time,
#             "longitude": longitude,
#             "latitude": latitude
#         })

#         doc.save()
#         frappe.db.commit()

#         return {
#             "status": "success",
#             "message": "Location entry saved.",
#             "log_id": doc.name
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Location Entry API Error")
#         return {
#             "status": "error",
#             "message": f"An error occurred: {str(e)}",
#             "code": 500
#         }

# @frappe.whitelist(methods=["POST"])
# def create_location_log():
#     data = frappe.request.get_json()
#     employee_id = data.get("employee_id")
#     employee_name = data.get("employee_name")
#     date = data.get("date")

#     if not (employee_id and employee_name and date):
#         return {
#             "status": "error",
#             "message": "All fields required.",
#             "code": 400
#         }

#     if frappe.db.exists("Employee Location Log", {"employee_id": employee_id, "date": date}):
#         return {
#             "status": "error",
#             "message": "Log already exists for this employee and date.",
#             "code": 409
#         }

#     doc = frappe.new_doc("Employee Location Log")
#     doc.employee = employee_id
#     doc.employee_name = employee_name
#     doc.date = date
#     doc.insert()
#     frappe.db.commit()

#     return {
#         "status": "success",
#         "log_id": doc.name,
#         "empl_id":doc.employee_id ,
#         "empl_name": doc.employee_name
#     }

# @frappe.whitelist(methods=["POST"])
# def append_location_entry():
#     data = frappe.request.get_json()
#     employee_id = data.get("employee_id")
#     date = data.get("date")
#     entries = data.get("entries")

#     if not (employee_id and date and isinstance(entries, list) and entries):
#         return {
#             "status": "error",
#             "message": "Required fields missing or invalid entries.",
#             "code": 400
#         }

#     log_name = frappe.db.get_value("Employee Location Log", {
#         "employee": employee_id,
#         "date": date
#     })

#     if not log_name:
#         return {
#             "status": "error",
#             "message": "Parent log does not exist. Check-in required first.",
#             "code": 404
#         }

#     doc = frappe.get_doc("Employee Location Log", log_name)

#     for entry in entries:
#         if "time" in entry and "latitude" in entry and "longitude" in entry:
#             doc.append("locations", {
#                 "time": entry["time"],
#                 "latitude": entry["latitude"],
#                 "longitude": entry["longitude"]
#             })

#     doc.save()
#     frappe.db.commit()

#     return {
#         "status": "success",
#         "message": f"{len(entries)} entries saved.",
#         "log_id": log_name
#     }

# @frappe.whitelist(methods=["POST"])
# def save_salesperson_location_log():
#     data = frappe.request.get_json()
#     salesperson_id = data.get("sales_person_id")
#     date = data.get("date")
#     entries = data.get("entries", [])

#     if not (salesperson_id and date):
#         return {
#             "status": "error",
#             "message": "Sales Person ID and Date are required.",
#             "code": 400
#         }

#     log_name = frappe.db.get_value("Employee Location Log", {
#         "employee": salesperson_id,
#         "date": date
#     })

#     if log_name:
#         doc = frappe.get_doc("Employee Location Log", log_name)
#         new_log_created = False
#     else:
#         doc = frappe.new_doc("Employee Location Log")
#         doc.employee = salesperson_id
#         doc.date = date
#         new_log_created = True

#     added = 0
#     for entry in entries:
#         if "time" in entry and "latitude" in entry and "longitude" in entry:
#             doc.append("locations", {
#                 "time": entry["time"],
#                 "latitude": entry["latitude"],
#                 "longitude": entry["longitude"],
#                 "entry_type": entry.get("entry_type", "Track")
#             })
#             added += 1

#     doc.save(ignore_permissions=True)
#     frappe.db.commit()

#     return {
#         "status": "success",
#         "message": f"{'Log created. ' if new_log_created else ''}{added} location entries saved.",
#         "log_id": doc.name,
#         "sales_person_id": salesperson_id
#     }

# @frappe.whitelist(allow_guest=False)
# def log_customer_visit():
#     data = json.loads(frappe.request.data)

#     required_fields = ["sales_person", "date", "time", "longitude", "latitude", "customer_name"]
#     for field in required_fields:
#         if not data.get(field):
#             frappe.throw(_("Missing required field: {0}").format(field))

#     doc = frappe.new_doc("Customer Visit Log")
#     doc.employee = data["sales_person"]
#     doc.date = data["date"]
#     doc.time = data["time"]
#     doc.longitude = data["longitude"]
#     doc.latitude = data["latitude"]
#     doc.customer_name = data["customer_name"]
#     doc.description = data.get("description", "")
#     doc.insert()

#     return {
#         "success": True,
#         "message": "Customer Visit Log created successfully",
#         "name": doc.name
#     }

# @frappe.whitelist(allow_guest=False)
# def get_all_sales_invoice_ids(sales_person=None):
#     if not sales_person:
#         frappe.throw("Sales Person ID is required")

#     try:
#         filters = {
#             "docstatus": 1,
#             "is_return": 0,
#             "custom_sales_person": sales_person
#         }

#         invoices = frappe.get_all(
#             "Sales Invoice",
#             filters=filters,
#             fields=["name", "customer", "outstanding_amount"],
#             order_by="posting_date desc"
#         )

#         return {
#             "status": "success",
#             "code": 200,
#             "message": "Successfully fetched all sales invoices",
#             "data": invoices
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "API Error: get_all_sales_invoice_ids")
#         return {
#             "status": "error",
#             "code": 500,
#             "message": f"An unexpected error occurred: {str(e)}",
#             "data": None
#         }

# @frappe.whitelist()
# def sales_invoice_detail_by_ids():
#     try:
#         invoice_id = frappe.form_dict.get("invoice_id")

#         if not invoice_id:
#             return {
#                 "status": "error",
#                 "code": 400,
#                 "message": "invoice_id is required",
#                 "data": None
#             }

#         try:
#             invoice = frappe.get_doc("Sales Invoice", invoice_id)
#         except frappe.DoesNotExistError:
#             return {
#                 "status": "error",
#                 "code": 404,
#                 "message": f"Sales Invoice '{invoice_id}' does not exist",
#                 "data": None
#             }

#         data = {
#             "posting_date": invoice.posting_date,
#             "customer": invoice.customer,
#             "items": [
#                 {
#                     "item_code": item.item_code,
#                     "item_name": item.item_name,
#                     "qty": item.qty,
#                     "rate": item.rate,
#                     "amount": item.amount
#                 }
#                 for item in invoice.items
#             ]
#         }

#         return {
#             "status": "success",
#             "code": 200,
#             "message": "Sales Invoice fetched successfully",
#             "data": data
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "API Error: sales_invoice_detail_by_ids")
#         return {
#             "status": "error",
#             "code": 500,
#             "message": f"An unexpected error occurred: {str(e)}",
#             "data": None
#         }

# @frappe.whitelist()
# def get_location_update_interval():
#     try:
#         data=frappe.get_doc("Location Update Settings","Location Update Settings")
#         return{
#             "status":"success",
#             "code":200,
#             "message":f"successfully fetch location update interval",
#             "data":data
#         }
#     except Exception as e:
#         return{
#             "status":"error",
#             "code":500,
#             "message":f"an error occured,{str(e)}"

#         }

# @frappe.whitelist()
# def get_item_tax():
#     templates = frappe.get_all(
#         "Item Tax Template",
#         fields=["name", "title", "gst_rate"]
#     )
    
#     result = []
#     for t in templates:
#         result.append({
#             "name": t.name,
#             "title": t.title,
#             "gst_rate": t.gst_rate or 0
#         })
    
#     return result

# @frappe.whitelist()
# def create_sales_return():
#     from collections import defaultdict

#     data = frappe.request.get_json()
#     company = data.get("company") or frappe.db.get_single_value("Global Defaults", "default_company")

#     def get_default_tax_template(company):
#         return frappe.db.get_value(
#             "Sales Taxes and Charges Template",
#             {"company": company, "is_default": 1},
#             "name"
#         )

#     sales_return = frappe.new_doc("Sales Invoice")
#     sales_return.is_return = 1
#     sales_return.posting_date = data.get("return_date") or frappe.utils.nowdate()
#     sales_return.customer = data.get("customer")
#     sales_return.company = company
#     sales_return.custom_sales_person = data.get("sales_person")
#     sales_return.custom_return_reason = data.get("return_reason")

#     if data.get("return_against"):
#         sales_return.return_against = data.get("return_against")
#         orig_inv = frappe.get_doc("Sales Invoice", data.get("return_against"))

#         if orig_inv.taxes_and_charges:
#             sales_return.taxes_and_charges = orig_inv.taxes_and_charges
#             for t in orig_inv.taxes:
#                 sales_return.append("taxes", {
#                     "charge_type": t.charge_type,
#                     "account_head": t.account_head,
#                     "rate": t.rate,
#                     "description": t.description
#                 })

#         original_item_map = defaultdict(float)
#         for it in orig_inv.items:
#             original_item_map[it.item_code] += flt(it.qty)

#         submitted_returns = frappe.get_all(
#             "Sales Invoice",
#             filters={
#                 "is_return": 1,
#                 "return_against": data.get("return_against"),
#                 "docstatus": 1
#             },
#             pluck="name"
#         )
#         returned_item_map = defaultdict(float)
#         if submitted_returns:
#             returned_rows = frappe.get_all(
#                 "Sales Invoice Item",
#                 filters={"parent": ["in", submitted_returns]},
#                 fields=["item_code", "qty"]
#             )
#             for r in returned_rows:
#                 returned_item_map[r["item_code"]] += abs(flt(r["qty"]))

#     else:
#         tax_template = get_default_tax_template(company)
#         if tax_template:
#             sales_return.taxes_and_charges = tax_template
#             taxes = frappe.get_all(
#                 "Sales Taxes and Charges",
#                 filters={"parent": tax_template},
#                 fields=["charge_type", "account_head", "rate", "description"]
#             )
#             for t in taxes:
#                 sales_return.append("taxes", t)

#     errors = []
#     for item in data.get("items", []):
#         qty = flt(item.get("qty"))
#         item_code = item.get("item_code")

#         if data.get("return_against"):
#             sold_qty = original_item_map.get(item_code, 0.0)
#             already_returned = returned_item_map.get(item_code, 0.0)
#             remaining = sold_qty - already_returned
#             if qty > remaining:
#                 errors.append(
#                     f"Item {item_code}: requested return {qty} exceeds remaining {remaining} "
#                     f"(sold {sold_qty} - already returned {already_returned})"
#                 )

#         sales_return.append("items", {
#             "item_code": item_code,
#             "qty": -abs(qty),
#             "rate": flt(item.get("rate")),
#             "amount": -abs(qty) * flt(item.get("rate"))
#         })

#     if errors:
#         return {"status": "error", "message": errors}

#     sales_return.run_method("set_other_charges")
#     sales_return.run_method("set_missing_values")
#     sales_return.run_method("calculate_taxes_and_totals")
#     sales_return.save(ignore_permissions=True)

#     frappe.local.response["_server_messages"] = None
#     frappe.clear_messages()

#     return {                            
#         "status": "success",
#         "sales_return": sales_return.name,
#         "tax_template": sales_return.taxes_and_charges
#     }

# @frappe.whitelist(allow_guest=True)
# def update_chundakadan_settings(enable_stock_validation):
#     try:
#         if not frappe.has_permission("Chundakadan Settings", "write"):
#             return {
#                 "status": "error",
#                 "message": "Not permitted to update settings",
#                 "http_status_code": 403
#             }

#         if isinstance(enable_stock_validation, str):
#             enable_stock_validation = enable_stock_validation.lower() == 'true'
#         doc = frappe.get_single("Chundakadan Settings")
#         doc.db_set('enable_stock_validation', 1 if enable_stock_validation else 0)
#         frappe.db.commit()

#         return {
#             "status": "success",
#             "message": "Settings updated successfully",
#             "data": {
#                 "enable_stock_validation": bool(doc.enable_stock_validation)
#             },
#             "http_status_code": 200
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Settings Update Error")

# @frappe.whitelist(allow_guest=True)
# def get_chundakadan_settings():
#     try:
#         if not frappe.has_permission("Chundakadan Settings", "read"):
#             return {
#                 "status": "error",
#                 "message": "Not permitted to read settings",
#                 "http_status_code": 403
#             }

#         doc = frappe.get_single("Chundakadan Settings")
        
#         return {
#             "status": "success",
#             "message": "Settings retrieved successfully",
#             "data": {
#                 "enable_stock_validation": bool(doc.enable_stock_validation)
#             },
#             "http_status_code": 200
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Settings Fetch Error")
#         return {
#             "status": "error",
#             "message": str(e),
#             "http_status_code": 500
#         }

# @frappe.whitelist(allow_guest=True)
# def get_task_details():
#     try:
#         sa = frappe.form_dict.get("sales_person")
#         if not sa :
#             return{
#                 "status":"error",
#                 "message":"sales person isrequired",
#                 "code":400
#             }
#         docs = frappe.get_all(
#             "Task",
#             fields=[
#                 'name', 'subject', 'status',
#                 'custom_customer', 'custom_assigned_to',
#                 'exp_start_date', 'exp_end_date', 'description',"custom_remarks"
#             ],
#             filters={"custom_assigned_to":sa}
#         )

#         for d in docs:
#             if d.get("description"):
#                 soup = BeautifulSoup(d["description"], "html.parser")
#                 d["description"] = soup.get_text()

#         return {
#             "status": "success",
#             "message": "task details retrieved",
#             "data": docs,
#             "code": 200
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Task Fetch Error")
#         return {
#             "status": "error",
#             "message": str(e),
#             "http_status_code": 500
#         }

# @frappe.whitelist(allow_guest=True)
# def update_status():
#     try:
#         data = frappe.request.get_json()
#         task_name = data.get("task_name")
#         new_status = data.get("status")
#         completion_date = data.get("completion_date")

#         if not task_name or not new_status:
#             return {
#                 "status": "error",
#                 "message": "Task name and status are required",
#                 "code": 400
#             }

#         if new_status == "Completed":
#             if not completion_date:
#                 return {
#                     "status": "error",
#                     "message": "Completion date is required when status is Completed",
#                     "code": 400
#                 }

#         task = frappe.get_doc("Task", task_name)
#         task.status = new_status

#         if new_status == "Completed" and completion_date:
#             task.completed_on = completion_date

#         task.save(ignore_permissions=True)
#         frappe.db.commit()

#         return {
#             "status": "success",
#             "message": f"Task {task_name} updated to {new_status}",
#             "code": 200
#         }

#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "Task Status Update Error")
#         return {
#             "status": "error",
#             "message": str(e),
#             "code": 500
#         }

# @frappe.whitelist(allow_guest=True)
# def add_remarks():
#     try:
#         data=frappe.request.get_json()
#         remarks=data.get("remarks")
#         task_name=data.get("task_name")
#         task=frappe.get_doc("Task",task_name)
#         task.custom_remarks=remarks
#         task.save(ignore_permissions=True)  
#         frappe.db.commit()
#         return{
#             "satatus":"success",
#             "message":f"remarks {remarks}added to  Task {task_name} ",
#             "code":200
#         }
#     except Exception as e:
#         frappe.log_error(frappe.get_traceback(), "remarks add  Error")
#         return {
#             "status": "error",
#             "message": str(e),
#             "code": 500
#         }


import json
import frappe
from frappe import _
from frappe.utils import now, nowdate, flt
from frappe.model.document import Document
from frappe.utils.password import set_encrypted_password
from bs4 import BeautifulSoup

@frappe.whitelist(allow_guest=True)
def response(message, data, success, status_code):
    '''method to generates responses of an API'''
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
    if hasattr(frappe.local, 'session') and frappe.local.session.data:
        frappe.local.session.data['device'] = 'mobile'
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
    
        # Get tax template from Item Taxes table
        tax_template = frappe.db.get_value(
            "Item Tax",
            filters={"parent": item.name},
            fieldname="item_tax_template"
        )

        result.append({
            "item_code": item.name,
            "item_name": item.item_name,
            "description": item.description,
            "uom": item.stock_uom,
            "price": price or 0.0,
            "maintain_stock": item.is_stock_item,
            "tax_template": tax_template or ""
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
            "gstin"
        ]
    )

    for customer in customers:
        if customer.get("gstin"):
            customer["has_gstin"] = True
        else:
            customer["has_gstin"] = False

    return {"message": customers}


# ==========================================
#  🚀 FINAL FIXED FUNCTION WITH STOCK IGNORE
# ==========================================
@frappe.whitelist(methods=["POST"])
def create_sales_order():
    try:
        data = frappe.request.get_json()
        if not data:
            return {"status": "error", "message": "Invalid request data", "code": 400}

        customer = data.get("customer")
        items = data.get("items")

        if not customer:
            return {"status": "error", "message": "Customer is required", "code": 400}
        if not items or not isinstance(items, list):
            return {"status": "error", "message": "At least one item is required", "code": 400}

        if not frappe.db.exists("Customer", customer):
            return {"status": "error", "message": f"Customer '{customer}' does not exist.", "code": 404}

        company_name = frappe.get_all("Company", fields=["name"], limit=1)[0].name
        default_currency = frappe.get_cached_value("Company", company_name, "default_currency")

        tax_template = frappe.db.get_value(
            "Sales Taxes and Charges Template",
            {"is_default": 1, "company": company_name},
            "name"
        )

        if not tax_template:
            fallback_template = "Output GST In-state"
            if frappe.db.exists("Sales Taxes and Charges Template", fallback_template):
                tax_template = fallback_template

        enable_stock_validation = frappe.db.get_single_value(
            "Chundakadan Settings", "enable_stock_validation"
        )

        insufficient_items = []

        so = frappe.get_doc({
            "doctype": "Sales Order",
            "customer": customer,
            "company": company_name,
            "currency": data.get("currency") or default_currency,
            "custom_sales_person": data.get("sales_person"),
            "delivery_date": data.get("delivery_date") or nowdate(),
            "transaction_date": data.get("transaction_date") or nowdate(),
            "custom_special_order": 0 if enable_stock_validation else 1,
            "items": []
        })

        # ==========================================================
        #  ITEM PROCESSING & STOCK VALIDATION
        # ==========================================================
        for item in items:
            item_code = item.get("item_code")
            req_qty = flt(item.get("qty", 1))

            warehouse = item.get("warehouse") or \
                        frappe.db.get_value("Item Default", {"parent": item_code, "company": company_name}, "default_warehouse") or \
                        frappe.db.get_value("Item", item_code, "default_warehouse")

            if not warehouse:
                return {"status": "error", "message": f"Warehouse not specified for item {item_code}", "code": 400}

            # ❗ Only validate when enabled (true)
            if enable_stock_validation:
                available_qty = flt(frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty") or 0)
                if req_qty > available_qty:
                    insufficient_items.append(
                        f"Insufficient stock: Item {item_code} - only {available_qty} available, but {req_qty} requested."
                    )

            so.append("items", {
                "item_code": item_code,
                "warehouse": warehouse,
                "qty": req_qty,
                "price_list_rate": flt(item.get("rate", 0)),
                "rate": flt(item.get("rate", 0)),
                "discount_amount": flt(item.get("discount_amount", 0)),
            })

        if enable_stock_validation and insufficient_items:
            return {"status": "error", "message": insufficient_items, "code": 400}

        # ==========================================================
        #  TAX & TOTALS
        # ==========================================================
        so.run_method("set_missing_values")

        if tax_template:
            so.taxes_and_charges = tax_template
            so.set_taxes()

        so.run_method("set_other_charges")
        so.run_method("calculate_taxes_and_totals")

        # ==========================================================
        #  🚨 CORE FIX: OVERRIDE ERPNext STOCK CHECKS
        # ==========================================================
        if not enable_stock_validation:
            # FORCE ALLOW ZERO / NEGATIVE STOCK
            so.flags.ignore_stock_validation = True
            so.flags.ignore_validate_update_after_submit = True
            so.flags.ignore_mandatory = True
            so.skip_stock_validation = 1
        else:
            so.skip_stock_validation = 0

        # ==========================================================
        #  SAVE DOCUMENT
        # ==========================================================
        so.insert(ignore_permissions=True)
        so.submit()

        return {
            "status": "success",
            "message": "Sales Order created successfully",
            "data": {
                "sales_order_id": so.name,
                "delivery_date": so.delivery_date,
                "customer": customer,
                "company": so.company,
                "items": items,
                "total": so.total,
                "grand_total": so.grand_total,
                "custom_special_order": so.custom_special_order
            },
            "code": 201
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Sales Order Creation Error")
        return {"status": "error", "message": str(e), "code": 417}


@frappe.whitelist()
def get_sales_orders_with_details(sales_person_id=None):
    if not sales_person_id:
        return {
            "status": "error",
            "message": "Sales Person ID is required"
        }

    sales_order_names = frappe.get_all(
        "Sales Order",
        filters={
            "custom_sales_person": sales_person_id,
            "docstatus": 1
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
            "total": doc.total,
            "total_taxes_and_charges": doc.total_taxes_and_charges,
            "grand_total": doc.grand_total,
            "rounded total":doc.rounded_total,
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

@frappe.whitelist()
def get_employee_location_entries(employee=None):
    if not employee:
        frappe.throw(_("Employee is required"))

    try:
        results = []
        logs = frappe.get_all(
            "Employee Location Log",
            filters={"employee": employee},
            fields=["name"]
        )

        if not logs:
            return []

        log_names = [log.name for log in logs]

        entries = frappe.get_all(
            "Employee Location Entry",
            filters={"parent": ["in", log_names]},
            fields=["parent", "latitude", "longitude", "creation"]
        )

        return entries

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "get_employee_location_entries error")
        frappe.throw(_("Failed to fetch employee location entries."))

@frappe.whitelist(allow_guest=False)
def get_sales_invoice_list():
    sales_person = frappe.request.args.get("sales_person")
    if not sales_person:
        return {
            "status": "error",
            "message": "Missing sales_person parameter"
        }

    invoices = frappe.get_all(
        "Sales Invoice",
        filters={
            "docstatus": 1,
            "custom_sales_person": sales_person,
            "is_return": 0 
        },
        fields=[
            "name", "customer", "posting_date", "due_date",
            "grand_total", "outstanding_amount", "status"
        ],
        order_by="creation desc"     )

    result = []

    for inv in invoices:
        items = frappe.get_all(
            "Sales Invoice Item",
            filters={"parent": inv.name},
            fields=[
                "item_code", "item_name", "qty", "rate", "amount", "description"
            ]
        )

        payment_refs = frappe.get_all(
            "Payment Entry Reference",
            filters={
                "reference_doctype": "Sales Invoice",
                "reference_name": inv.name
            },
            fields=["parent", "allocated_amount"],
        )

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
                continue

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

@frappe.whitelist(methods=["POST"])
def pay_sales_invoice():
    data = frappe.request.get_json()

    invoice_name = data.get("invoice_name")
    payment_amount = float(data.get("payment_amount", 0))
    mode_of_payment = data.get("mode_of_payment", "Cash")
    reference_no = data.get("reference_no", "")
    reference_date = data.get("reference_date", nowdate())
    posting_date = data.get("posting_date", nowdate())

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

    payment_entry_data = {
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
    }

    if mode_of_payment.lower() in ["Cheque", "Bank Draft"]:
        if not reference_no or not reference_date:
            return {
                "status": "error",
                "message": f"{mode_of_payment} requires Reference No and Reference Date",
                "code": 400
            }

        if mode_of_payment.lower() == "cheque":
            payment_entry_data.update({
                "cheque_no": reference_no,
                "cheque_date": reference_date
            })

        if mode_of_payment.lower() == "bank transfer":
            payment_entry_data.update({
                "reference_no": reference_no,
                "reference_date": reference_date
            })

    payment_entry = frappe.get_doc(payment_entry_data)
    payment_entry.insert(ignore_permissions=True)

    return {
        "status": "success",
        "payment_entry": payment_entry.name
    }

@frappe.whitelist()
def get_customer_sales_invoices_by_salesperson(sales_person=None, customer=None):
    if not sales_person:
        frappe.throw("Sales Person ID is required")

    filters = {
        "docstatus": 1,
        "custom_sales_person": sales_person,
        "is_return": 0   
    }

    if customer:
        filters["customer"] = customer

    try:
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

@frappe.whitelist()
def get_location_data(employee=None, date=None):
    if not employee:
        frappe.throw(_("Employee is required"))
    if not date:
        frappe.throw(_("Date is required"))

    try:
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
            location_entries = frappe.get_all(
                "Employee Location Entry",
                filters={"parent": ["in", log_names]},
                fields=["parent", "latitude", "longitude", "creation", "time"],
                order_by="creation asc"
            )

            for entry in location_entries:
                if entry.get("time"):
                    entry["time"] = frappe.utils.format_time(entry["time"])

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

@frappe.whitelist(allow_guest=False)
def create_payment_entry_from_sales_invoices():
    data = frappe.local.form_dict

    if frappe.request and frappe.request.data:
        data = json.loads(frappe.request.data)

    customer = data.get("customer")
    total_allocated_amount = data.get("total_allocated_amount")
    mode_of_payment = data.get("mode_of_payment")
    invoice_allocations = data.get("invoice_allocations", [])
    reference_no = data.get("reference_no")
    reference_date = data.get("reference_date")

    if not customer or not total_allocated_amount or not mode_of_payment :
        frappe.throw(_("Missing required fields"))

    if mode_of_payment in ["Cheque", "Bank Transfer"]:
        if not reference_no or not reference_date:
            frappe.throw(_("Reference No and Reference Date are required for Cheque or Bank Transfer payments."))

    pe = frappe.new_doc("Payment Entry")
    pe.payment_type = "Receive"
    pe.party_type = "Customer"
    pe.party = customer
    pe.posting_date = now()
    pe.custom_sales_person = data.get("sales_person")
    pe.mode_of_payment = mode_of_payment
    pe.paid_amount = total_allocated_amount
    pe.received_amount = total_allocated_amount
    pe.target_exchange_rate = 1
    pe.paid_to = frappe.get_value("Mode of Payment Account", {
        "parent": mode_of_payment
    }, "default_account")

    if mode_of_payment in ["Cheque", "Bank Draft"]:
        pe.reference_no = reference_no
        pe.reference_date = reference_date

    allocated_total = 0

    for alloc in invoice_allocations:
        invoice_outstanding = frappe.get_value("Sales Invoice", alloc["invoice"], "outstanding_amount") or 0
        allocation_amount = min(float(alloc["amount"]), invoice_outstanding)

        if allocation_amount > 0:
            pe.append("references", {
                "reference_doctype": "Sales Invoice",
                "reference_name": alloc["invoice"],
                "allocated_amount": allocation_amount
            })
            allocated_total += allocation_amount

    if float(total_allocated_amount) > allocated_total:
        pe.unallocated_amount = float(total_allocated_amount) - allocated_total

    pe.insert()
    frappe.db.commit()

    return {
        "message": "Payment Entry created",
        "payment_entry": pe.name
    }

@frappe.whitelist(allow_guest=True)
def get_sales_returns(sales_person=None, invoice_id=None):
    try:
        if not sales_person:
            return {
                "status": "error",
                "message": "Sales Person ID is required",
                "code": 400
            }

        filters = {
            "is_return": 1,
            "custom_sales_person": sales_person
        }

        if invoice_id:
            filters["return_against"] = invoice_id

        sales_returns = frappe.get_all(
            "Sales Invoice",
            filters=filters,
            fields=[
                "name",
                "return_against",
                "customer",
                "company",
                "posting_date",
                "workflow_state",
                "custom_sales_person",
                "custom_return_reason"
            ],
            order_by="creation desc"
        )

        for sr in sales_returns:
            sr["items"] = frappe.get_all(
                "Sales Invoice Item",
                filters={"parent": sr["name"]},
                fields=["item_code", "item_name", "qty", "rate", "amount"]
            )

        return {
            "status": "success",
            "data": sales_returns
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Sales Returns API Error")
        return {
            "status": "error",
            "message": f"An error occurred: {str(e)}",
            "code": 500
        }

@frappe.whitelist()
def payment_entry_status():
    customer_name = frappe.request.args.get("customer_name")
    sales_person = frappe.request.args.get("sales_person")

    if not customer_name:
        return {"status": "error", "message": "Missing customer_name"}
    if not sales_person:
        return {"status": "error", "message": "Missing sales_person"}

    payment_entries = frappe.get_all(
        "Payment Entry",
        filters={
            "party_type": "Customer",
            "party": customer_name,
            "custom_sales_person": sales_person,
            "docstatus": 0
        },
        fields=["name", "posting_date", "paid_amount", "reference_no"]
    )

    result = []
    total_allocated = 0

    for pe in payment_entries:
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
        log_name = frappe.db.get_value("Employee Location Log", {
            "employee_id": employee_id,
            "date": date
        }, "name")

        if log_name:
            doc = frappe.get_doc("Employee Location Log", log_name)
        else:
            doc = frappe.new_doc("Employee Location Log")
            doc.employee_id = employee_id
            doc.employee_name = employee_name
            doc.date = date
            doc.insert()

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
    salesperson_id = data.get("sales_person_id")
    date = data.get("date")
    entries = data.get("entries", [])

    if not (salesperson_id and date):
        return {
            "status": "error",
            "message": "Sales Person ID and Date are required.",
            "code": 400
        }

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

    added = 0
    for entry in entries:
        if "time" in entry and "latitude" in entry and "longitude" in entry:
            doc.append("locations", {
                "time": entry["time"],
                "latitude": entry["latitude"],
                "longitude": entry["longitude"],
                "entry_type": entry.get("entry_type", "Track")
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
def get_all_sales_invoice_ids(sales_person=None):
    if not sales_person:
        frappe.throw("Sales Person ID is required")

    try:
        filters = {
            "docstatus": 1,
            "is_return": 0,
            "custom_sales_person": sales_person
        }

        invoices = frappe.get_all(
            "Sales Invoice",
            filters=filters,
            fields=["name", "customer", "outstanding_amount"],
            order_by="posting_date desc"
        )

        return {
            "status": "success",
            "code": 200,
            "message": "Successfully fetched all sales invoices",
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

        if not invoice_id:
            return {
                "status": "error",
                "code": 400,
                "message": "invoice_id is required",
                "data": None
            }

        try:
            invoice = frappe.get_doc("Sales Invoice", invoice_id)
        except frappe.DoesNotExistError:
            return {
                "status": "error",
                "code": 404,
                "message": f"Sales Invoice '{invoice_id}' does not exist",
                "data": None
            }

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

@frappe.whitelist()
def get_item_tax():
    templates = frappe.get_all(
        "Item Tax Template",
        fields=["name", "title", "gst_rate"]
    )
    
    result = []
    for t in templates:
        result.append({
            "name": t.name,
            "title": t.title,
            "gst_rate": t.gst_rate or 0
        })
    
    return result

@frappe.whitelist()
def create_sales_return():
    from collections import defaultdict

    data = frappe.request.get_json()
    company = data.get("company") or frappe.db.get_single_value("Global Defaults", "default_company")

    def get_default_tax_template(company):
        return frappe.db.get_value(
            "Sales Taxes and Charges Template",
            {"company": company, "is_default": 1},
            "name"
        )

    sales_return = frappe.new_doc("Sales Invoice")
    sales_return.is_return = 1
    sales_return.posting_date = data.get("return_date") or frappe.utils.nowdate()
    sales_return.customer = data.get("customer")
    sales_return.company = company
    sales_return.custom_sales_person = data.get("sales_person")
    sales_return.custom_return_reason = data.get("return_reason")

    if data.get("return_against"):
        sales_return.return_against = data.get("return_against")
        orig_inv = frappe.get_doc("Sales Invoice", data.get("return_against"))

        if orig_inv.taxes_and_charges:
            sales_return.taxes_and_charges = orig_inv.taxes_and_charges
            for t in orig_inv.taxes:
                sales_return.append("taxes", {
                    "charge_type": t.charge_type,
                    "account_head": t.account_head,
                    "rate": t.rate,
                    "description": t.description
                })

        original_item_map = defaultdict(float)
        for it in orig_inv.items:
            original_item_map[it.item_code] += flt(it.qty)

        submitted_returns = frappe.get_all(
            "Sales Invoice",
            filters={
                "is_return": 1,
                "return_against": data.get("return_against"),
                "docstatus": 1
            },
            pluck="name"
        )
        returned_item_map = defaultdict(float)
        if submitted_returns:
            returned_rows = frappe.get_all(
                "Sales Invoice Item",
                filters={"parent": ["in", submitted_returns]},
                fields=["item_code", "qty"]
            )
            for r in returned_rows:
                returned_item_map[r["item_code"]] += abs(flt(r["qty"]))

    else:
        tax_template = get_default_tax_template(company)
        if tax_template:
            sales_return.taxes_and_charges = tax_template
            taxes = frappe.get_all(
                "Sales Taxes and Charges",
                filters={"parent": tax_template},
                fields=["charge_type", "account_head", "rate", "description"]
            )
            for t in taxes:
                sales_return.append("taxes", t)

    errors = []
    for item in data.get("items", []):
        qty = flt(item.get("qty"))
        item_code = item.get("item_code")

        if data.get("return_against"):
            sold_qty = original_item_map.get(item_code, 0.0)
            already_returned = returned_item_map.get(item_code, 0.0)
            remaining = sold_qty - already_returned
            if qty > remaining:
                errors.append(
                    f"Item {item_code}: requested return {qty} exceeds remaining {remaining} "
                    f"(sold {sold_qty} - already returned {already_returned})"
                )

        sales_return.append("items", {
            "item_code": item_code,
            "qty": -abs(qty),
            "rate": flt(item.get("rate")),
            "amount": -abs(qty) * flt(item.get("rate"))
        })

    if errors:
        return {"status": "error", "message": errors}

    sales_return.run_method("set_other_charges")
    sales_return.run_method("set_missing_values")
    sales_return.run_method("calculate_taxes_and_totals")
    sales_return.save(ignore_permissions=True)

    frappe.local.response["_server_messages"] = None
    frappe.clear_messages()

    return {                            
        "status": "success",
        "sales_return": sales_return.name,
        "tax_template": sales_return.taxes_and_charges
    }

@frappe.whitelist(allow_guest=True)
def update_chundakadan_settings(enable_stock_validation):
    try:
        if not frappe.has_permission("Chundakadan Settings", "write"):
            return {
                "status": "error",
                "message": "Not permitted to update settings",
                "http_status_code": 403
            }

        if isinstance(enable_stock_validation, str):
            enable_stock_validation = enable_stock_validation.lower() == 'true'
        doc = frappe.get_single("Chundakadan Settings")
        doc.db_set('enable_stock_validation', 1 if enable_stock_validation else 0)
        frappe.db.commit()

        return {
            "status": "success",
            "message": "Settings updated successfully",
            "data": {
                "enable_stock_validation": bool(doc.enable_stock_validation)
            },
            "http_status_code": 200
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Settings Update Error")

@frappe.whitelist(allow_guest=True)
def get_chundakadan_settings():
    try:
        if not frappe.has_permission("Chundakadan Settings", "read"):
            return {
                "status": "error",
                "message": "Not permitted to read settings",
                "http_status_code": 403
            }

        doc = frappe.get_single("Chundakadan Settings")
        
        return {
            "status": "success",
            "message": "Settings retrieved successfully",
            "data": {
                "enable_stock_validation": bool(doc.enable_stock_validation)
            },
            "http_status_code": 200
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Settings Fetch Error")
        return {
            "status": "error",
            "message": str(e),
            "http_status_code": 500
        }

@frappe.whitelist(allow_guest=True)
def get_task_details():
    try:
        sa = frappe.form_dict.get("sales_person")
        if not sa :
            return{
                "status":"error",
                "message":"sales person isrequired",
                "code":400
            }
        docs = frappe.get_all(
            "Task",
            fields=[
                'name', 'subject', 'status',
                'custom_customer', 'custom_assigned_to',
                'exp_start_date', 'exp_end_date', 'description',"custom_remarks"
            ],
            filters={"custom_assigned_to":sa}
        )

        for d in docs:
            if d.get("description"):
                soup = BeautifulSoup(d["description"], "html.parser")
                d["description"] = soup.get_text()

        return {
            "status": "success",
            "message": "task details retrieved",
            "data": docs,
            "code": 200
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Task Fetch Error")
        return {
            "status": "error",
            "message": str(e),
            "http_status_code": 500
        }

@frappe.whitelist(allow_guest=True)
def update_status():
    try:
        data = frappe.request.get_json()
        task_name = data.get("task_name")
        new_status = data.get("status")
        completion_date = data.get("completion_date")

        if not task_name or not new_status:
            return {
                "status": "error",
                "message": "Task name and status are required",
                "code": 400
            }

        if new_status == "Completed":
            if not completion_date:
                return {
                    "status": "error",
                    "message": "Completion date is required when status is Completed",
                    "code": 400
                }

        task = frappe.get_doc("Task", task_name)
        task.status = new_status

        if new_status == "Completed" and completion_date:
            task.completed_on = completion_date

        task.save(ignore_permissions=True)
        frappe.db.commit()

        return {
            "status": "success",
            "message": f"Task {task_name} updated to {new_status}",
            "code": 200
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Task Status Update Error")
        return {
            "status": "error",
            "message": str(e),
            "code": 500
        }

@frappe.whitelist(allow_guest=True)
def add_remarks():
    try:
        data=frappe.request.get_json()
        remarks=data.get("remarks")
        task_name=data.get("task_name")
        task=frappe.get_doc("Task",task_name)
        task.custom_remarks=remarks
        task.save(ignore_permissions=True)  
        frappe.db.commit()
        return{
            "satatus":"success",
            "message":f"remarks {remarks}added to  Task {task_name} ",
            "code":200
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "remarks add  Error")
        return {
            "status": "error",
            "message": str(e),
            "code": 500
        }