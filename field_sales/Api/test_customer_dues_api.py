"""The app's due list: same report as the desk, and nobody sees another
executive's customers."""

from types import SimpleNamespace
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import flt, today

from field_sales.Api import auth


class TestCustomerDuesApi(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		try:
			from chundakadan.testing import a_company, a_customer, a_stock_item, a_warehouse
		except ImportError:
			self.skipTest("chundakadan is not installed on this site")
		self.company = a_company()
		self.customer = a_customer(self.company) if self.company else None
		self.item = a_stock_item()
		self.warehouse = a_warehouse(self.company) if self.company else None
		if not (self.company and self.customer and self.item):
			self.skipTest("this bench cannot build a Sales Invoice")
		self.people = self._two_sales_people()
		self._clear_previous()
		self._invoice(1000, self.people[0])
		self._invoice(4000, self.people[1])

	def tearDown(self):
		frappe.local.request = None
		frappe.db.rollback()

	def _clear_previous(self):
		names = frappe.get_all("Sales Invoice", filters={"customer": self.customer}, pluck="name")
		if names:
			frappe.db.delete("GL Entry", {"voucher_type": "Sales Invoice", "voucher_no": ["in", names]})
			frappe.db.delete("Sales Invoice Item", {"parent": ["in", names]})
			frappe.db.delete("Sales Invoice", {"name": ["in", names]})
		receipts = frappe.get_all("Payment Entry", filters={"party": self.customer}, pluck="name")
		if receipts:
			frappe.db.delete("GL Entry", {"voucher_type": "Payment Entry", "voucher_no": ["in", receipts]})
			frappe.db.delete("Payment Entry Reference", {"parent": ["in", receipts]})
			frappe.db.delete("Payment Entry", {"name": ["in", receipts]})

	def _two_sales_people(self):
		names = [
			n
			for n in frappe.get_all("Sales Person", filters={"enabled": 1}, pluck="name", order_by="name asc")
			if n
		][:2]
		while len(names) < 2:
			doc = frappe.get_doc(
				{
					"doctype": "Sales Person",
					"sales_person_name": f"_Test Dues Api {len(names)}",
					"is_group": 0,
				}
			)
			doc.flags.ignore_mandatory = True
			doc.insert(ignore_permissions=True)
			names.append(doc.name)
		return names

	def _invoice(self, amount, sales_person):
		doc = frappe.get_doc(
			{
				"doctype": "Sales Invoice",
				"customer": self.customer,
				"company": self.company,
				"currency": frappe.get_cached_value("Company", self.company, "default_currency"),
				"conversion_rate": 1,
				"posting_date": today(),
				"set_posting_time": 1,
				"due_date": today(),
				"custom_sales_person": sales_person,
				"custom_ignore_overdue_restriction": 1,
				"items": [
					{"item_code": self.item, "qty": 1, "rate": amount, "warehouse": self.warehouse}
				],
			}
		)
		doc.flags.ignore_mandatory = True
		doc.insert(ignore_permissions=True)
		doc.submit()
		return doc

	def _call(self, view_all=True, own=None, **args):
		# response() writes into frappe.local.response and returns nothing,
		# the way every endpoint in this module does
		frappe.local.request = SimpleNamespace(args={"company": self.company, **args})
		frappe.local.response = frappe._dict()
		with (
			patch.object(auth, "_caller_has_view_all_role", return_value=view_all),
			patch.object(auth, "_resolve_caller_sales_person", return_value=own),
		):
			auth.get_customer_dues()
		return frappe.local.response

	def _rows(self, payload):
		self.assertIsNotNone(payload.get("data"), payload.get("message"))
		return payload["data"]["rows"]

	def test_a_manager_sees_the_whole_team(self):
		rows = self._rows(self._call(customer=self.customer))
		self.assertEqual(flt(sum(r["due"] for r in rows), 2), 5000)

	def test_a_salesman_sees_only_their_own(self):
		"""The gate that matters: an executive must not be shown another
		executive's customers or their money."""
		rows = self._rows(self._call(view_all=False, own=self.people[0], customer=self.customer))
		self.assertEqual(flt(sum(r["due"] for r in rows), 2), 1000)
		self.assertEqual({r["sales_person"] for r in rows}, {self.people[0]})

	def test_a_salesman_cannot_ask_for_somebody_else(self):
		"""Their own sales person is forced on after the query params are
		read, so passing another name changes nothing."""
		rows = self._rows(
			self._call(
				view_all=False,
				own=self.people[0],
				customer=self.customer,
				sales_person=self.people[1],
			)
		)
		self.assertEqual(flt(sum(r["due"] for r in rows), 2), 1000)

	def test_a_login_with_no_sales_person_is_refused(self):
		payload = self._call(view_all=False, own=None)
		self.assertEqual(payload["http_status_code"], 404)

	def test_a_manager_can_narrow_to_one_executive(self):
		rows = self._rows(self._call(customer=self.customer, sales_person=self.people[1]))
		self.assertEqual(flt(sum(r["due"] for r in rows), 2), 4000)

	def test_the_totals_describe_the_rows(self):
		payload = self._call(customer=self.customer)
		totals = payload["data"]["totals"]
		rows = self._rows(payload)
		self.assertEqual(flt(totals["due"], 2), flt(sum(r["due"] for r in rows), 2))
		self.assertEqual(totals["customers"], len({r["customer"] for r in rows}))

	def test_detail_gives_a_row_per_invoice(self):
		payload = self._call(customer=self.customer, detail="1")
		self.assertTrue(payload["data"]["detail"])
		rows = self._rows(payload)
		self.assertEqual(len(rows), 2)
		self.assertIn("invoice", rows[0])
		self.assertEqual(flt(payload["data"]["totals"]["due"], 2), 5000)

	def test_detail_obeys_the_same_gate(self):
		rows = self._rows(
			self._call(view_all=False, own=self.people[0], customer=self.customer, detail="1")
		)
		self.assertEqual({r["sales_person"] for r in rows}, {self.people[0]})

	def test_the_total_is_the_due_not_the_raw_outstanding(self):
		"""A receipt nobody put against an invoice leaves every invoice
		where it was. Totalling the invoices would send an executive after
		money the customer has already paid -- the A K Trade Links case."""
		receivable = frappe.get_cached_value("Company", self.company, "default_receivable_account")
		bank = frappe.db.get_value(
			"Account",
			{"company": self.company, "is_group": 0, "account_type": ["in", ["Bank", "Cash"]]},
			"name",
			order_by="name asc",
		)
		if not (receivable and bank):
			self.skipTest("this bench cannot build a Payment Entry")
		receipt = frappe.get_doc(
			{
				"doctype": "Payment Entry",
				"payment_type": "Receive",
				"company": self.company,
				"posting_date": today(),
				"party_type": "Customer",
				"party": self.customer,
				"paid_from": receivable,
				"paid_to": bank,
				"paid_amount": 1500,
				"received_amount": 1500,
				"source_exchange_rate": 1,
				"target_exchange_rate": 1,
				"reference_no": frappe.generate_hash(length=6),
				"reference_date": today(),
				"custom_sales_person": self.people[0],
			}
		)
		receipt.flags.ignore_mandatory = True
		receipt.insert(ignore_permissions=True)
		receipt.submit()

		totals = self._call(customer=self.customer)["data"]["totals"]
		self.assertEqual(flt(totals["outstanding"], 2), 5000)
		self.assertEqual(flt(totals["advance"], 2), 1500)
		self.assertEqual(flt(totals["due"], 2), 3500)
