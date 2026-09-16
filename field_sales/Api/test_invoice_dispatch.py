from types import SimpleNamespace

import frappe
from frappe.tests.utils import FrappeTestCase

from field_sales.Api import auth


class TestInvoiceDispatch(FrappeTestCase):
	def setUp(self):
		self.invoice = frappe.get_all(
			"Sales Invoice",
			filters={"docstatus": 1, "is_return": 0, "custom_sales_person": ["is", "set"]},
			fields=["name", "custom_sales_person"],
			order_by="creation desc",
			limit=1,
		)[0]
		frappe.db.delete("Dispatch Log", {"sales_invoice": self.invoice.name})

	def tearDown(self):
		frappe.local.request = None
		frappe.db.rollback()

	def _log(self, **values):
		log = frappe.get_doc({
			"doctype": "Dispatch Log",
			"sales_invoice": self.invoice.name,
			"dispatch_status": "Dispatched",
			"vehicle_no": "KL10AB1234",
			"lr_no": "LR-77",
			"driver_name": "Manu",
			"dispatched_on": "2026-09-16 10:00:00",
			"expected_delivery_date": "2026-09-17",
			**values,
		})
		log.flags.ignore_validate = True
		log.flags.ignore_links = True
		log.db_insert()
		return log

	def _list_row(self):
		frappe.local.request = SimpleNamespace(args={"sales_person": self.invoice.custom_sales_person})
		out = auth.get_sales_invoice_list()
		return next(r for r in out["invoices"] if r["invoice_id"] == self.invoice.name)

	def test_list_without_log_returns_null_dispatch(self):
		self.assertIsNone(self._list_row()["dispatch"])

	def test_list_includes_dispatch_details(self):
		self._log()
		dispatch = self._list_row()["dispatch"]
		self.assertEqual(dispatch["dispatch_status"], "Dispatched")
		self.assertEqual(dispatch["vehicle_no"], "KL10AB1234")
		self.assertEqual(dispatch["lr_no"], "LR-77")
		self.assertEqual(str(dispatch["expected_delivery_date"]), "2026-09-17")
		self.assertIn("transporter_name", dispatch)
		self.assertNotIn("sales_invoice", dispatch)

	def test_detail_includes_dispatch(self):
		self._log(dispatch_status="Pending", pending_reason="Stock Not Available")
		frappe.form_dict.invoice_id = self.invoice.name
		out = auth.sales_invoice_detail_by_ids()
		self.assertEqual(out["status"], "success")
		self.assertEqual(out["data"]["dispatch"]["dispatch_status"], "Pending")
		self.assertEqual(out["data"]["dispatch"]["pending_reason"], "Stock Not Available")

	def test_map_empty_input(self):
		self.assertEqual(auth._dispatch_info_map([]), {})
