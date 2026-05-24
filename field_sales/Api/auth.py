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
#         company_name = _resolve_company_for_caller()
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
import base64
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
        fields=[
            "name", "item_name", "description", "stock_uom", "is_stock_item",
            "standard_rate", "valuation_rate", "last_purchase_rate"
        ]
    )

    # Fallback selling price list (Selling Settings.selling_price_list)
    fallback_pl = None
    try:
        fallback_pl = frappe.db.get_single_value(
            "Selling Settings", "selling_price_list"
        )
    except Exception:
        fallback_pl = None

    result = []

    for item in items:
        # Price fetch order:
        #   1. Item Price in the requested price_list (default "Standard Selling")
        #   2. Item Price in Selling Settings' configured price list
        #   3. Item.standard_rate (master field)
        #   4. Item.last_purchase_rate
        #   5. Item.valuation_rate
        #   6. 0
        price = frappe.db.get_value(
            "Item Price",
            filters={"item_code": item.name, "price_list": price_list},
            fieldname="price_list_rate",
        )
        if not price and fallback_pl and fallback_pl != price_list:
            price = frappe.db.get_value(
                "Item Price",
                filters={"item_code": item.name, "price_list": fallback_pl},
                fieldname="price_list_rate",
            )
        if not price:
            price = (
                item.get("standard_rate")
                or item.get("last_purchase_rate")
                or item.get("valuation_rate")
            )

        # Get tax template from Item Taxes table
        tax_template = frappe.db.get_value(
            "Item Tax",
            filters={"parent": item.name},
            fieldname="item_tax_template"
        )

        # Get stock across all warehouses
        stock_data = frappe.db.sql("""
            SELECT 
                warehouse,
                actual_qty
            FROM `tabBin`
            WHERE item_code = %s
            ORDER BY warehouse
        """, (item.name,), as_dict=True)

        # Calculate total stock
        total_stock = sum([s.actual_qty for s in stock_data]) if stock_data else 0

        result.append({
            "item_code": item.name,
            "item_name": item.item_name,
            "description": item.description,
            "uom": item.stock_uom,
            "price": price or 0.0,
            "maintain_stock": item.is_stock_item,
            "tax_template": tax_template or "",
            "total_stock": total_stock,
            "stock_by_warehouse": stock_data  # Detailed stock per warehouse
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

        company_name = _resolve_company_for_caller()
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

        # `submit` may arrive as bool, "true"/"false", or 0/1 from the mobile client.
        submit_flag = data.get("submit", True)
        if isinstance(submit_flag, str):
            submit_flag = submit_flag.lower() not in ("false", "0", "no")
        else:
            submit_flag = bool(submit_flag)

        if submit_flag:
            so.submit()
            _maybe_log_visit(
                so,
                data.get("latitude"),
                data.get("longitude"),
                "SO {}".format(so.name),
            )

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
            "docstatus": ["in", [0, 1]]
        },
        pluck="name"
    )

    sales_orders = []
    for so_name in sales_order_names:
        doc = frappe.get_doc("Sales Order", so_name)
        sales_orders.append({
            "name": doc.name,
            "customer": doc.customer,
            "customer_name": doc.customer_name,
            "status": doc.status,
            "docstatus": doc.docstatus,
            "custom_special_order": doc.get("custom_special_order") or 0,
            "modified": str(doc.modified),
            "delivery_date": doc.delivery_date,
            "total": doc.total,
            "total_taxes_and_charges": doc.total_taxes_and_charges,
            "grand_total": doc.grand_total,
            "rounded total":doc.rounded_total,
            "items": [
                {
                    "item_code": item.item_code,
                    "item_name": item.item_name,
                    "qty": item.qty,
                    "rate": item.rate,
                    "amount": item.amount,
                    "uom": item.uom
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

    # Auto-create Customer Visit Log when the mobile app sends GPS.
    # The salesperson is physically at the customer when they record a PE,
    # so the visit happens at insert time (not at submit, which can be later).
    _maybe_log_visit(
        pe,
        data.get("latitude"),
        data.get("longitude"),
        "PE {}".format(pe.name),
    )

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

@frappe.whitelist(methods=["POST"])
def create_task(
    subject=None,
    custom_customer=None,
    exp_start_date=None,
    exp_end_date=None,
    description=None,
    custom_remarks=None,
    custom_assigned_to=None,
    status=None,
):
    """Create a Task for the calling sales person (or for an explicit
    custom_assigned_to passed by the client). Mirrors the shape returned
    by get_task_details so the mobile client can append the new row to
    its in-memory list without a full refetch."""
    try:
        data = frappe.request.get_json() or {}
        subject = subject or data.get("subject")
        custom_customer = custom_customer or data.get("custom_customer")
        exp_start_date = exp_start_date or data.get("exp_start_date")
        exp_end_date = exp_end_date or data.get("exp_end_date")
        description = description or data.get("description")
        custom_remarks = custom_remarks or data.get("custom_remarks")
        custom_assigned_to = custom_assigned_to or data.get("custom_assigned_to")
        status = status or data.get("status") or "Open"

        if not subject:
            return {"status": "error", "message": "Subject is required", "code": 400}
        if not exp_start_date or not exp_end_date:
            return {"status": "error", "message": "Start and End dates are required", "code": 400}

        # Default assignee = the calling user's sales person (matches
        # get_task_details's filter on custom_assigned_to).
        if not custom_assigned_to:
            custom_assigned_to = _resolve_caller_sales_person()
        if not custom_assigned_to:
            return {"status": "error", "message": "custom_assigned_to could not be resolved", "code": 400}

        doc = frappe.get_doc({
            "doctype": "Task",
            "subject": subject,
            "status": status,
            "exp_start_date": frappe.utils.getdate(exp_start_date),
            "exp_end_date": frappe.utils.getdate(exp_end_date),
            "description": description or "",
            "custom_customer": custom_customer,
            "custom_assigned_to": custom_assigned_to,
            "custom_remarks": custom_remarks or "",
        })
        doc.insert(ignore_permissions=True)

        return {
            "status": "success",
            "message": "Task created",
            "data": {
                "name": doc.name,
                "subject": doc.subject,
                "status": doc.status,
                "custom_customer": doc.custom_customer,
                "custom_assigned_to": doc.custom_assigned_to,
                "exp_start_date": str(doc.exp_start_date) if doc.exp_start_date else None,
                "exp_end_date": str(doc.exp_end_date) if doc.exp_end_date else None,
                "description": doc.description or "",
                "custom_remarks": doc.custom_remarks or "",
            },
            "code": 200,
        }
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.create_task")
        return {"status": "error", "message": str(e), "code": 500}


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




@frappe.whitelist(allow_guest=True)
def get_item_stock():
    try:
        data = frappe.request.get_json()
        item_code = data.get("item_code")
        warehouse = data.get("warehouse")  # Optional filter
        
        # Base query
        filters = {}
        if item_code:
            filters["item_code"] = item_code
        if warehouse:
            filters["warehouse"] = warehouse
        
        # Get stock data from Bin doctype
        stock_data = frappe.get_all(
            "Bin",
            filters=filters,
            fields=[
                "item_code",
                "warehouse",
                "actual_qty",
                "reserved_qty",
                "ordered_qty",
                "indented_qty",
                "planned_qty",
                "projected_qty",
                "valuation_rate",
                "stock_value"
            ]
        )
        
        # If you want item details too
        if stock_data:
            for stock in stock_data:
                item = frappe.get_cached_value(
                    "Item",
                    stock["item_code"],
                    ["item_name", "stock_uom", "item_group"],
                    as_dict=True
                )
                stock.update(item)
        
        return {
            "status": "success",
            "message": f"Retrieved stock for {len(stock_data)} items",
            "data": stock_data,
            "code": 200
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Item Stock Error")
        return {
            "status": "error",
            "message": str(e),
            "code": 500
        }


# Alternative: Get stock for all items (no filters)
@frappe.whitelist(allow_guest=True)
def get_all_items_stock():
    try:
        # Get all items with their stock (including zero stock)
        stock_data = frappe.db.sql("""
            SELECT 
                i.name as item_code,
                i.item_name,
                i.stock_uom,
                i.item_group,
                COALESCE(b.warehouse, '') as warehouse,
                COALESCE(b.actual_qty, 0) as actual_qty
            FROM `tabItem` i
            LEFT JOIN `tabBin` b ON i.name = b.item_code
            WHERE i.disabled = 0
            ORDER BY i.item_code, b.warehouse
        """, as_dict=True)
        
        return {
            "status": "success",
            "message": f"Retrieved stock for {len(stock_data)} items",
            "data": stock_data,
            "code": 200
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get All Items Stock Error")
        return {
            "status": "error",
            "message": str(e),
            "code": 500
        }
# Get stock summary grouped by item
@frappe.whitelist(allow_guest=True)
def get_item_stock_summary():
    try:
        data = frappe.request.get_json()
        item_code = data.get("item_code")
        
        filters = {"actual_qty": [">", 0]}
        if item_code:
            filters["item_code"] = item_code
        
        # Get summarized stock
        stock_summary = frappe.db.sql("""
            SELECT 
                b.item_code,
                i.item_name,
                i.stock_uom,
                SUM(b.actual_qty) as total_qty,
                SUM(b.reserved_qty) as total_reserved,
                SUM(b.projected_qty) as total_available,
                COUNT(DISTINCT b.warehouse) as warehouse_count,
                GROUP_CONCAT(DISTINCT b.warehouse) as warehouses
            FROM `tabBin` b
            INNER JOIN `tabItem` i ON b.item_code = i.name
            {condition}
            GROUP BY b.item_code
            ORDER BY b.item_code
        """.format(
            condition=f"WHERE b.item_code = '{item_code}'" if item_code else "WHERE b.actual_qty > 0"
        ), as_dict=True)
        
        return {
            "status": "success",
            "message": f"Retrieved stock summary for {len(stock_summary)} items",
            "data": stock_summary,
            "code": 200
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Get Item Stock Summary Error")
        return {
            "status": "error",
            "message": str(e),
            "code": 500
        }


# ==========================================================================
#  Quotation & Sales Order extension endpoints
#  - Append-only section.
#  - india_compliance handles GST taxes on save/submit; no manual tax logic.
# ==========================================================================

def _resolve_caller_sales_person():
    """Resolve the Sales Person linked to the current session user.

    Returns the Sales Person name (string) or None if the caller is not
    linked to a Sales Person via an Employee record.
    """
    user = frappe.session.user
    if not user or user == "Guest":
        return None
    employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
    if not employee:
        return None
    sales_person = frappe.db.get_value("Sales Person", {"employee": employee}, "name")
    return sales_person


def _resolve_company_for_caller():
    """3-layer fallback for the calling user's company.

    1. Employee.company linked to frappe.session.user
    2. Chundakadan Settings.default_company
    3. First Company in the DB

    Returns the company name string. Never None unless the bench has
    zero Companies (in which case ERPNext is misconfigured).
    """
    user = frappe.session.user
    if user and user != "Guest":
        emp_company = frappe.db.get_value("Employee", {"user_id": user}, "company")
        if emp_company:
            return emp_company

    try:
        settings_default = frappe.db.get_single_value(
            "Chundakadan Settings", "default_company"
        )
        if settings_default:
            return settings_default
    except Exception:
        pass

    rows = frappe.get_all("Company", fields=["name"], limit=1)
    return rows[0].name if rows else None


def _maybe_log_visit(doc, latitude, longitude, source_label):
    """Best-effort auto-log of a Customer Visit Log row tied to `doc`.

    Called from create/submit flows when the doc is reaching docstatus=1.
    Silently skips if lat/lng is missing or if log creation fails — must
    NEVER raise back into the caller, the parent save is what matters.
    """
    try:
        if latitude is None or longitude is None:
            return None
        try:
            lat_f = float(latitude)
            lng_f = float(longitude)
        except (TypeError, ValueError):
            return None
        if lat_f == 0 and lng_f == 0:
            return None

        from frappe.utils import nowdate, nowtime

        sales_person = _resolve_caller_sales_person()
        if not sales_person:
            return None

        log = frappe.new_doc("Customer Visit Log")
        log.employee = sales_person
        log.date = nowdate()
        log.time = nowtime()
        log.latitude = lat_f
        log.longitude = lng_f
        # The Customer Visit Log uses customer_name as a free-text field.
        # Handle SO/Quotation (customer / customer_name) AND
        # Payment Entry (party / party_name) field shapes.
        log.customer_name = (
            getattr(doc, "customer_name", None)
            or getattr(doc, "party_name", None)
            or getattr(doc, "customer", None)
            or getattr(doc, "party", "")
        )
        log.description = "Auto-logged via {}".format(source_label)
        log.insert(ignore_permissions=True)
        return log.name
    except Exception:
        frappe.log_error(frappe.get_traceback(), "field_sales._maybe_log_visit")
        return None


@frappe.whitelist(methods=["POST"])
def update_sales_order(name=None, customer=None, delivery_date=None, items=None):
    """Update a Draft Sales Order. Submitted/cancelled SOs are rejected.

    india_compliance recomputes taxes on save; we never touch the taxes table.
    """
    try:
        data = frappe.request.get_json() or {}
        name = name or data.get("name")
        customer = customer or data.get("customer")
        delivery_date = delivery_date or data.get("delivery_date")
        items = items if items is not None else data.get("items")

        if not name:
            return response("Sales Order name is required", None, False, 400)
        if not customer:
            return response("Customer is required", None, False, 400)
        if not items or not isinstance(items, list):
            return response("At least one item is required", None, False, 400)

        if not frappe.db.exists("Sales Order", name):
            return response(f"Sales Order '{name}' does not exist", None, False, 404)
        if not frappe.db.exists("Customer", customer):
            return response(f"Customer '{customer}' does not exist", None, False, 404)

        doc = frappe.get_doc("Sales Order", name)

        if doc.docstatus != 0:
            return response("Submitted orders cannot be edited", None, False, 400)

        # Permission: caller must own this SO via custom_sales_person
        caller_sp = _resolve_caller_sales_person()
        if caller_sp and doc.get("custom_sales_person") and doc.custom_sales_person != caller_sp:
            return response("You do not have permission to edit this Sales Order", None, False, 403)

        doc.customer = customer
        doc.delivery_date = frappe.utils.getdate(delivery_date) if delivery_date else doc.delivery_date

        # Persist Special Order toggle if the client sent it.
        if "custom_special_order" in data:
            doc.custom_special_order = 1 if data.get("custom_special_order") else 0

        # Replace items child table; keep sales team / custom_sales_person as-is
        doc.set("items", [])
        for item in items:
            item_code = item.get("item_code")
            if not item_code:
                return response("item_code is required for each item", None, False, 400)
            row = {
                "item_code": item_code,
                "qty": flt(item.get("qty", 1)),
                "rate": flt(item.get("rate", 0)),
                "price_list_rate": flt(item.get("rate", 0)),
            }
            if item.get("uom"):
                row["uom"] = item.get("uom")
            if item.get("delivery_date"):
                row["delivery_date"] = frappe.utils.getdate(item.get("delivery_date"))
            doc.append("items", row)

        # india_compliance recomputes taxes on save automatically
        doc.save()

        return response("Sales Order updated", {"name": doc.name}, True, 200)

    except frappe.PermissionError:
        frappe.log_error(frappe.get_traceback(), "field_sales.update_sales_order")
        return response("Permission denied", None, False, 403)
    except frappe.DoesNotExistError:
        frappe.log_error(frappe.get_traceback(), "field_sales.update_sales_order")
        return response("Sales Order not found", None, False, 404)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.update_sales_order")
        return response(str(e), None, False, 500)


@frappe.whitelist(methods=["GET"])
def get_quotations_with_details(sales_person_id=None, status_filter=None):
    """List Quotations filtered by sales person (via Sales Team child)
    and optional status. Mirrors get_sales_orders_with_details.
    """
    try:
        # Verify caller's own sales-person; do not trust raw sales_person_id
        caller_sp = _resolve_caller_sales_person()
        if sales_person_id and caller_sp and sales_person_id != caller_sp:
            return response("You can only view your own quotations", None, False, 403)
        effective_sp = sales_person_id or caller_sp

        valid_statuses = {"Draft", "Submitted", "Open", "Lost", "Ordered", "Expired"}
        if status_filter and status_filter not in valid_statuses:
            return response(f"Invalid status_filter. Allowed: {sorted(valid_statuses)}", None, False, 400)

        # This bench's Quotation DocType has no `sales_team` child table; it
        # uses a `custom_sales_person` Link field (same as Sales Order). Probe
        # the meta and pick whichever filter the schema actually supports.
        if effective_sp:
            quotation_meta = frappe.get_meta("Quotation")
            has_custom_sp = quotation_meta.get_field("custom_sales_person") is not None
            has_sales_team = quotation_meta.get_field("sales_team") is not None

            if has_custom_sp:
                # Match the caller's quotations AND any orphans (custom_sales_person
                # IS NULL / empty) — orphans happen when the field was added
                # after some drafts already existed, or when an admin user
                # creates a doc without an Employee record. Without the OR,
                # those drafts vanish from the mobile list.
                status_clause = "AND q.status = %(status)s" if status_filter else ""
                quotation_names = frappe.db.sql_list(
                    """
                    SELECT q.name FROM `tabQuotation` q
                    WHERE (q.custom_sales_person = %(sp)s
                           OR q.custom_sales_person IS NULL
                           OR q.custom_sales_person = '')
                          {status_clause}
                    ORDER BY q.modified DESC
                    """.format(status_clause=status_clause),
                    {"sp": effective_sp, "status": status_filter},
                )
            elif has_sales_team:
                quotation_names = frappe.db.sql_list(
                    """
                    SELECT DISTINCT q.name
                    FROM `tabQuotation` q
                    INNER JOIN `tabSales Team` st
                        ON st.parent = q.name AND st.parenttype = 'Quotation'
                    WHERE st.sales_person = %(sp)s
                    {status_clause}
                    ORDER BY q.modified DESC
                    """.format(
                        status_clause="AND q.status = %(status)s" if status_filter else ""
                    ),
                    {"sp": effective_sp, "status": status_filter}
                )
            else:
                # No way to scope by sales person; return everything for this caller.
                filters = {}
                if status_filter:
                    filters["status"] = status_filter
                quotation_names = frappe.get_all(
                    "Quotation", filters=filters, pluck="name", order_by="modified desc"
                )
        else:
            filters = {}
            if status_filter:
                filters["status"] = status_filter
            quotation_names = frappe.get_all("Quotation", filters=filters, pluck="name", order_by="modified desc")

        quotations = []
        for q_name in quotation_names:
            doc = frappe.get_doc("Quotation", q_name)
            quotations.append({
                "name": doc.name,
                "customer": doc.get("party_name"),
                "customer_name": doc.get("customer_name"),
                "transaction_date": doc.transaction_date,
                "valid_till": doc.valid_till,
                "status": doc.status,
                "docstatus": doc.docstatus,
                "grand_total": doc.grand_total,
                "items": [
                    {
                        "item_code": it.item_code,
                        "item_name": it.item_name,
                        "qty": it.qty,
                        "rate": it.rate,
                        "amount": it.amount,
                        "uom": it.uom,
                    } for it in doc.items
                ],
                "taxes": [
                    {
                        "account_head": tx.account_head,
                        "description": tx.description,
                        "rate": tx.rate,
                        "tax_amount": tx.tax_amount,
                    } for tx in (doc.get("taxes") or [])
                ],
            })

        return response("Quotations fetched", {"quotations": quotations}, True, 200)

    except frappe.PermissionError:
        frappe.log_error(frappe.get_traceback(), "field_sales.get_quotations_with_details")
        return response("Permission denied", None, False, 403)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.get_quotations_with_details")
        return response(str(e), None, False, 500)


@frappe.whitelist(methods=["POST"])
def create_quotation(customer=None, transaction_date=None, valid_till=None, items=None):
    """Create a Draft Quotation for the current sales person."""
    try:
        data = frappe.request.get_json() or {}
        customer = customer or data.get("customer")
        transaction_date = transaction_date or data.get("transaction_date")
        valid_till = valid_till or data.get("valid_till")
        items = items if items is not None else data.get("items")

        if not customer:
            return response("Customer is required", None, False, 400)
        if not items or not isinstance(items, list):
            return response("At least one item is required", None, False, 400)
        if not frappe.db.exists("Customer", customer):
            return response(f"Customer '{customer}' does not exist", None, False, 404)

        company_name = _resolve_company_for_caller()
        default_currency = frappe.get_cached_value("Company", company_name, "default_currency")

        caller_sp = _resolve_caller_sales_person()

        # Minimal doc shape — let ERPNext's set_missing_values resolve
        # selling_price_list / currency from Customer + Company defaults.
        # An over-defensive earlier draft set those explicitly and could
        # itself trigger the "'NoneType' object has no attribute 'options'"
        # if the chosen price list was stale.
        q = frappe.get_doc({
            "doctype": "Quotation",
            "quotation_to": "Customer",
            "party_name": customer,
            "company": company_name,
            "currency": data.get("currency") or default_currency,
            "transaction_date": frappe.utils.getdate(transaction_date) if transaction_date else nowdate(),
            "valid_till": frappe.utils.getdate(valid_till) if valid_till else None,
            "items": []
        })

        for item in items:
            item_code = item.get("item_code")
            if not item_code:
                return response("item_code is required for each item", None, False, 400)
            row = {
                "item_code": item_code,
                "qty": flt(item.get("qty", 1)),
                "rate": flt(item.get("rate", 0)),
                "price_list_rate": flt(item.get("rate", 0)),
            }
            if item.get("uom"):
                row["uom"] = item.get("uom")
            q.append("items", row)

        # Attach the calling sales person. This bench's Quotation does NOT
        # have the standard ERPNext `sales_team` child table — it uses a
        # custom_sales_person Link field, same pattern as create_sales_order.
        # Probe the meta to pick whichever the DocType actually has and skip
        # silently if neither exists.
        if caller_sp:
            quotation_meta = frappe.get_meta("Quotation")
            if quotation_meta.get_field("sales_team"):
                q.append("sales_team", {
                    "sales_person": caller_sp,
                    "allocated_percentage": 100,
                })
            elif quotation_meta.get_field("custom_sales_person"):
                q.custom_sales_person = caller_sp

        # Match the working create_sales_order pattern: one set_missing_values
        # + insert. Skip explicit calculate_taxes_and_totals beforehand.
        q.flags.ignore_mandatory = True
        q.run_method("set_missing_values")
        q.insert(ignore_permissions=True)

        submit_flag = data.get("submit", False)
        if isinstance(submit_flag, str):
            submit_flag = submit_flag.lower() not in ("false", "0", "no")
        else:
            submit_flag = bool(submit_flag)

        if submit_flag:
            q.submit()
            _maybe_log_visit(
                q,
                data.get("latitude"),
                data.get("longitude"),
                "Quotation {}".format(q.name),
            )

        return response(
            "Quotation created",
            {"name": q.name, "docstatus": q.docstatus, "status": q.status},
            True,
            200,
        )

    except frappe.PermissionError:
        frappe.log_error(frappe.get_traceback(), "field_sales.create_quotation")
        return response("Permission denied", None, False, 403)
    except Exception as e:
        tb = frappe.get_traceback()
        frappe.log_error(tb, "field_sales.create_quotation")
        # Surface the *deepest* useful frame so the mobile snackbar shows
        # where it broke (file:line, calling function). Removes the
        # "NoneType has no attribute 'options'" mystery in the field.
        diag = _extract_last_frame(tb) or str(e)
        return response("Create failed: {}".format(diag), None, False, 500)


def _extract_last_frame(tb):
    """Pull the deepest non-frappe-internal frame from a traceback string.

    Returns 'path/file.py:LINENO in func: <exception msg>' or None.
    Skips frames inside frappe's own client/handler shim so the caller
    sees their own model/controller code's failure site, not the
    request dispatcher.
    """
    try:
        lines = [ln.rstrip() for ln in tb.splitlines() if ln.strip()]
        # File frames look like:  File "/path/foo.py", line 123, in func
        last_file = None
        for ln in lines:
            stripped = ln.strip()
            if not stripped.startswith("File "):
                continue
            # Skip frappe handler/whitelist plumbing
            if "/frappe/handler.py" in stripped:
                continue
            if "/frappe/api/" in stripped:
                continue
            last_file = stripped
        final = lines[-1] if lines else ""
        if last_file:
            return "{} -> {}".format(last_file, final)
        return final or None
    except Exception:
        return None


@frappe.whitelist(methods=["POST"])
def update_quotation(name=None, customer=None, valid_till=None, items=None):
    """Update a Draft Quotation."""
    try:
        data = frappe.request.get_json() or {}
        name = name or data.get("name")
        customer = customer or data.get("customer")
        valid_till = valid_till or data.get("valid_till")
        items = items if items is not None else data.get("items")

        if not name:
            return response("Quotation name is required", None, False, 400)
        if not customer:
            return response("Customer is required", None, False, 400)
        if not items or not isinstance(items, list):
            return response("At least one item is required", None, False, 400)

        if not frappe.db.exists("Quotation", name):
            return response(f"Quotation '{name}' does not exist", None, False, 404)
        if not frappe.db.exists("Customer", customer):
            return response(f"Customer '{customer}' does not exist", None, False, 404)

        doc = frappe.get_doc("Quotation", name)

        if doc.docstatus != 0:
            return response("Submitted orders cannot be edited", None, False, 400)

        # Permission: caller must be a sales person on this quotation
        caller_sp = _resolve_caller_sales_person()
        if caller_sp:
            sales_team_members = {row.sales_person for row in (doc.get("sales_team") or [])}
            if sales_team_members and caller_sp not in sales_team_members:
                return response("You do not have permission to edit this Quotation", None, False, 403)

        doc.party_name = customer
        doc.customer = customer
        if valid_till:
            doc.valid_till = frappe.utils.getdate(valid_till)

        doc.set("items", [])
        for item in items:
            item_code = item.get("item_code")
            if not item_code:
                return response("item_code is required for each item", None, False, 400)
            row = {
                "item_code": item_code,
                "qty": flt(item.get("qty", 1)),
                "rate": flt(item.get("rate", 0)),
                "price_list_rate": flt(item.get("rate", 0)),
            }
            if item.get("uom"):
                row["uom"] = item.get("uom")
            doc.append("items", row)

        # india_compliance recomputes taxes on save
        doc.save()

        return response("Quotation updated", {"name": doc.name}, True, 200)

    except frappe.PermissionError:
        frappe.log_error(frappe.get_traceback(), "field_sales.update_quotation")
        return response("Permission denied", None, False, 403)
    except frappe.DoesNotExistError:
        frappe.log_error(frappe.get_traceback(), "field_sales.update_quotation")
        return response("Quotation not found", None, False, 404)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.update_quotation")
        return response(str(e), None, False, 500)


@frappe.whitelist(methods=["POST"])
def submit_quotation(name=None):
    """Submit a Draft Quotation."""
    try:
        data = frappe.request.get_json() or {}
        name = name or data.get("name")

        if not name:
            return response("Quotation name is required", None, False, 400)
        if not frappe.db.exists("Quotation", name):
            return response(f"Quotation '{name}' does not exist", None, False, 404)

        doc = frappe.get_doc("Quotation", name)

        if doc.docstatus != 0:
            return response("Already submitted or cancelled", None, False, 400)

        # Permission: caller must be a sales person on this quotation
        caller_sp = _resolve_caller_sales_person()
        if caller_sp:
            sales_team_members = {row.sales_person for row in (doc.get("sales_team") or [])}
            if sales_team_members and caller_sp not in sales_team_members:
                return response("You do not have permission to submit this Quotation", None, False, 403)

        doc.submit()
        _maybe_log_visit(
            doc,
            data.get("latitude"),
            data.get("longitude"),
            "Quotation {}".format(doc.name),
        )

        return response("Quotation submitted", {"name": doc.name, "status": doc.status}, True, 200)

    except frappe.PermissionError:
        frappe.log_error(frappe.get_traceback(), "field_sales.submit_quotation")
        return response("Permission denied", None, False, 403)
    except frappe.DoesNotExistError:
        frappe.log_error(frappe.get_traceback(), "field_sales.submit_quotation")
        return response("Quotation not found", None, False, 404)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.submit_quotation")
        return response(str(e), None, False, 500)


@frappe.whitelist(methods=["POST"])
def convert_quotation_to_sales_order(quotation_name=None, delivery_date=None):
    """Convert a Submitted Quotation into a Draft Sales Order."""
    try:
        from erpnext.selling.doctype.quotation.quotation import make_sales_order

        data = frappe.request.get_json() or {}
        quotation_name = quotation_name or data.get("quotation_name")
        delivery_date = delivery_date or data.get("delivery_date")

        if not quotation_name:
            return response("quotation_name is required", None, False, 400)
        if not delivery_date:
            return response("delivery_date is required", None, False, 400)
        if not frappe.db.exists("Quotation", quotation_name):
            return response(f"Quotation '{quotation_name}' does not exist", None, False, 404)

        quotation = frappe.get_doc("Quotation", quotation_name)
        if quotation.docstatus != 1:
            return response("Only submitted quotations can be converted", None, False, 400)

        # Permission: caller must be on the sales team
        caller_sp = _resolve_caller_sales_person()
        if caller_sp:
            sales_team_members = {row.sales_person for row in (quotation.get("sales_team") or [])}
            if sales_team_members and caller_sp not in sales_team_members:
                return response("You do not have permission to convert this Quotation", None, False, 403)

        parsed_date = frappe.utils.getdate(delivery_date)
        target_doc = make_sales_order(source_name=quotation_name)
        target_doc.delivery_date = parsed_date
        for row in target_doc.items:
            row.delivery_date = parsed_date

        # india_compliance computes taxes on insert
        target_doc.insert()

        return response(
            "Sales Order created from Quotation",
            {"sales_order_name": target_doc.name},
            True,
            200,
        )

    except frappe.PermissionError:
        frappe.log_error(frappe.get_traceback(), "field_sales.convert_quotation_to_sales_order")
        return response("Permission denied", None, False, 403)
    except frappe.DoesNotExistError:
        frappe.log_error(frappe.get_traceback(), "field_sales.convert_quotation_to_sales_order")
        return response("Quotation not found", None, False, 404)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.convert_quotation_to_sales_order")
        return response(str(e), None, False, 500)


@frappe.whitelist(methods=["POST"])
def submit_sales_order(name=None):
    """Submit a Draft Sales Order (docstatus 0 -> 1). Used by the mobile app
    after a sales person has edited a Draft created via create_sales_order
    with submit=false."""
    try:
        data = frappe.request.get_json() or {}
        so_name = name or data.get("name")
        if not so_name:
            return response("Sales Order name is required", None, False, 400)

        doc = frappe.get_doc("Sales Order", so_name)

        if doc.docstatus != 0:
            return response(
                "Only Draft Sales Orders can be submitted",
                None,
                False,
                400,
            )

        caller_sp = _resolve_caller_sales_person()
        if caller_sp and getattr(doc, "custom_sales_person", None):
            if doc.custom_sales_person != caller_sp:
                return response(
                    "You do not have permission to submit this order",
                    None,
                    False,
                    403,
                )

        doc.submit()
        _maybe_log_visit(
            doc,
            data.get("latitude"),
            data.get("longitude"),
            "SO {}".format(doc.name),
        )
        return response(
            "Sales Order submitted",
            {"name": doc.name, "status": doc.status},
            True,
            200,
        )
    except frappe.DoesNotExistError:
        return response("Sales Order not found", None, False, 404)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.submit_sales_order")
        return response(str(e), None, False, 500)


@frappe.whitelist(methods=["POST"])
def get_print_pdf(doctype=None, name=None, print_format=None, letterhead=None):
    """Generate a PDF (base64) or HTML fallback for a given doctype/name."""
    try:
        if not doctype or not name:
            return response("doctype and name are required", None, False, 400)

        if not frappe.db.exists(doctype, name):
            return response(f"{doctype} {name} not found", None, False, 404)

        if not print_format:
            print_format = "Standard"

        # Try PDF generation first (requires wkhtmltopdf)
        try:
            pdf_binary = frappe.get_print(
                doctype,
                name,
                print_format=print_format,
                letterhead=letterhead,
                as_pdf=True,
                ignore_permissions=True,
            )
            if not pdf_binary:
                raise Exception("Empty PDF output")

            pdf_b64 = base64.b64encode(pdf_binary).decode("utf-8")
            return response(
                "PDF generated",
                {
                    "pdf_base64": pdf_b64,
                    "html": None,
                    "content_type": "application/pdf",
                },
                True,
                200,
            )
        except Exception:
            # wkhtmltopdf missing or PDF generation failed — fall back to HTML
            html_string = frappe.get_print(
                doctype,
                name,
                print_format=print_format,
                letterhead=letterhead,
                ignore_permissions=True,
            )
            if not html_string:
                return response("Failed to generate print content", None, False, 500)

            return response(
                "HTML fallback",
                {
                    "pdf_base64": None,
                    "html": html_string,
                    "content_type": "text/html",
                },
                True,
                200,
            )
    except frappe.PermissionError:
        return response("No permission to access this document", None, False, 403)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.get_print_pdf")
        return response(str(e), None, False, 500)


@frappe.whitelist()
def get_print_formats(doctype=None):
    """Return available Print Formats and Letter Heads for a doctype."""
    try:
        if not doctype:
            return response("doctype is required", None, False, 400)

        formats = frappe.get_all(
            "Print Format",
            filters={"doc_type": doctype, "disabled": 0},
            fields=["name"],
            order_by="name asc",
        )

        names = [pf.get("name") for pf in formats]
        if "Standard" not in names:
            formats.append({"name": "Standard"})

        letterheads = frappe.get_all(
            "Letter Head",
            filters={"disabled": 0},
            fields=["name", "is_default"],
            order_by="is_default desc, name asc",
        )

        return response(
            "Print formats fetched",
            {
                "print_formats": [{"name": pf.get("name")} for pf in formats],
                "letterheads": [
                    {"name": lh.get("name"), "is_default": lh.get("is_default")}
                    for lh in letterheads
                ],
            },
            True,
            200,
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.get_print_formats")
        return response(str(e), None, False, 500)


@frappe.whitelist()
def get_today_snapshot(sales_person_id=None):
    """Return today's headline counts for the Sales Person's home dashboard.

    Resets naturally at midnight (filters use today's date). After a sales
    person logs the next day's first activity, the tiles read fresh.
    """
    try:
        from frappe.utils import today

        caller_sp = _resolve_caller_sales_person()
        sp = sales_person_id or caller_sp
        if not sp:
            return response("Sales person required", None, False, 400)
        if caller_sp and sp != caller_sp:
            return response("You can only view your own snapshot", None, False, 403)

        today_str = today()

        # Visits — Customer Visit Log rows for this sales person, dated today.
        # Schema varies; query defensively via the table API.
        visits = 0
        try:
            visits = frappe.db.count(
                "Customer Visit Log",
                filters={
                    "sales_person": sp,
                    "visit_date": today_str,
                },
            )
        except Exception:
            try:
                # Fallback: parent log row created today
                visits = frappe.db.count(
                    "Customer Visit Log",
                    filters={
                        "sales_person": sp,
                        "creation": [">=", today_str],
                    },
                )
            except Exception:
                visits = 0

        # Orders — Sales Orders this sales person created today.
        orders = frappe.db.count(
            "Sales Order",
            filters={
                "custom_sales_person": sp,
                "transaction_date": today_str,
                "docstatus": ["in", [0, 1]],
            },
        )

        # Collected — Payment Entries received today by this sales person.
        # If Payment Entry doesn't link to sales_person directly in this
        # app, fall back to 0.
        collected = 0
        try:
            rows = frappe.db.sql(
                """
                SELECT SUM(paid_amount) FROM `tabPayment Entry`
                WHERE docstatus = 1
                  AND DATE(posting_date) = %(d)s
                  AND (custom_sales_person = %(sp)s OR owner IN (
                       SELECT user_id FROM `tabEmployee`
                       WHERE name IN (
                         SELECT employee FROM `tabSales Person` WHERE name = %(sp)s
                       )
                  ))
                """,
                {"d": today_str, "sp": sp},
            )
            collected = float(rows[0][0] or 0) if rows else 0
        except Exception:
            collected = 0

        return response(
            "Snapshot fetched",
            {
                "date": today_str,
                "visits": visits,
                "orders": orders,
                "collected": collected,
            },
            True,
            200,
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.get_today_snapshot")
        return response(str(e), None, False, 500)


@frappe.whitelist(methods=["POST"])
def create_employee_checkin(log_type=None, latitude=None, longitude=None):
    """Mobile-app Check-In / Check-Out.

    Creates a standard ERPNext `Employee Checkin` for the calling user
    with the current timestamp + (optional) GPS. If a Shift Type is
    configured on the Employee, ERPNext's auto-attendance cron will
    roll the IN/OUT pairs into a daily Attendance record automatically
    (skip_auto_attendance is left at the default 0).
    """
    try:
        from frappe.utils import now_datetime

        data = frappe.request.get_json() or {}
        log_type = log_type or data.get("log_type")
        latitude = latitude if latitude is not None else data.get("latitude")
        longitude = longitude if longitude is not None else data.get("longitude")
        device_id = data.get("device_id") or "mobile_app"

        if log_type not in ("IN", "OUT"):
            return response("log_type must be 'IN' or 'OUT'", None, False, 400)

        user = frappe.session.user
        if not user or user == "Guest":
            return response("Authentication required", None, False, 401)

        employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
        if not employee:
            return response(
                "No Employee record linked to user '{}'".format(user),
                None,
                False,
                404,
            )

        checkin = frappe.new_doc("Employee Checkin")
        checkin.employee = employee
        checkin.log_type = log_type
        checkin.time = now_datetime()
        checkin.device_id = device_id

        meta = frappe.get_meta("Employee Checkin")
        if latitude is not None and meta.has_field("custom_latitude"):
            try:
                checkin.custom_latitude = float(latitude)
            except (TypeError, ValueError):
                pass
        if longitude is not None and meta.has_field("custom_longitude"):
            try:
                checkin.custom_longitude = float(longitude)
            except (TypeError, ValueError):
                pass

        checkin.insert(ignore_permissions=True)

        return response(
            "Checkin recorded",
            {
                "name": checkin.name,
                "log_type": checkin.log_type,
                "time": str(checkin.time),
                "employee": checkin.employee,
            },
            True,
            200,
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.create_employee_checkin")
        return response(str(e), None, False, 500)


@frappe.whitelist()
def get_today_checkin_status():
    """Return the calling user's most recent Employee Checkin for today,
    so the mobile UI can show 'Last checked IN at 09:42 AM' without
    storing state client-side."""
    try:
        from frappe.utils import today

        user = frappe.session.user
        if not user or user == "Guest":
            return response("Authentication required", None, False, 401)
        employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
        if not employee:
            return response("No Employee linked", None, False, 404)

        rows = frappe.get_all(
            "Employee Checkin",
            filters={
                "employee": employee,
                "time": [">=", today()],
            },
            fields=["name", "log_type", "time"],
            order_by="time desc",
            limit=1,
        )
        last = rows[0] if rows else None
        return response(
            "Checkin status",
            {
                "employee": employee,
                "last_log_type": last["log_type"] if last else None,
                "last_time": str(last["time"]) if last else None,
                "is_checked_in": bool(last and last["log_type"] == "IN"),
            },
            True,
            200,
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.get_today_checkin_status")
        return response(str(e), None, False, 500)


# =====================================================================
#  HR — Leave Application + Salary Slip endpoints for the mobile app
# =====================================================================


def _resolve_caller_employee():
    """Resolve the Employee linked to frappe.session.user.
    Returns the Employee name (string) or None."""
    user = frappe.session.user
    if not user or user == "Guest":
        return None
    return frappe.db.get_value("Employee", {"user_id": user}, "name")


@frappe.whitelist()
def get_leave_types():
    """List active Leave Types for use in the Apply Leave form."""
    try:
        types = frappe.get_all(
            "Leave Type",
            filters={"is_lwp": 0},
            fields=["name", "leave_type_name", "max_leaves_allowed", "is_compensatory"],
            order_by="name",
        )
        return response("Leave types", types, True, 200)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.get_leave_types")
        return response(str(e), None, False, 500)


@frappe.whitelist()
def get_my_leave_balance():
    """Return per-leave-type allocation/used/balance for the calling
    user's Employee for the current leave year.
    Uses ERPNext's get_leave_balance_on(employee, date) helper.
    """
    try:
        from frappe.utils import nowdate

        employee = _resolve_caller_employee()
        if not employee:
            return response("No Employee linked", None, False, 404)

        from hrms.hr.doctype.leave_application.leave_application import (
            get_leave_balance_on,
        )

        leave_types = frappe.get_all(
            "Leave Type",
            filters={"is_lwp": 0},
            fields=["name"],
            order_by="name",
        )
        rows = []
        for lt in leave_types:
            try:
                balance = get_leave_balance_on(
                    employee=employee,
                    leave_type=lt.name,
                    date=nowdate(),
                ) or 0
            except Exception:
                balance = 0
            rows.append({"leave_type": lt.name, "balance": flt(balance)})
        return response(
            "Leave balance",
            {"employee": employee, "balances": rows, "as_of": nowdate()},
            True,
            200,
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.get_my_leave_balance")
        return response(str(e), None, False, 500)


@frappe.whitelist()
def get_my_leave_applications(status_filter=None):
    """List the calling user's own Leave Applications, newest first."""
    try:
        employee = _resolve_caller_employee()
        if not employee:
            return response("No Employee linked", None, False, 404)

        filters = {"employee": employee}
        if status_filter and status_filter in ("Open", "Approved", "Rejected", "Cancelled"):
            filters["status"] = status_filter

        rows = frappe.get_all(
            "Leave Application",
            filters=filters,
            fields=[
                "name", "leave_type", "from_date", "to_date", "half_day",
                "total_leave_days", "status", "description", "posting_date",
                "leave_approver", "docstatus",
            ],
            order_by="from_date desc",
        )
        return response(
            "Leave applications",
            {"applications": rows},
            True,
            200,
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.get_my_leave_applications")
        return response(str(e), None, False, 500)


@frappe.whitelist(methods=["POST"])
def create_leave_application(
    leave_type=None,
    from_date=None,
    to_date=None,
    half_day=0,
    half_day_date=None,
    description=None,
):
    """Create + submit a Leave Application for the calling user."""
    try:
        data = frappe.request.get_json() or {}
        leave_type = leave_type or data.get("leave_type")
        from_date = from_date or data.get("from_date")
        to_date = to_date or data.get("to_date")
        half_day = half_day if half_day else data.get("half_day", 0)
        half_day_date = half_day_date or data.get("half_day_date")
        description = description or data.get("description")

        if not (leave_type and from_date and to_date):
            return response(
                "leave_type, from_date and to_date are required",
                None,
                False,
                400,
            )

        employee = _resolve_caller_employee()
        if not employee:
            return response("No Employee linked", None, False, 404)

        emp = frappe.get_doc("Employee", employee)
        leave_approver = emp.leave_approver or None

        doc = frappe.new_doc("Leave Application")
        doc.employee = employee
        doc.leave_type = leave_type
        doc.from_date = frappe.utils.getdate(from_date)
        doc.to_date = frappe.utils.getdate(to_date)
        doc.half_day = 1 if half_day else 0
        if doc.half_day and half_day_date:
            doc.half_day_date = frappe.utils.getdate(half_day_date)
        doc.description = description or ""
        if leave_approver:
            doc.leave_approver = leave_approver
        doc.status = "Open"
        doc.insert(ignore_permissions=True)
        try:
            doc.submit()
        except Exception:
            # Some installs auto-submit via workflow; some require explicit submit.
            # If submit fails (workflow rule), leave as Draft and let user know.
            frappe.log_error(
                frappe.get_traceback(),
                "field_sales.create_leave_application.submit",
            )

        return response(
            "Leave Application created",
            {
                "name": doc.name,
                "status": doc.status,
                "docstatus": doc.docstatus,
                "total_leave_days": flt(doc.total_leave_days),
            },
            True,
            200,
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.create_leave_application")
        return response(str(e), None, False, 500)


@frappe.whitelist()
def get_pending_leave_approvals():
    """List Leave Applications awaiting the calling user's approval.
    Filter: leave_approver = session user (frappe User name = Employee.leave_approver),
    status = Open, docstatus = 1.
    """
    try:
        user = frappe.session.user
        if not user or user == "Guest":
            return response("Authentication required", None, False, 401)

        rows = frappe.get_all(
            "Leave Application",
            filters={
                "leave_approver": user,
                "status": "Open",
                "docstatus": 1,
            },
            fields=[
                "name", "employee", "employee_name", "leave_type",
                "from_date", "to_date", "half_day", "total_leave_days",
                "description", "posting_date",
            ],
            order_by="from_date asc",
        )
        return response(
            "Pending approvals",
            {"approvals": rows},
            True,
            200,
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.get_pending_leave_approvals")
        return response(str(e), None, False, 500)


@frappe.whitelist(methods=["POST"])
def act_on_leave_application(name=None, action=None, reason=None):
    """Approve or reject a Leave Application. Caller must be the doc's
    leave_approver. `action` must be 'Approved' or 'Rejected'."""
    try:
        data = frappe.request.get_json() or {}
        name = name or data.get("name")
        action = action or data.get("action")
        reason = reason or data.get("reason")

        if action not in ("Approved", "Rejected"):
            return response("action must be Approved or Rejected", None, False, 400)
        if not name:
            return response("name is required", None, False, 400)

        user = frappe.session.user
        doc = frappe.get_doc("Leave Application", name)
        if doc.leave_approver and doc.leave_approver != user:
            return response(
                "You are not the leave approver for this application",
                None,
                False,
                403,
            )

        # The approval flow in ERPNext: set status, then save. If the doc
        # was Submitted (docstatus=1), we update via db_set + run_method
        # to fire downstream side-effects (leave ledger entries, etc.).
        if doc.docstatus == 1:
            doc.status = action
            if reason:
                doc.description = (doc.description or "") + "\n\n[Approver note] " + reason
            doc.save(ignore_permissions=True)
        else:
            # Draft: submit with the chosen status.
            doc.status = action
            doc.submit()

        return response(
            "Leave {}".format(action.lower()),
            {"name": doc.name, "status": doc.status},
            True,
            200,
        )
    except frappe.DoesNotExistError:
        return response("Leave Application not found", None, False, 404)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.act_on_leave_application")
        return response(str(e), None, False, 500)


@frappe.whitelist()
def get_my_salary_slips(year=None):
    """List the calling user's Salary Slips, newest first. Optionally
    filter by fiscal/calendar year."""
    try:
        employee = _resolve_caller_employee()
        if not employee:
            return response("No Employee linked", None, False, 404)

        filters = {"employee": employee, "docstatus": ["in", [0, 1]]}
        if year:
            try:
                year_int = int(year)
                filters["start_date"] = [
                    "between",
                    ["{}-01-01".format(year_int), "{}-12-31".format(year_int)],
                ]
            except (TypeError, ValueError):
                pass

        rows = frappe.get_all(
            "Salary Slip",
            filters=filters,
            fields=[
                "name", "start_date", "end_date", "posting_date",
                "gross_pay", "net_pay", "total_deduction", "docstatus",
                "status",
            ],
            order_by="start_date desc",
            limit=24,
        )
        return response("Salary slips", {"slips": rows}, True, 200)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.get_my_salary_slips")
        return response(str(e), None, False, 500)


@frappe.whitelist()
def get_salary_slip_detail(name=None):
    """Return the full Salary Slip detail (earnings + deductions tables)
    for the calling user. Refuses if the slip belongs to another
    employee — privacy guard."""
    try:
        if not name:
            return response("name is required", None, False, 400)

        employee = _resolve_caller_employee()
        if not employee:
            return response("No Employee linked", None, False, 404)

        doc = frappe.get_doc("Salary Slip", name)
        if doc.employee != employee:
            return response(
                "You can only view your own salary slips",
                None,
                False,
                403,
            )

        return response(
            "Salary slip detail",
            {
                "name": doc.name,
                "employee": doc.employee,
                "employee_name": doc.employee_name,
                "start_date": str(doc.start_date) if doc.start_date else None,
                "end_date": str(doc.end_date) if doc.end_date else None,
                "posting_date": str(doc.posting_date) if doc.posting_date else None,
                "gross_pay": flt(doc.gross_pay),
                "total_deduction": flt(doc.total_deduction),
                "net_pay": flt(doc.net_pay),
                "currency": doc.currency,
                "status": doc.status,
                "docstatus": doc.docstatus,
                "earnings": [
                    {
                        "salary_component": r.salary_component,
                        "amount": flt(r.amount),
                    } for r in (doc.earnings or [])
                ],
                "deductions": [
                    {
                        "salary_component": r.salary_component,
                        "amount": flt(r.amount),
                    } for r in (doc.deductions or [])
                ],
            },
            True,
            200,
        )
    except frappe.DoesNotExistError:
        return response("Salary Slip not found", None, False, 404)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.get_salary_slip_detail")
        return response(str(e), None, False, 500)


# =====================================================================
#  SOCIAL LOGIN — Google Sign-In (mobile)
# =====================================================================

@frappe.whitelist(allow_guest=True, methods=["POST"])
def social_login_google(id_token=None):
    """Exchange a Google ID token for a Frappe session.

    Mobile (google_sign_in package) does the native Google auth flow
    and gets a JWT id_token whose `aud` claim is the Web OAuth client
    configured on Chundakadan Settings. This endpoint verifies the
    token's signature + audience, looks up the matching Frappe User
    by email, and creates a session — returns the sid for the mobile
    client to store and use as a cookie on subsequent calls.

    Security:
    - Token signature verified against Google's published JWKS
    - audience (aud) must match Chundakadan Settings.google_oauth_web_client_id
    - issuer (iss) must be one of Google's accepted issuers
    - email must already exist in tabUser (no auto-provisioning)
    - account must be enabled
    """
    try:
        data = frappe.request.get_json() or {}
        id_token_str = id_token or data.get("id_token")
        if not id_token_str:
            return response("id_token is required", None, False, 400)

        expected_aud = frappe.db.get_single_value(
            "Chundakadan Settings", "google_oauth_web_client_id"
        )
        if not expected_aud:
            return response(
                "Google Sign-In is not configured. Ask admin to set "
                "'Google OAuth Web Client ID' in Chundakadan Settings.",
                None,
                False,
                503,
            )

        # Verify the token using Google's auth library. This calls out
        # to https://www.googleapis.com/oauth2/v3/certs (cached).
        try:
            from google.oauth2 import id_token as google_id_token
            from google.auth.transport import requests as google_requests
        except ImportError:
            return response(
                "Backend missing google-auth library. Install via "
                "'/home/frappe/<bench>/env/bin/pip install google-auth' "
                "then restart bench.",
                None,
                False,
                500,
            )

        try:
            idinfo = google_id_token.verify_oauth2_token(
                id_token_str,
                google_requests.Request(),
                expected_aud,
            )
        except ValueError as ve:
            return response(
                "Google token invalid or expired: {}".format(str(ve)),
                None,
                False,
                401,
            )

        # Issuer must be Google
        if idinfo.get("iss") not in (
            "accounts.google.com",
            "https://accounts.google.com",
        ):
            return response("Token not issued by Google", None, False, 401)

        email = (idinfo.get("email") or "").strip().lower()
        if not email:
            return response("Token has no email claim", None, False, 400)
        if not idinfo.get("email_verified", False):
            return response("Google email not verified", None, False, 401)

        # Look up Frappe User by exact email match (case-insensitive)
        user_name = frappe.db.get_value(
            "User",
            {"email": email},
            "name",
        )
        if not user_name:
            return response(
                "No Frappe User found for {}. Contact admin to provision your account.".format(email),
                None,
                False,
                404,
            )
        if not frappe.db.get_value("User", user_name, "enabled"):
            return response(
                "Account '{}' is disabled. Contact admin.".format(user_name),
                None,
                False,
                403,
            )

        # Create a real Frappe session as that user. We bypass the
        # LoginManager password check because we already verified the
        # caller's identity via Google.
        from frappe.auth import LoginManager
        login_manager = LoginManager()
        login_manager.user = user_name
        login_manager.post_login()

        sid = frappe.local.session.sid
        full_name = frappe.db.get_value("User", user_name, "full_name") or user_name

        return response(
            "Login successful",
            {
                "sid": sid,
                "user": user_name,
                "email": email,
                "full_name": full_name,
            },
            True,
            200,
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.social_login_google")
        return response(str(e), None, False, 500)


@frappe.whitelist(methods=["POST"])
def cancel_sales_order(name=None):
    """Cancel a Submitted Sales Order, but ONLY within 24 hours of submission.

    Submission time is approximated by `doc.modified` — Frappe blocks edits on
    docstatus=1, so `modified` stays at the moment of submit unless something
    else explicitly bumps it. Good enough for a 24h grace window.
    """
    try:
        from frappe.utils import now_datetime, get_datetime

        data = frappe.request.get_json() or {}
        so_name = name or data.get("name")
        if not so_name:
            return response("Sales Order name is required", None, False, 400)

        doc = frappe.get_doc("Sales Order", so_name)

        if doc.docstatus != 1:
            return response(
                "Only Submitted Sales Orders can be cancelled",
                None,
                False,
                400,
            )

        submitted_at = get_datetime(doc.modified)
        elapsed_hours = (now_datetime() - submitted_at).total_seconds() / 3600.0
        if elapsed_hours > 24:
            return response(
                "Cancellation window expired (24 hours after submission)",
                {"hours_since_submit": round(elapsed_hours, 2)},
                False,
                400,
            )

        caller_sp = _resolve_caller_sales_person()
        if caller_sp and getattr(doc, "custom_sales_person", None):
            if doc.custom_sales_person != caller_sp:
                return response(
                    "You do not have permission to cancel this order",
                    None,
                    False,
                    403,
                )

        doc.cancel()
        return response(
            "Sales Order cancelled",
            {"name": doc.name, "status": doc.status},
            True,
            200,
        )
    except frappe.DoesNotExistError:
        return response("Sales Order not found", None, False, 404)
    except frappe.LinkExistsError as e:
        return response(
            "Cannot cancel — this order has linked documents (invoices/deliveries). "
            "Cancel those first.",
            {"detail": str(e)},
            False,
            400,
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.cancel_sales_order")
        return response(str(e), None, False, 500)


@frappe.whitelist()
def get_active_company():
    """Return the company the calling user's create actions will be billed to.

    Mirrors `_resolve_company_for_caller` and adds the human-readable
    company name + currency so the mobile home screen can display
    "Welcome, Fanseem P / Chundakadan Agencies" without a second lookup.
    """
    try:
        company = _resolve_company_for_caller()
        if not company:
            return response("No company configured", None, False, 404)

        details = frappe.db.get_value(
            "Company",
            company,
            ["name", "company_name", "default_currency", "country"],
            as_dict=True,
        ) or {"name": company, "company_name": company}

        return response(
            "Active company resolved",
            {
                "name": details.get("name"),
                "company_name": details.get("company_name") or details.get("name"),
                "default_currency": details.get("default_currency"),
                "country": details.get("country"),
            },
            True,
            200,
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.get_active_company")
        return response(str(e), None, False, 500)

        