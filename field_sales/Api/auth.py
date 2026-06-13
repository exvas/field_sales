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

        # Gate on the Employee record — anyone in HR can log in.
        # The mobile shows HR tiles (Leaves, Payslips, Attendance, Expenses)
        # to all employees and hides sales tiles when sales_person_id is
        # empty. Pure portal/website users without an Employee record
        # stay blocked.
        emp = frappe.db.get_value(
            "Employee",
            {"user_id": user.name},
            ["name", "employee_name"],
            as_dict=True,
        )
        if not emp:
            frappe.local.response["message"] = {
                "success_key": 0,
                "message": "Access denied. This account is not linked to an Employee record.",
            }
            frappe.local.response.http_status_code = 403
            return

        employee_id = emp.name
        employee_name = emp.employee_name
        sales_person_id = frappe.db.get_value(
            "Sales Person",
            {"employee": emp.name},
            "name",
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
def get_items(price_list="Standard Selling", search=None, limit=0):
    """Fast item lookup for the mobile picker.

    Performance: previously ran ~3 SQL roundtrips PER item (price lookup
    + tax template + per-warehouse Bin scan). With ~8,800 items that was
    ~26,000 queries and timed out the mobile picker. This version does
    exactly 4 SQL queries regardless of catalog size and merges in
    Python — drops typical response time from 30s+ to under 1s.

    Optional params:
      search: substring match on item_code / item_name (case-insensitive)
      limit:  cap the row count (default 0 = no cap)

    Response shape is preserved for backward compatibility, but
    stock_by_warehouse is now an empty list per row — the old shape was
    the slowest part of the loop. Use get_item_stock_summary(item_code)
    for the per-warehouse breakdown of a single item.
    """
    try:
        fallback_pl = (
            frappe.db.get_single_value("Selling Settings", "selling_price_list")
            or "Standard Selling"
        )
    except Exception:
        fallback_pl = "Standard Selling"

    # 1) All items (single query, optionally filtered)
    item_filters = ["i.disabled = 0"]
    params = {}
    if search:
        item_filters.append("(i.name LIKE %(search)s OR i.item_name LIKE %(search)s)")
        params["search"] = "%{}%".format(search.strip())
    where_clause = " AND ".join(item_filters)
    limit_clause = "LIMIT {}".format(int(limit)) if int(limit or 0) > 0 else ""

    items = frappe.db.sql(
        """
        SELECT i.name, i.item_name, i.description, i.stock_uom, i.is_stock_item,
               i.standard_rate, i.last_purchase_rate, i.valuation_rate
        FROM `tabItem` i
        WHERE {where}
        ORDER BY i.item_name
        {limit}
        """.format(where=where_clause, limit=limit_clause),
        params,
        as_dict=True,
    )

    if not items:
        return []

    # 2) Prices: one query for BOTH the requested + fallback price lists.
    #    Build a per-item primary/fallback dict to apply the fallback chain.
    price_rows = frappe.db.sql(
        """
        SELECT item_code, price_list, price_list_rate
        FROM `tabItem Price`
        WHERE price_list IN (%(pl)s, %(fpl)s)
        """,
        {"pl": price_list, "fpl": fallback_pl},
        as_dict=True,
    )
    primary_prices = {}
    fallback_prices = {}
    for row in price_rows:
        if row.price_list == price_list:
            primary_prices[row.item_code] = row.price_list_rate
        else:
            fallback_prices[row.item_code] = row.price_list_rate

    # 3) Tax template: one row per item (we just need any one)
    tax_rows = frappe.db.sql(
        """
        SELECT parent, MIN(item_tax_template) AS item_tax_template
        FROM `tabItem Tax`
        GROUP BY parent
        """,
        as_dict=True,
    )
    tax_dict = {r.parent: r.item_tax_template for r in tax_rows}

    # 4) Aggregated stock across warehouses, one row per item
    stock_rows = frappe.db.sql(
        """
        SELECT item_code, SUM(actual_qty) AS total_stock
        FROM `tabBin`
        GROUP BY item_code
        """,
        as_dict=True,
    )
    stock_dict = {r.item_code: flt(r.total_stock or 0) for r in stock_rows}

    # Merge in Python — O(N), no further DB hits
    result = []
    for it in items:
        price = (
            primary_prices.get(it.name)
            or fallback_prices.get(it.name)
            or it.get("standard_rate")
            or it.get("last_purchase_rate")
            or it.get("valuation_rate")
            or 0
        )
        result.append({
            "item_code": it.name,
            "item_name": it.item_name,
            "description": it.description,
            "uom": it.stock_uom,
            "price": flt(price),
            "maintain_stock": it.is_stock_item,
            "tax_template": tax_dict.get(it.name, "") or "",
            "total_stock": stock_dict.get(it.name, 0),
            "stock_by_warehouse": [],  # use get_item_stock_summary for per-WH
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
    # View-All Transaction Role bypass: a manager configured under
    # Chundakadan Settings.view_all_transaction_role gets every Sales
    # Order on mobile regardless of which sales person is asking.
    bypass = _caller_has_view_all_role()

    if not bypass and not sales_person_id:
        return {
            "status": "error",
            "message": "Sales Person ID is required"
        }

    filters = {"docstatus": ["in", [0, 1]]}
    if not bypass:
        filters["custom_sales_person"] = sales_person_id

    sales_order_names = frappe.get_all(
        "Sales Order",
        filters=filters,
        order_by="modified desc",
        pluck="name",
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

    # Sales-Person-specific MOP override configured in
    # Chundakadan Settings.mop_mapping. Hard 400 if not configured —
    # every (sales_person, company, mode) tuple must be explicit.
    caller_sp = _resolve_caller_sales_person()
    paid_to = _resolve_mop_account(caller_sp, invoice.company, mode_of_payment)

    if not paid_to:
        return {
            "status": "error",
            "message": (
                f"No Chundakadan Settings.mop_mapping row for "
                f"sales_person='{caller_sp}', company='{invoice.company}', "
                f"mode_of_payment='{mode_of_payment}'. Ask an admin to add the row."
            ),
            "code": 400,
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

    # Resolve company (Employee.company -> Settings.default_company -> first Company)
    company = _resolve_company_for_caller()

    # Sales-Person-specific MOP override configured in
    # Chundakadan Settings.mop_mapping. Hard 400 if not configured.
    caller_sp = _resolve_caller_sales_person() or data.get("sales_person")
    paid_to = _resolve_mop_account(caller_sp, company, mode_of_payment)
    if not paid_to:
        frappe.throw(_(
            "No Chundakadan Settings.mop_mapping row for "
            "sales_person='{0}', company='{1}', mode_of_payment='{2}'. "
            "Ask an admin to add the row."
        ).format(caller_sp, company, mode_of_payment))

    pe = frappe.new_doc("Payment Entry")
    pe.payment_type = "Receive"
    pe.party_type = "Customer"
    pe.party = customer
    pe.posting_date = now()
    pe.company = company
    pe.custom_sales_person = data.get("sales_person")
    pe.mode_of_payment = mode_of_payment
    pe.paid_amount = total_allocated_amount
    pe.received_amount = total_allocated_amount
    pe.target_exchange_rate = 1
    pe.paid_to = paid_to

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

    # Surface BOTH drafts (docstatus=0) and submitted (docstatus=1) PEs.
    # Mirrors the Quotation/SO mobile lists where users want to see their
    # own recent activity, not just drafts. Cancelled (docstatus=2) is
    # excluded as those are dead records.
    payment_entries = frappe.get_all(
        "Payment Entry",
        filters={
            "party_type": "Customer",
            "party": customer_name,
            "custom_sales_person": sales_person,
            "docstatus": ["in", [0, 1]],
        },
        fields=["name", "posting_date", "paid_amount", "reference_no", "docstatus"],
        order_by="creation desc",
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
            "docstatus": pe.docstatus,
            "status": "Submitted" if pe.docstatus == 1 else "Draft",
            "references": ref_list,
        })

    return {
        "status": "success",
        "data": result,
        "total_allocated_amount": total_allocated
    }

@frappe.whitelist(allow_guest=False)
def save_fcm_token(fcm_token, device_platform=None, device_id=None):
    """Register / refresh an FCM token for the calling user. Idempotent —
    if the exact same token already exists for this user we just update
    last_seen; same device_id replaces the prior token; otherwise insert
    a new row.

    Called by the Flutter app after Firebase getToken() resolves.
    """
    user = frappe.session.user
    if not user or user == "Guest":
        frappe.throw("Not logged in")
    if not fcm_token:
        frappe.throw("fcm_token is required")

    now = frappe.utils.now()

    # 1. Exact same token already stored? Just touch last_seen.
    existing = frappe.db.get_value(
        "FCM Token",
        {"user": user, "token": fcm_token},
        "name",
    )
    if existing:
        frappe.db.set_value("FCM Token", existing, "last_seen", now,
                            update_modified=False)
        frappe.db.commit()
        return {"status": "success", "message": "Token refreshed", "name": existing}

    # 2. Same device, different token? Replace.
    if device_id:
        prior = frappe.db.get_value(
            "FCM Token",
            {"user": user, "device_id": device_id},
            "name",
        )
        if prior:
            frappe.db.set_value("FCM Token", prior, {
                "token": fcm_token,
                "device_platform": device_platform or "Android",
                "last_seen": now,
            }, update_modified=False)
            frappe.db.commit()
            return {"status": "success", "message": "Token replaced", "name": prior}

    # 3. Brand new — insert.
    doc = frappe.get_doc({
        "doctype": "FCM Token",
        "user": user,
        "token": fcm_token,
        "device_platform": device_platform or "Android",
        "device_id": device_id,
        "last_seen": now,
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return {"status": "success", "message": "Token saved", "name": doc.name}


@frappe.whitelist(allow_guest=False)
def delete_fcm_token(fcm_token=None, device_id=None):
    """Called on logout. Removes this device's tokens so the user stops
    receiving pushes on a phone they no longer have access to.
    """
    user = frappe.session.user
    if not user or user == "Guest":
        return response("Not logged in", None, False, 401)
    filters = {"user": user}
    if fcm_token:
        filters["token"] = fcm_token
    elif device_id:
        filters["device_id"] = device_id
    else:
        return response("fcm_token or device_id required", None, False, 400)
    deleted = frappe.db.delete("FCM Token", filters)
    frappe.db.commit()
    return response("Token removed", {"removed": True}, True, 200)


@frappe.whitelist()
def get_hr_policy():
    """Return the current HR Policy snapshot. Mobile compares `version`
    against its cached copy and re-fetches the PDF only if newer.
    """
    try:
        doc = frappe.get_single("HR Policy")
        pdf_url = doc.get("policy_pdf") or ""
        # Frappe stores Attach as a relative path like /private/files/... or
        # /files/.... Prepend site URL for the mobile to fetch.
        full_pdf_url = ""
        if pdf_url:
            base = frappe.utils.get_url()
            full_pdf_url = pdf_url if pdf_url.startswith("http") else f"{base}{pdf_url}"
        return response(
            "HR Policy",
            {
                "version": doc.version or 0,
                "policy_pdf_url": full_pdf_url,
                "policy_html": doc.policy_html or "",
                "last_updated_by": doc.last_updated_by or "",
                "last_updated_on": str(doc.last_updated_on or ""),
            },
            True,
            200,
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.get_hr_policy")
        return response(str(e), None, False, 500)


@frappe.whitelist()
def get_newsletters(limit=20, offset=0):
    """List recent newsletters for the mobile inbox. Returns each with a
    short HTML-stripped preview; the detail endpoint returns the full
    body when the user taps in.
    """
    try:
        try:
            limit_n = max(1, min(int(limit), 100))
        except (TypeError, ValueError):
            limit_n = 20
        try:
            offset_n = max(0, int(offset))
        except (TypeError, ValueError):
            offset_n = 0

        rows = frappe.get_all(
            "Newsletter",
            fields=[
                "name", "subject", "sender_name", "sender_email",
                "send_from", "creation",
            ],
            order_by="creation desc",
            limit=limit_n,
            start=offset_n,
            ignore_permissions=True,
        )
        # Add a 200-char preview from `message`
        import re
        for r in rows:
            msg = frappe.db.get_value("Newsletter", r["name"], "message") or ""
            text = re.sub(r"<[^>]+>", " ", msg).strip()
            text = re.sub(r"\s+", " ", text)
            r["preview"] = (text[:200] + "…") if len(text) > 200 else text
            r["creation"] = str(r.get("creation") or "")
        return response("Newsletters", {"entries": rows, "count": len(rows)}, True, 200)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.get_newsletters")
        return response(str(e), None, False, 500)


@frappe.whitelist()
def get_my_notifications(limit=50, unread_only=0):
    """List the caller's Notification Log entries (the persistent log
    behind the mobile bell icon). Push notifications create one row per
    recipient via chundakadan.utils.push._log_notification, so every
    historical push shows up here even if the device missed it.
    """
    try:
        user = frappe.session.user
        if not user or user == "Guest":
            return response("Authentication required", None, False, 401)
        try:
            limit_n = max(1, min(int(limit), 200))
        except (TypeError, ValueError):
            limit_n = 50
        filters = {"for_user": user}
        if str(unread_only) in ("1", "true", "True"):
            filters["read"] = 0

        rows = frappe.get_all(
            "Notification Log",
            filters=filters,
            fields=[
                "name", "subject", "email_content", "type",
                "document_type", "document_name", "read",
                "from_user", "creation",
            ],
            order_by="creation desc",
            limit=limit_n,
            ignore_permissions=True,
        )
        for r in rows:
            r["creation"] = str(r.get("creation") or "")
        return response(
            "My notifications",
            {"entries": rows, "count": len(rows)},
            True, 200,
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(),
                         "field_sales.get_my_notifications")
        return response(str(e), None, False, 500)


@frappe.whitelist(methods=["POST"])
def mark_notification_read(name=None):
    """Mark a single Notification Log row as read. Called when the user
    taps a row in the mobile bell list.
    """
    try:
        user = frappe.session.user
        if not user or user == "Guest":
            return response("Authentication required", None, False, 401)
        if not name:
            return response("name is required", None, False, 400)
        owner = frappe.db.get_value("Notification Log", name, "for_user")
        if owner != user:
            return response("Not your notification", None, False, 403)
        # Only set columns that actually exist on Notification Log in
        # this Frappe version. `seen` was tried 2026-06-04 and threw
        # "Unknown column 'seen' in 'SET'" — drop it. The `read` flag
        # alone is what the desk + mobile both look at.
        frappe.db.set_value("Notification Log", name,
                            "read", 1,
                            update_modified=False)
        frappe.db.commit()
        return response("Marked read", {"name": name}, True, 200)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(),
                         "field_sales.mark_notification_read")
        return response(str(e), None, False, 500)


@frappe.whitelist(methods=["POST"])
def mark_all_notifications_read():
    """Clears the unread badge by setting read=1 on every unread
    notification for the caller. Called from the mobile bell's
    'Mark all as read' action.
    """
    try:
        user = frappe.session.user
        if not user or user == "Guest":
            return response("Authentication required", None, False, 401)
        n = frappe.db.sql(
            """
            UPDATE `tabNotification Log`
               SET `read` = 1
             WHERE for_user = %s AND `read` = 0
            """,
            (user,),
        )
        frappe.db.commit()
        affected = frappe.db.sql("SELECT ROW_COUNT()")[0][0]
        return response(
            "All marked read",
            {"affected": affected},
            True, 200,
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(),
                         "field_sales.mark_all_notifications_read")
        return response(str(e), None, False, 500)


@frappe.whitelist()
def get_unread_notification_count():
    """Returns the unread Notification Log count for the caller. Polled
    by the mobile home page to render the badge on the bell icon.
    """
    try:
        user = frappe.session.user
        if not user or user == "Guest":
            return response("Authentication required", None, False, 401)
        n = frappe.db.count("Notification Log",
                            filters={"for_user": user, "read": 0})
        return response("Unread count", {"count": n}, True, 200)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(),
                         "field_sales.get_unread_notification_count")
        return response(str(e), None, False, 500)


@frappe.whitelist()
def get_newsletter_details(name=None):
    """Return the full body of one Newsletter for the detail page."""
    try:
        if not name:
            return response("name is required", None, False, 400)
        row = frappe.db.get_value(
            "Newsletter", name,
            ["name", "subject", "sender_name", "sender_email", "message", "creation"],
            as_dict=True,
        )
        if not row:
            return response("Newsletter not found", None, False, 404)
        row["creation"] = str(row.get("creation") or "")
        return response("Newsletter", row, True, 200)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.get_newsletter_details")
        return response(str(e), None, False, 500)

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
    # Explicit visit_type = Customer Visit. Field auto-created by
    # chundakadan.install.ensure_visit_log_visit_type_field. has_field
    # guards against missing-field benches that haven't migrated.
    if frappe.get_meta("Customer Visit Log").has_field("visit_type"):
        doc.visit_type = "Customer Visit"
    # ignore_permissions=True: this endpoint is @frappe.whitelist'd +
    # validates required fields above, so we trust authenticated users
    # to log their own visits. Without this, every sales executive
    # hits 403 'No permission for Customer Visit Log' because the
    # doctype's role-perm rules don't include 'Sales User' (matches
    # the pattern used in create_employee_checkin's visit-log mirror).
    doc.insert(ignore_permissions=True)

    # NO Employee Checkin mirror here (intentionally). Customer visits
    # logged mid-day are sales tracking, NOT attendance — they should
    # ONLY land in Customer Visit Log. The mirror was added 2026-06-05
    # and reverted same day after Najeeb clarified the intent:
    #   create_employee_checkin (Check-In/Check-Out) → both records
    #   log_customer_visit       (mid-day visits)     → visit log only

    return {
        "success": True,
        "message": "Customer Visit Log created successfully",
        "name": doc.name,
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
    """Return tasks assigned to the calling sales person.

    Picks up BOTH assignment paths so the desk team can use whichever
    workflow they prefer without losing visibility on mobile:

      1. The custom Link field `Task.custom_assigned_to` -> Sales Person.
         (Old workflow — admin picks the sales person directly on the
         Task form.)
      2. Frappe's standard "Assign To" sidebar, which writes the user's
         email into `Task._assign` (JSON list) AND creates a ToDo row.
         We resolve the sales person -> Employee -> user_id and check
         for membership in _assign.

    Until this was extended, tasks assigned only via the sidebar (with
    custom_assigned_to left blank) were invisible to mobile — which is
    exactly what was happening on this bench.
    """
    try:
        sa = frappe.form_dict.get("sales_person")
        if not sa:
            return {
                "status": "error",
                "message": "sales person is required",
                "code": 400,
            }

        # Path 1: custom_assigned_to Link match.
        names_link = set(
            frappe.get_all("Task", filters={"custom_assigned_to": sa}, pluck="name")
        )

        # Path 2: standard "Assign To" sidebar — find the user_id behind
        # this sales person, then look for it inside Task._assign.
        names_assign = set()
        employee = frappe.db.get_value("Sales Person", sa, "employee")
        user_id = (
            frappe.db.get_value("Employee", employee, "user_id") if employee else None
        )
        if user_id:
            names_assign = set(
                frappe.db.sql_list(
                    """
                    SELECT name FROM `tabTask`
                    WHERE _assign LIKE %(needle)s
                    """,
                    {"needle": f'%"{user_id}"%'},
                )
            )

        all_names = list(names_link | names_assign)
        if not all_names:
            return {
                "status": "success",
                "message": "task details retrieved",
                "data": [],
                "code": 200,
            }

        docs = frappe.get_all(
            "Task",
            filters={"name": ["in", all_names]},
            fields=[
                "name", "subject", "status",
                "custom_customer", "custom_assigned_to",
                "exp_start_date", "exp_end_date", "description", "custom_remarks",
            ],
            order_by="modified desc",
        )

        for d in docs:
            if d.get("description"):
                soup = BeautifulSoup(d["description"], "html.parser")
                d["description"] = soup.get_text()

        return {
            "status": "success",
            "message": "task details retrieved",
            "data": docs,
            "code": 200,
        }

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "Task Fetch Error")
        return {
            "status": "error",
            "message": str(e),
            "http_status_code": 500,
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


@frappe.whitelist()
def get_mop_default_account(mode_of_payment=None, company=None):
    """Whitelisted helper for the Chundakadan Settings client script.

    JS calling frappe.db.get_value('Mode of Payment Account', ...) hits
    check_parent_permission and throws 'Not permitted' even for System
    Manager because Mode of Payment Account is a child DocType. This
    helper gates on the caller having write access to Chundakadan
    Settings (anyone editing the MOP grid does) and runs the lookup
    with ignore_permissions=True.

    Returns the default_account string or None when no row matches.
    """
    if not frappe.has_permission("Chundakadan Settings", "write"):
        frappe.throw(_("You do not have permission to read Chundakadan Settings."))
    if not (mode_of_payment and company):
        return None
    return frappe.db.get_value(
        "Mode of Payment Account",
        {"parent": mode_of_payment, "company": company},
        "default_account",
    )


def _caller_has_view_all_role():
    """True if the session user holds the Role configured in
    Chundakadan Settings -> view_all_transaction_role, OR appears as a
    Manager in Chundakadan Settings -> manager_details.

    Used by mobile list endpoints to bypass the per-sales-person filter
    for managers who need cross-team visibility. Returns False when the
    setting is blank (the default — no override).
    """
    user = frappe.session.user
    if not user or user == "Guest":
        return False
    if user == "Administrator":
        return True
    role = frappe.db.get_single_value("Chundakadan Settings", "view_all_transaction_role")
    if role and role in frappe.get_roles(user):
        return True
    # Manager rows resolve via Employee, mirroring the Sales Person chain:
    # frappe.session.user -> Employee.user_id -> Manager Detail.employee
    employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
    if not employee:
        return False
    return bool(frappe.db.exists("Chundakadan Manager Detail", {
        "parent": "Chundakadan Settings",
        "parenttype": "Chundakadan Settings",
        "employee": employee,
    }))


def _caller_manager_flags():
    """Return (allow_edit, allow_submit, workflow_approval) for the caller
    from Chundakadan Settings -> manager_details, or (False, False, False)
    if the user is not a manager.

    Resolves via Employee.user_id, same as _resolve_caller_sales_person.
    """
    user = frappe.session.user
    if not user or user == "Guest":
        return (False, False, False)
    employee = frappe.db.get_value("Employee", {"user_id": user}, "name")
    if not employee:
        return (False, False, False)
    row = frappe.db.get_value(
        "Chundakadan Manager Detail",
        {
            "parent": "Chundakadan Settings",
            "parenttype": "Chundakadan Settings",
            "employee": employee,
        },
        ["allow_edit", "allow_submit", "workflow_approval"],
        as_dict=True,
    )
    if not row:
        return (False, False, False)
    return (bool(row.allow_edit), bool(row.allow_submit), bool(row.workflow_approval))


def _resolve_sales_person_defaults(sales_person, company=None):
    """Look up per-sales-person defaults (warehouse, cost_center, price_list,
    default_mode_of_payment) from Chundakadan Settings -> sales_person_details.

    Returns a frappe._dict (possibly empty) so callers can do .get() without
    None-checks. If company is provided, prefers the row matching that
    company; otherwise returns the first row for the sales person.
    """
    if not sales_person:
        return frappe._dict()
    filters = {
        "parent": "Chundakadan Settings",
        "parenttype": "Chundakadan Settings",
        "sales_person": sales_person,
    }
    if company:
        filters["company"] = company
    fields = ["warehouse", "cost_center", "price_list", "default_mode_of_payment", "company"]
    row = frappe.db.get_value("Chundakadan Sales Person Detail", filters, fields, as_dict=True)
    if not row and company:
        # Fall back to any row for this sales person if the company-specific one is missing.
        filters.pop("company")
        row = frappe.db.get_value("Chundakadan Sales Person Detail", filters, fields, as_dict=True)
    return frappe._dict(row or {})


def _resolve_mop_account(sales_person, company, mode_of_payment):
    """Look up the Sales-Person-specific paid_to Account configured in
    Chundakadan Settings.mop_mapping.

    Returns the Account name or None. Caller MUST hard-fail (400) when
    None — per product decision, every (sales_person, company, mode)
    tuple in use must be explicitly mapped.

    Stored as a child table on the Chundakadan Settings singleton, so we
    query tabChundakadan Sales Person MOP directly with parent locked.
    """
    if not (sales_person and company and mode_of_payment):
        return None
    return frappe.db.get_value(
        "Chundakadan Sales Person MOP",
        {
            "parent": "Chundakadan Settings",
            "parenttype": "Chundakadan Settings",
            "sales_person": sales_person,
            "company": company,
            "mode_of_payment": mode_of_payment,
        },
        "account",
    )


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

        # View-All bypass: managers configured under
        # Chundakadan Settings.view_all_transaction_role drop into the
        # "no scope" branch below (which returns every quotation).
        if _caller_has_view_all_role():
            effective_sp = None

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
                "custom_sales_person": doc.get("custom_sales_person") or "",
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


@frappe.whitelist()
def get_my_recent_payment_entries(
    limit=50, status=None, customer=None, from_date=None, to_date=None
):
    """List the calling sales person's recent Payment Entries (Drafts +
    Submitted), across every customer. Powers the always-on "My Recent
    Payment Entries" card on the mobile PE screen.

    Optional filters:
      - status: 'Draft' | 'Submitted' (anything else = no status filter)
      - customer: party id (e.g. CA-CUS-02064)
      - from_date / to_date: ISO date strings (inclusive). Filters on
        posting_date.

    Always-on filters:
      - custom_sales_person = caller's resolved Sales Person
      - docstatus IN (0, 1)   (cancelled excluded)
    Ordered: creation desc.
    """
    try:
        caller_sp = _resolve_caller_sales_person()
        if not caller_sp:
            return response("No Sales Person linked to your account", None, False, 404)
        try:
            limit_n = int(limit) if limit else 50
        except (TypeError, ValueError):
            limit_n = 50

        filters = {
            "custom_sales_person": caller_sp,
            "docstatus": ["in", [0, 1]],
        }
        if status == "Draft":
            filters["docstatus"] = 0
        elif status == "Submitted":
            filters["docstatus"] = 1
        if customer:
            filters["party"] = customer
        if from_date:
            filters["posting_date"] = [">=", from_date]
        if to_date:
            # If from_date also present, combine into a between range
            if isinstance(filters.get("posting_date"), list):
                filters["posting_date"] = ["between", [from_date, to_date]]
            else:
                filters["posting_date"] = ["<=", to_date]

        rows = frappe.get_all(
            "Payment Entry",
            filters=filters,
            fields=[
                "name", "posting_date", "paid_amount", "reference_no",
                "docstatus", "party", "party_name", "mode_of_payment",
            ],
            order_by="creation desc",
            limit=limit_n,
        )
        for r in rows:
            r["status"] = "Submitted" if r.get("docstatus") == 1 else "Draft"
        return response("My recent PEs", {"entries": rows}, True, 200)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.get_my_recent_payment_entries")
        return response(str(e), None, False, 500)


@frappe.whitelist()
def get_my_bounced_cheques(limit=100, from_date=None, to_date=None):
    """List the caller's bounced cheques. Filters Payment Entry on the
    chundakadan custom_check_bounce=1 flag (the same field powering the
    desk "Cheque Bounce" report). Submitted docs only — bounce is a
    post-clearance status, never set on Draft.

    Optional filters:
      - from_date / to_date: posting_date bounds (inclusive)

    Returns each PE plus its first Sales Invoice reference so the mobile
    can show "vs which invoice" without a second round-trip.
    """
    try:
        caller_sp = _resolve_caller_sales_person()
        if not caller_sp:
            return response("No Sales Person linked to your account", None, False, 404)
        try:
            limit_n = int(limit) if limit else 100
        except (TypeError, ValueError):
            limit_n = 100

        filters = {
            "custom_sales_person": caller_sp,
            "docstatus": 1,
            "custom_check_bounce": 1,
        }
        if from_date and to_date:
            filters["posting_date"] = ["between", [from_date, to_date]]
        elif from_date:
            filters["posting_date"] = [">=", from_date]
        elif to_date:
            filters["posting_date"] = ["<=", to_date]

        rows = frappe.get_all(
            "Payment Entry",
            filters=filters,
            fields=[
                "name", "posting_date", "paid_amount",
                "party", "party_name", "reference_no", "reference_date",
                "mode_of_payment",
            ],
            order_by="posting_date desc",
            limit=limit_n,
        )

        # Tack on the first Sales Invoice reference for each PE (cheap;
        # one query, IN clause). Sales people want to know which bill
        # the bounced cheque was meant to clear.
        if rows:
            pe_names = [r["name"] for r in rows]
            refs = frappe.db.sql(
                """
                SELECT per.parent, per.reference_name, per.allocated_amount
                FROM `tabPayment Entry Reference` per
                WHERE per.parent IN %(names)s
                  AND per.reference_doctype = 'Sales Invoice'
                ORDER BY per.idx ASC
                """,
                {"names": tuple(pe_names)},
                as_dict=True,
            )
            first_ref = {}
            for r in refs:
                first_ref.setdefault(r["parent"], r)
            total_bounced = 0.0
            for r in rows:
                ref = first_ref.get(r["name"])
                r["sales_invoice"] = ref["reference_name"] if ref else None
                r["allocated_amount"] = ref["allocated_amount"] if ref else 0
                total_bounced += float(r.get("paid_amount") or 0)
        else:
            total_bounced = 0.0

        return response(
            "My bounced cheques",
            {
                "entries": rows,
                "count": len(rows),
                "total_amount": total_bounced,
            },
            True,
            200,
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.get_my_bounced_cheques")
        return response(str(e), None, False, 500)


@frappe.whitelist()
def get_payment_entry_details(name=None):
    """Full details for one Payment Entry — header fields + reference rows
    (Sales Invoice / Sales Order allocations). Powers the mobile detail
    sheet that opens when a user taps a row in "My Recent Payment
    Entries". Callers must be the sales person who owns the doc.

    NOTE: uses db.get_value + raw SQL instead of frappe.get_doc because
    mobile users (Sales User role) typically lack read permission on the
    Payment Entry DocType — frappe.get_doc would throw PermissionError
    → HTTP 417. We have our own custom_sales_person == caller gate, so
    bypassing standard role perms is correct here (mirrors the
    get_mop_default_account pattern).
    """
    try:
        if not name:
            return response("name is required", None, False, 400)

        # Fetch header via db.get_value — bypasses doctype-level role check.
        pe = frappe.db.get_value(
            "Payment Entry",
            name,
            [
                "name", "docstatus", "posting_date", "party", "party_name",
                "mode_of_payment", "paid_amount", "received_amount",
                "reference_no", "reference_date", "remarks",
                "total_allocated_amount", "unallocated_amount",
                "custom_sales_person",
            ],
            as_dict=True,
        )
        if not pe:
            return response("Payment Entry not found", None, False, 404)

        # Permission gate: caller must own this PE (or Administrator).
        caller_sp = _resolve_caller_sales_person()
        owner_sp = pe.get("custom_sales_person")
        if frappe.session.user != "Administrator" and (
            not caller_sp or caller_sp != owner_sp
        ):
            return response("Not your Payment Entry", None, False, 403)

        # Fetch reference rows via raw SQL — child DocType reads via the
        # client API would hit check_parent_permission (gotcha #3).
        ref_rows = frappe.db.sql(
            """
            SELECT reference_doctype, reference_name, total_amount,
                   outstanding_amount, allocated_amount, due_date
            FROM `tabPayment Entry Reference`
            WHERE parent = %s
            ORDER BY idx ASC
            """,
            (name,),
            as_dict=True,
        )
        refs = [
            {
                "reference_doctype": r.get("reference_doctype"),
                "reference_name": r.get("reference_name"),
                "total_amount": r.get("total_amount") or 0,
                "outstanding_amount": r.get("outstanding_amount") or 0,
                "allocated_amount": r.get("allocated_amount") or 0,
                "due_date": r.get("due_date"),
            }
            for r in (ref_rows or [])
        ]

        payload = {
            "name": pe["name"],
            "docstatus": pe["docstatus"],
            "status": "Submitted" if pe["docstatus"] == 1 else "Draft",
            "posting_date": pe.get("posting_date"),
            "party": pe.get("party"),
            "party_name": pe.get("party_name"),
            "mode_of_payment": pe.get("mode_of_payment"),
            "paid_amount": pe.get("paid_amount") or 0,
            "received_amount": pe.get("received_amount") or 0,
            "reference_no": pe.get("reference_no"),
            "reference_date": pe.get("reference_date"),
            "remarks": pe.get("remarks"),
            "total_allocated_amount": pe.get("total_allocated_amount") or 0,
            "unallocated_amount": pe.get("unallocated_amount") or 0,
            "references": refs,
        }
        return response("PE details", payload, True, 200)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.get_payment_entry_details")
        return response(str(e), None, False, 500)


@frappe.whitelist(methods=["POST"])
def submit_payment_entry(name=None):
    """Submit a Draft Payment Entry created via the mobile.
    Mirrors submit_quotation / submit_sales_order — the create endpoint
    leaves the PE at docstatus=0 so the user can review (and Print /
    Share). This whitelist takes it from Draft → Submitted.
    """
    try:
        data = frappe.request.get_json() or {}
        name = name or data.get("name")

        if not name:
            return response("Payment Entry name is required", None, False, 400)
        if not frappe.db.exists("Payment Entry", name):
            return response(f"Payment Entry '{name}' does not exist", None, False, 404)

        doc = frappe.get_doc("Payment Entry", name)

        if doc.docstatus != 0:
            return response("Already submitted or cancelled", None, False, 400)

        # Permission: caller must be the PE's owning sales person (or Admin).
        caller_sp = _resolve_caller_sales_person()
        if caller_sp and doc.get("custom_sales_person") and doc.custom_sales_person != caller_sp:
            return response(
                "You do not have permission to submit this Payment Entry",
                None,
                False,
                403,
            )

        doc.submit()

        return response(
            "Payment Entry submitted",
            {"name": doc.name, "status": "Submitted", "docstatus": doc.docstatus},
            True,
            200,
        )
    except frappe.PermissionError:
        frappe.log_error(frappe.get_traceback(), "field_sales.submit_payment_entry")
        return response("Permission denied", None, False, 403)
    except frappe.DoesNotExistError:
        return response("Payment Entry not found", None, False, 404)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.submit_payment_entry")
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
            # frappe.get_print() doesn't accept ignore_permissions — was
            # silently throwing TypeError before the fallback could even
            # produce a useful HTML response. Standard role perms apply.
            pdf_binary = frappe.get_print(
                doctype,
                name,
                print_format=print_format,
                letterhead=letterhead,
                as_pdf=True,
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
        # Doctype fields: `employee` (Link -> Sales Person, labeled
        # "Sales Person Id") and `date`. The CREATE endpoint
        # log_customer_visit writes those exact field names. Earlier
        # versions of this counter queried `sales_person`/`visit_date`
        # which don't exist on the doctype — both attempts errored out
        # and the except swallowed the bug, giving every sales person
        # a permanent "0 Visits" tile no matter how many they logged.
        visits = 0
        try:
            visits = frappe.db.count(
                "Customer Visit Log",
                filters={
                    "employee": sp,
                    "date": today_str,
                },
            )
        except Exception:
            try:
                # Fallback: rows created today by this sales person
                visits = frappe.db.count(
                    "Customer Visit Log",
                    filters={
                        "employee": sp,
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


# ─────────────────────────────────────────────────────────────────────
# Today-detail endpoints — back the three home tiles (Visits / Orders /
# Collected). Each returns the list that the count on the tile rolled
# up, in a shape the mobile detail page can render generically.
# Caller's sales person is resolved via _resolve_caller_sales_person
# (same as get_today_snapshot); sales_person_id arg is honoured if
# explicitly passed but cross-user reads are rejected.
# ─────────────────────────────────────────────────────────────────────

def _resolve_sp_for_detail(sales_person_id=None):
    """Common gate for the three today-detail endpoints. Returns the
    sales person name or raises via response().
    """
    caller_sp = _resolve_caller_sales_person()
    sp = sales_person_id or caller_sp
    if not sp:
        return None, response("Sales person required", None, False, 400)
    if caller_sp and sp != caller_sp:
        return None, response("You can only view your own list", None, False, 403)
    return sp, None


@frappe.whitelist()
def get_my_today_visits(sales_person_id=None):
    """Today's Customer Visit Log rows for the caller."""
    try:
        from frappe.utils import today
        sp, err = _resolve_sp_for_detail(sales_person_id)
        if err is not None:
            return err
        rows = frappe.get_all(
            "Customer Visit Log",
            filters={"employee": sp, "date": today()},
            fields=["name", "customer_name", "time", "latitude", "longitude", "description"],
            order_by="time desc",
            limit=100,
        )
        for r in rows:
            if r.get("time"):
                r["time"] = str(r["time"])
        return response("Today's visits", {"entries": rows, "count": len(rows)}, True, 200)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.get_my_today_visits")
        return response(str(e), None, False, 500)


@frappe.whitelist()
def get_my_today_orders(sales_person_id=None):
    """Today's Sales Orders created by the caller."""
    try:
        from frappe.utils import today
        sp, err = _resolve_sp_for_detail(sales_person_id)
        if err is not None:
            return err
        rows = frappe.get_all(
            "Sales Order",
            filters={
                "custom_sales_person": sp,
                "transaction_date": today(),
                "docstatus": ["in", [0, 1]],
            },
            fields=[
                "name", "customer", "customer_name", "transaction_date",
                "grand_total", "rounded_total", "status", "docstatus",
                "delivery_date",
            ],
            order_by="creation desc",
            limit=100,
        )
        for r in rows:
            r["status_label"] = "Submitted" if r.get("docstatus") == 1 else "Draft"
        return response("Today's orders", {"entries": rows, "count": len(rows)}, True, 200)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.get_my_today_orders")
        return response(str(e), None, False, 500)


@frappe.whitelist()
def get_my_today_collected(sales_person_id=None):
    """Today's Submitted Payment Entries linked to the caller. Sums to
    the same number as the 'Collected' tile.
    """
    try:
        from frappe.utils import today
        sp, err = _resolve_sp_for_detail(sales_person_id)
        if err is not None:
            return err
        today_str = today()
        rows = frappe.db.sql(
            """
            SELECT name, party, party_name, posting_date, paid_amount,
                   reference_no, mode_of_payment, docstatus
            FROM `tabPayment Entry`
            WHERE docstatus = 1
              AND DATE(posting_date) = %(d)s
              AND (custom_sales_person = %(sp)s OR owner IN (
                   SELECT user_id FROM `tabEmployee`
                   WHERE name IN (
                     SELECT employee FROM `tabSales Person` WHERE name = %(sp)s
                   )
              ))
            ORDER BY creation DESC
            LIMIT 100
            """,
            {"d": today_str, "sp": sp},
            as_dict=True,
        )
        total = sum(float(r.get("paid_amount") or 0) for r in rows)
        return response(
            "Today's collections",
            {"entries": rows, "count": len(rows), "total": total},
            True, 200,
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.get_my_today_collected")
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

        # === Shift Location preflight (2026-06-13) ===
        # HRMS's Employee Checkin.validate_distance_from_shift_location:
        #  - if HR Settings.allow_geolocation_tracking ON + no lat/long → throws
        #  - else if employee has an active Shift Assignment with shift_location
        #    set → enforces distance < Shift Location.checkin_radius
        #
        # Strategy:
        #  - OFFICE STAFF (has Shift Assignment with shift_location): GPS is
        #    MANDATORY. Reject API request with friendly 400 if no GPS sent.
        #    Then let HRMS enforce the radius automatically.
        #  - FIELD STAFF (no Shift Assignment with shift_location): GPS is
        #    OPTIONAL. If missing, write a tiny non-zero placeholder so HRMS's
        #    "lat/long required" throw doesn't fire. Radius enforcement won't
        #    run anyway (no shift_location to compare against).
        has_shift_location = bool(frappe.db.exists("Shift Assignment", {
            "employee": employee,
            "shift_location": ["is", "set"],
            "docstatus": 1,
            "status": "Active",
        }))

        if has_shift_location and (latitude is None or longitude is None):
            return response(
                "GPS coordinates are required for checkin — you are assigned "
                "to a shift location. Please enable location on your device.",
                None, False, 400,
            )

        checkin = frappe.new_doc("Employee Checkin")
        checkin.employee = employee
        checkin.log_type = log_type
        checkin.time = now_datetime()
        checkin.device_id = device_id

        # Write GPS to BOTH the standard HRMS fields (latitude/longitude,
        # used by validate_distance_from_shift_location) AND the custom
        # mirror fields (custom_latitude/custom_longitude, used by other
        # chundakadan code paths — e.g. reverse-geocode, mobile views).
        try:
            lat_f = float(latitude) if latitude is not None else None
            lon_f = float(longitude) if longitude is not None else None
        except (TypeError, ValueError):
            lat_f = lon_f = None

        # Field-staff bypass: HRMS throws on lat/long missing if
        # allow_geolocation_tracking is on. Field staff don't need GPS, so
        # write a tiny non-zero placeholder that satisfies the truthy check.
        if lat_f is None and not has_shift_location:
            lat_f = 1e-6
        if lon_f is None and not has_shift_location:
            lon_f = 1e-6

        meta = frappe.get_meta("Employee Checkin")
        if lat_f is not None:
            if meta.has_field("latitude"):
                checkin.latitude = lat_f
            if meta.has_field("custom_latitude"):
                checkin.custom_latitude = lat_f
        if lon_f is not None:
            if meta.has_field("longitude"):
                checkin.longitude = lon_f
            if meta.has_field("custom_longitude"):
                checkin.custom_longitude = lon_f

        checkin.insert(ignore_permissions=True)

        # Customer-asked behavior 2026-06-04: every mobile Check-In/Out
        # should ALSO drop a Customer Visit Log row at the same lat/long,
        # so HR can audit where employees punch in from on the existing
        # visit-log map view. The Customer Visit Log.employee field is
        # Link -> Sales Person, so non-sales-person users (HR, Admin)
        # silently skip this step — they still get the Employee Checkin.
        visit_log_name = None
        if latitude is not None and longitude is not None:
            sp = _resolve_caller_sales_person()
            if sp:
                try:
                    visit = frappe.new_doc("Customer Visit Log")
                    visit.employee = sp
                    visit.date = checkin.time.date()
                    visit.time = checkin.time.time()
                    try:
                        visit.latitude = float(latitude)
                        visit.longitude = float(longitude)
                    except (TypeError, ValueError):
                        pass
                    # customer_name is mandatory-ish per the existing
                    # log_customer_visit validation — fill with the
                    # log_type so the row reads as "Check-In" /
                    # "Check-Out" in the visit-log grid.
                    visit.customer_name = (
                        "Check-In" if log_type == "IN" else "Check-Out"
                    )
                    # visit_type is the structured filterable companion
                    # to customer_name. Custom Field auto-created by
                    # chundakadan.install.ensure_visit_log_visit_type_field.
                    # has_field guards against the field not existing yet
                    # on benches that haven't migrated.
                    visit_type_value = (
                        "Check-In" if log_type == "IN" else "Check-Out"
                    )
                    if frappe.get_meta("Customer Visit Log").has_field("visit_type"):
                        visit.visit_type = visit_type_value
                    visit.description = (
                        f"Auto-created from mobile {visit.customer_name} "
                        f"(Employee Checkin: {checkin.name})"
                    )
                    visit.insert(ignore_permissions=True)
                    visit_log_name = visit.name
                except Exception:
                    # Don't fail the checkin if the visit log fails —
                    # checkin is the primary record, visit log is the
                    # audit shadow. Log + continue.
                    frappe.log_error(
                        frappe.get_traceback(),
                        "field_sales.create_employee_checkin.visit_log",
                    )

        return response(
            "Checkin recorded",
            {
                "name": checkin.name,
                "log_type": checkin.log_type,
                "time": str(checkin.time),
                "employee": checkin.employee,
                "customer_visit_log": visit_log_name,
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
    """List active Leave Types for use in the Apply Leave form.
    Includes custom_require_certificate so the mobile can show the
    certificate uploader as required for Sick Leave (etc.) without an
    extra round trip."""
    try:
        types = frappe.get_all(
            "Leave Type",
            filters={"is_lwp": 0},
            fields=[
                "name",
                "leave_type_name",
                "max_leaves_allowed",
                "is_compensatory",
                "custom_require_certificate",
            ],
            order_by="name",
        )
        return response("Leave types", types, True, 200)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.get_leave_types")
        return response(str(e), None, False, 500)


@frappe.whitelist()
def get_my_leave_balance():
    """Return per-leave-type allocated / used / balance for the calling
    user's Employee for the current leave allocation period.

    `allocated`: SUM(total_leaves_allocated) from active Leave Allocations
    `balance`  : get_leave_balance_on() (HRMS helper — accounts for
                 already-used leaves)
    `used`     : allocated - balance (clamped to >= 0)
    """
    try:
        from frappe.utils import nowdate, getdate

        employee = _resolve_caller_employee()
        if not employee:
            return response("No Employee linked", None, False, 404)

        from hrms.hr.doctype.leave_application.leave_application import (
            get_leave_balance_on,
        )

        today = getdate(nowdate())

        # Get all active allocations grouped by leave type
        alloc_rows = frappe.db.sql(
            """
            SELECT leave_type, SUM(total_leaves_allocated) AS allocated
            FROM `tabLeave Allocation`
            WHERE employee = %s AND docstatus = 1
              AND from_date <= %s AND to_date >= %s
            GROUP BY leave_type
            """,
            (employee, today, today),
            as_dict=True,
        )

        rows = []
        # Always include all leave types so the picker has options,
        # even when the employee has no allocation yet.
        leave_types = frappe.get_all(
            "Leave Type",
            filters={"is_lwp": 0},
            fields=["name"],
            order_by="name",
        )
        alloc_dict = {r.leave_type: flt(r.allocated or 0) for r in alloc_rows}

        for lt in leave_types:
            try:
                balance = get_leave_balance_on(
                    employee=employee,
                    leave_type=lt.name,
                    date=today,
                ) or 0
            except Exception:
                balance = 0
            allocated = alloc_dict.get(lt.name, 0)
            used = max(allocated - flt(balance), 0)
            rows.append({
                "leave_type": lt.name,
                "allocated": flt(allocated),
                "used": flt(used),
                "balance": flt(balance),
            })

        return response(
            "Leave balance",
            {"employee": employee, "balances": rows, "as_of": str(today)},
            True,
            200,
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.get_my_leave_balance")
        return response(str(e), None, False, 500)


@frappe.whitelist()
def get_upcoming_holidays(limit=10):
    """Return upcoming holidays from the calling user's Employee's
    holiday_list, falling back to the company's default_holiday_list.
    Weekly offs included; UI can filter them out if undesired."""
    try:
        from frappe.utils import nowdate

        employee = _resolve_caller_employee()
        if not employee:
            return response("No Employee linked", None, False, 404)

        holiday_list = frappe.db.get_value("Employee", employee, "holiday_list")
        if not holiday_list:
            company = frappe.db.get_value("Employee", employee, "company")
            if company:
                holiday_list = frappe.db.get_value(
                    "Company", company, "default_holiday_list"
                )
        if not holiday_list:
            return response(
                "No holiday list assigned",
                {"holiday_list": None, "holidays": []},
                True,
                200,
            )

        rows = frappe.db.sql(
            """
            SELECT holiday_date, description, weekly_off
            FROM `tabHoliday`
            WHERE parent = %s AND holiday_date >= %s
            ORDER BY holiday_date ASC
            LIMIT %s
            """,
            (holiday_list, nowdate(), int(limit)),
            as_dict=True,
        )

        return response(
            "Upcoming holidays",
            {
                "holiday_list": holiday_list,
                "holidays": [
                    {
                        "holiday_date": str(r.holiday_date),
                        "description": r.description,
                        "weekly_off": bool(r.weekly_off),
                    } for r in rows
                ],
            },
            True,
            200,
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.get_upcoming_holidays")
        return response(str(e), None, False, 500)


# =====================================================================
#  EXPENSE CLAIM + EMPLOYEE ADVANCE
# =====================================================================

_EXPENSE_STATUSES = ("Draft", "Submitted", "Approved", "Rejected", "Paid", "Cancelled")


@frappe.whitelist()
def get_my_expense_summary():
    """Headline totals for the calling user's Expense Claims (current
    calendar year) — feeds the mobile summary card."""
    try:
        from frappe.utils import nowdate, getdate

        employee = _resolve_caller_employee()
        if not employee:
            return response("No Employee linked", None, False, 404)

        year = getdate(nowdate()).year
        year_start = "{}-01-01".format(year)
        year_end = "{}-12-31".format(year)

        rows = frappe.db.sql(
            """
            SELECT approval_status, SUM(total_claimed_amount) AS total
            FROM `tabExpense Claim`
            WHERE employee = %s
              AND docstatus IN (0, 1)
              AND posting_date BETWEEN %s AND %s
            GROUP BY approval_status
            """,
            (employee, year_start, year_end),
            as_dict=True,
        )

        buckets = {"Draft": 0, "Approved": 0, "Rejected": 0}
        total = 0
        for r in rows:
            amt = flt(r.total or 0)
            total += amt
            if r.approval_status in buckets:
                buckets[r.approval_status] += amt

        return response(
            "Expense summary",
            {
                "employee": employee,
                "year": year,
                "total": flt(total),
                "pending": flt(buckets["Draft"]),
                "approved": flt(buckets["Approved"]),
                "rejected": flt(buckets["Rejected"]),
            },
            True,
            200,
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.get_my_expense_summary")
        return response(str(e), None, False, 500)


@frappe.whitelist()
def get_my_expense_claims(status=None, limit=50):
    """Caller's Expense Claims, newest first, with optional status filter."""
    try:
        employee = _resolve_caller_employee()
        if not employee:
            return response("No Employee linked", None, False, 404)

        filters = {"employee": employee, "docstatus": ["in", [0, 1]]}
        if status and status in _EXPENSE_STATUSES:
            filters["approval_status"] = status

        rows = frappe.get_all(
            "Expense Claim",
            filters=filters,
            fields=[
                "name", "posting_date", "total_claimed_amount",
                "total_sanctioned_amount", "total_advance_amount",
                "total_taxes_and_charges", "grand_total",
                "approval_status", "status", "docstatus",
            ],
            order_by="posting_date desc",
            limit=int(limit),
        )
        return response(
            "Expense claims",
            {"claims": rows},
            True,
            200,
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.get_my_expense_claims")
        return response(str(e), None, False, 500)


@frappe.whitelist()
def get_expense_claim_detail(name=None):
    """Full Expense Claim detail (header + expense lines). Privacy guard:
    refuses if the claim doesn't belong to the caller (unless caller is
    the listed expense_approver)."""
    try:
        if not name:
            return response("name is required", None, False, 400)

        employee = _resolve_caller_employee()
        if not employee:
            return response("No Employee linked", None, False, 404)

        doc = frappe.get_doc("Expense Claim", name)
        if doc.employee != employee and doc.expense_approver != frappe.session.user:
            return response(
                "You can only view your own expense claims",
                None,
                False,
                403,
            )

        return response(
            "Expense claim detail",
            {
                "name": doc.name,
                "employee": doc.employee,
                "employee_name": doc.employee_name,
                "posting_date": str(doc.posting_date) if doc.posting_date else None,
                "company": doc.company,
                "approval_status": doc.approval_status,
                "status": doc.status,
                "docstatus": doc.docstatus,
                "total_claimed_amount": flt(doc.total_claimed_amount),
                "total_sanctioned_amount": flt(doc.total_sanctioned_amount),
                "total_taxes_and_charges": flt(doc.total_taxes_and_charges),
                "total_advance_amount": flt(doc.total_advance_amount),
                "grand_total": flt(doc.grand_total),
                "expense_approver": doc.expense_approver,
                "expenses": [
                    {
                        "expense_date": str(e.expense_date) if e.expense_date else None,
                        "expense_type": e.expense_type,
                        "description": e.description,
                        "amount": flt(e.amount),
                        "sanctioned_amount": flt(e.sanctioned_amount),
                    } for e in (doc.expenses or [])
                ],
                "taxes": [
                    {
                        "account_head": t.account_head,
                        "description": t.description,
                        "rate": flt(t.rate),
                        "tax_amount": flt(t.tax_amount),
                    } for t in (doc.taxes or [])
                ],
                "attachments": [
                    {"file_url": f.file_url, "file_name": f.file_name}
                    for f in frappe.get_all(
                        "File",
                        filters={"attached_to_doctype": "Expense Claim",
                                 "attached_to_name": doc.name},
                        fields=["file_url", "file_name"],
                    )
                ],
            },
            True,
            200,
        )
    except frappe.DoesNotExistError:
        return response("Expense Claim not found", None, False, 404)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.get_expense_claim_detail")
        return response(str(e), None, False, 500)


@frappe.whitelist()
def get_expense_claim_types():
    """List Expense Claim Types for the form picker."""
    try:
        rows = frappe.get_all("Expense Claim Type", fields=["name"], order_by="name")
        return response("Expense claim types", {"types": rows}, True, 200)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.get_expense_claim_types")
        return response(str(e), None, False, 500)


@frappe.whitelist(methods=["POST"])
def create_expense_claim(
    posting_date=None,
    expenses=None,
    company=None,
    remark=None,
    submit=False,
):
    """Create (and optionally submit) an Expense Claim for the calling
    user. `expenses` is a list of {expense_date, expense_type,
    description, amount} dicts."""
    try:
        data = frappe.request.get_json() or {}
        posting_date = posting_date or data.get("posting_date")
        expenses = expenses if expenses is not None else data.get("expenses", [])
        company = company or data.get("company")
        remark = remark or data.get("remark")
        submit_flag = data.get("submit", submit) if isinstance(submit, bool) else submit

        employee = _resolve_caller_employee()
        if not employee:
            return response("No Employee linked", None, False, 404)
        if not expenses or not isinstance(expenses, list):
            return response("At least one expense line is required", None, False, 400)

        emp = frappe.get_doc("Employee", employee)
        if not company:
            company = emp.company or _resolve_company_for_caller()

        doc = frappe.new_doc("Expense Claim")
        doc.employee = employee
        doc.company = company
        doc.posting_date = frappe.utils.getdate(posting_date) if posting_date else frappe.utils.nowdate()
        if emp.expense_approver:
            doc.expense_approver = emp.expense_approver
        if remark:
            doc.remark = remark

        for line in expenses:
            doc.append("expenses", {
                "expense_date": frappe.utils.getdate(line.get("expense_date")) if line.get("expense_date") else doc.posting_date,
                "expense_type": line.get("expense_type"),
                "description": line.get("description") or "",
                "amount": flt(line.get("amount", 0)),
                "sanctioned_amount": flt(line.get("amount", 0)),
            })

        doc.flags.ignore_mandatory = True
        doc.insert(ignore_permissions=True)
        if submit_flag:
            try:
                doc.submit()
            except Exception:
                frappe.log_error(
                    frappe.get_traceback(),
                    "field_sales.create_expense_claim.submit",
                )

        return response(
            "Expense Claim created",
            {
                "name": doc.name,
                "approval_status": doc.approval_status,
                "docstatus": doc.docstatus,
                "total_claimed_amount": flt(doc.total_claimed_amount),
            },
            True,
            200,
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.create_expense_claim")
        return response(str(e), None, False, 500)


@frappe.whitelist()
def get_pending_expense_approvals():
    """Expense Claims awaiting the calling user's approval
    (expense_approver = session user, approval_status = Draft,
    docstatus = 1)."""
    try:
        user = frappe.session.user
        if not user or user == "Guest":
            return response("Authentication required", None, False, 401)

        rows = frappe.get_all(
            "Expense Claim",
            filters={
                "expense_approver": user,
                "approval_status": "Draft",
                "docstatus": 1,
            },
            fields=[
                "name", "employee", "employee_name", "posting_date",
                "total_claimed_amount", "company",
            ],
            order_by="posting_date asc",
        )
        return response("Pending expense approvals", {"approvals": rows}, True, 200)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.get_pending_expense_approvals")
        return response(str(e), None, False, 500)


@frappe.whitelist(methods=["POST"])
def act_on_expense_claim(name=None, action=None, reason=None):
    """Approve or Reject an Expense Claim. Caller must be the doc's
    expense_approver. action: 'Approved' or 'Rejected'."""
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
        doc = frappe.get_doc("Expense Claim", name)
        if doc.expense_approver and doc.expense_approver != user:
            return response(
                "You are not the expense approver for this claim",
                None,
                False,
                403,
            )

        doc.approval_status = action
        if reason:
            doc.remark = (doc.remark or "") + "\n\n[Approver note] " + reason

        if doc.docstatus == 0:
            doc.submit()
        else:
            doc.save(ignore_permissions=True)

        return response(
            "Expense Claim {}".format(action.lower()),
            {"name": doc.name, "approval_status": doc.approval_status},
            True,
            200,
        )
    except frappe.DoesNotExistError:
        return response("Expense Claim not found", None, False, 404)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.act_on_expense_claim")
        return response(str(e), None, False, 500)


@frappe.whitelist()
def get_my_employee_advances():
    """Caller's Employee Advances — paid_amount / advance_amount."""
    try:
        employee = _resolve_caller_employee()
        if not employee:
            return response("No Employee linked", None, False, 404)

        rows = frappe.get_all(
            "Employee Advance",
            filters={"employee": employee, "docstatus": ["in", [0, 1]]},
            fields=[
                "name", "purpose", "advance_amount", "paid_amount",
                "claimed_amount", "return_amount", "status",
                "posting_date", "advance_account",
            ],
            order_by="posting_date desc",
            limit=20,
        )
        return response("Employee advances", {"advances": rows}, True, 200)
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.get_my_employee_advances")
        return response(str(e), None, False, 500)


@frappe.whitelist(methods=["POST"])
def request_employee_advance(
    advance_amount=None,
    purpose=None,
    posting_date=None,
):
    """Submit an Employee Advance request for the calling user."""
    try:
        data = frappe.request.get_json() or {}
        advance_amount = advance_amount or data.get("advance_amount")
        purpose = purpose or data.get("purpose")
        posting_date = posting_date or data.get("posting_date")

        if not advance_amount or flt(advance_amount) <= 0:
            return response("advance_amount must be > 0", None, False, 400)

        employee = _resolve_caller_employee()
        if not employee:
            return response("No Employee linked", None, False, 404)

        emp = frappe.get_doc("Employee", employee)
        company = emp.company or _resolve_company_for_caller()

        doc = frappe.new_doc("Employee Advance")
        doc.employee = employee
        doc.company = company
        doc.purpose = purpose or "Advance request via mobile"
        doc.advance_amount = flt(advance_amount)
        doc.posting_date = frappe.utils.getdate(posting_date) if posting_date else frappe.utils.nowdate()
        doc.flags.ignore_mandatory = True
        doc.insert(ignore_permissions=True)

        return response(
            "Advance requested",
            {
                "name": doc.name,
                "advance_amount": flt(doc.advance_amount),
                "status": doc.status,
            },
            True,
            200,
        )
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "field_sales.request_employee_advance")
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
    medical_certificate=None,
):
    """Create + submit a Leave Application for the calling user.

    medical_certificate, when provided, is a file URL returned by
    Frappe's /api/method/upload_file endpoint (e.g. /private/files/abc.pdf).
    Required when the selected Leave Type has custom_require_certificate
    flagged — chundakadan.chundakadan.api.leave.validate_leave enforces
    that on save; we just pass the URL through here.
    """
    try:
        data = frappe.request.get_json() or {}
        leave_type = leave_type or data.get("leave_type")
        from_date = from_date or data.get("from_date")
        to_date = to_date or data.get("to_date")
        half_day = half_day if half_day else data.get("half_day", 0)
        half_day_date = half_day_date or data.get("half_day_date")
        description = description or data.get("description")
        medical_certificate = medical_certificate or data.get("medical_certificate")

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
        if medical_certificate:
            doc.custom_medical_certificate = medical_certificate
        if leave_approver:
            doc.leave_approver = leave_approver
        doc.status = "Open"
        doc.insert(ignore_permissions=True)
        # Do NOT auto-submit. chundakadan's multi-step chain advances
        # the doc while it stays at docstatus=0 (Draft). The final
        # approver's click in chundakadan.api.leave.approve_leave is
        # what actually submits, which is when leave balance is
        # consumed and the doc becomes immutable. Until then it can be
        # rerouted, edited, or rejected without leaking ledger entries.

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

    Uses chundakadan's multi-step chain (current_approver field on
    Leave Application, populated by chundakadan.chundakadan.api.leave.
    generate_approval_flow). Falls back to the standard leave_approver
    field for leaves created before the multi-step flow was wired.

    Status filter: Open OR Pending (chundakadan flow keeps doc Open
    while moving through the chain; standard sets it to Open while
    waiting on leave_approver). docstatus: 0 (drafts mid-flow) or 1.
    """
    try:
        user = frappe.session.user
        if not user or user == "Guest":
            return response("Authentication required", None, False, 401)

        # Match leave.py:_caller_can_act_on policy. A leave is "pending
        # for me" if ANY of:
        #   - current_approver = me (resolved user)
        #   - leave_approver = me (standard ERPNext designated field)
        #   - I hold the role of the current step (approval_flow row at
        #     idx = current_approval_index + 1, since Frappe child idx
        #     is 1-based while current_approval_index is 0-based)
        roles = frappe.get_roles(user) or ["__noroles__"]
        rows = frappe.db.sql(
            """
            SELECT la.name, la.employee, la.employee_name, la.leave_type,
                   la.from_date, la.to_date, la.half_day, la.total_leave_days,
                   la.description, la.posting_date,
                   la.current_approver, la.leave_approver,
                   la.custom_approval_status, la.status
            FROM `tabLeave Application` la
            WHERE (
                la.current_approver = %(user)s
                OR la.leave_approver = %(user)s
                OR EXISTS (
                    SELECT 1
                    FROM `tabLeave Approval Detail` flow
                    WHERE flow.parent = la.name
                      AND flow.parenttype = 'Leave Application'
                      AND flow.idx = COALESCE(la.current_approval_index, 0) + 1
                      AND flow.approver_role IN %(roles)s
                )
            )
              AND la.docstatus IN (0, 1)
              AND COALESCE(la.custom_approval_status, '') NOT IN ('Approved', 'Rejected')
              AND la.status IN ('Open', 'Pending')
            ORDER BY la.from_date ASC
            """,
            {"user": user, "roles": tuple(roles)},
            as_dict=True,
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
    """Approve or reject a Leave Application via chundakadan's multi-step
    workflow. action must be 'Approved' or 'Rejected'.

    Delegates to chundakadan.chundakadan.api.leave.approve_leave /
    reject_leave so the chain advances correctly: an Approved click at
    step 1 routes the doc to step 2, not straight to final Approved.
    """
    try:
        data = frappe.request.get_json() or {}
        name = name or data.get("name")
        action = action or data.get("action")
        reason = reason or data.get("reason")

        if action not in ("Approved", "Rejected"):
            return response("action must be Approved or Rejected", None, False, 400)
        if not name:
            return response("name is required", None, False, 400)

        # Delegate to chundakadan's chain-aware handlers. They do their
        # own authorization checks (current_approver match) and throw
        # frappe.PermissionError if the caller is not the right approver.
        try:
            from chundakadan.chundakadan.api.leave import (
                approve_leave as _approve,
                reject_leave as _reject,
            )
            if action == "Approved":
                _approve(name)
            else:
                _reject(name, remarks=reason)
        except ImportError:
            # chundakadan not installed (shouldn't happen on this bench)
            # — fall back to the old single-step behaviour.
            doc = frappe.get_doc("Leave Application", name)
            user = frappe.session.user
            if doc.leave_approver and doc.leave_approver != user:
                return response(
                    "You are not the leave approver for this application",
                    None,
                    False,
                    403,
                )
            doc.status = action
            if reason:
                doc.description = (doc.description or "") + "\n\n[Approver note] " + reason
            if doc.docstatus == 1:
                doc.save(ignore_permissions=True)
            else:
                doc.submit()

        # Re-read for the response so the client sees the post-action state
        doc = frappe.get_doc("Leave Application", name)
        return response(
            "Leave {}".format(action.lower()),
            {
                "name": doc.name,
                "status": doc.status,
                "custom_approval_status": doc.get("custom_approval_status"),
                "current_approver": doc.get("current_approver"),
            },
            True,
            200,
        )
    except frappe.PermissionError as e:
        return response(str(e) or "Not authorized", None, False, 403)
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

        