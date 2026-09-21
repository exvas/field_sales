from types import SimpleNamespace

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, flt, nowdate

from field_sales.Api import auth

COMPANY = "Chundakadan Agencies"


class TestPostDatedChequeApi(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		if not frappe.db.exists("DocType", "Post Dated Cheque"):
			self.skipTest("Post Dated Cheque not installed on this site")
		invoice = frappe.get_all(
			"Sales Invoice",
			filters={"docstatus": 1, "is_return": 0, "company": COMPANY, "custom_sales_person": ["is", "set"]},
			fields=["name", "customer", "custom_sales_person", "outstanding_amount"],
			limit=1,
		)
		if not invoice:
			self.skipTest("no invoice with a sales person")
		self.invoice = invoice[0]

	def tearDown(self):
		frappe.local.request = None
		frappe.db.rollback()

	def _cheque(self, **values):
		doc = frappe.get_doc({
			"doctype": "Post Dated Cheque",
			"company": COMPANY,
			"customer": self.invoice.customer,
			"posting_date": nowdate(),
			"cheque_no": frappe.generate_hash(length=8),
			"cheque_date": add_days(nowdate(), 10),
			"amount": 5000,
			"bank_name": "SBI",
			"sales_person": self.invoice.custom_sales_person,
			**values,
		})
		doc.insert()
		doc.submit()
		return doc

	def _call(self, **args):
		frappe.local.request = SimpleNamespace(args={"sales_person": self.invoice.custom_sales_person, **args})
		return auth.get_post_dated_cheques()

	def test_missing_sales_person(self):
		frappe.local.request = SimpleNamespace(args={})
		self.assertEqual(auth.get_post_dated_cheques()["status"], "error")

	def test_lists_pending_cheques_with_details(self):
		doc = self._cheque(references=[{"sales_invoice": self.invoice.name, "allocated_amount": 1000}])
		out = self._call()
		row = next(c for c in out["cheques"] if c["name"] == doc.name)
		self.assertEqual(row["status"], "Pending")
		self.assertEqual(row["cheque_no"], doc.cheque_no)
		self.assertEqual(flt(row["amount"]), 5000)
		self.assertEqual(row["days_to_due"], 10)
		self.assertEqual(row["invoices"][0]["sales_invoice"], self.invoice.name)
		self.assertEqual(out["cheque_count"], len([c for c in out["cheques"]]))

	def test_only_that_sales_persons_cheques(self):
		other = frappe.db.get_value("Sales Person", {"name": ["!=", self.invoice.custom_sales_person], "enabled": 1}, "name")
		if not other:
			self.skipTest("only one sales person")
		mine = self._cheque()
		theirs = self._cheque(sales_person=other)
		names = [c["name"] for c in self._call()["cheques"]]
		self.assertIn(mine.name, names)
		self.assertNotIn(theirs.name, names)

	def test_status_filter(self):
		from chundakadan.chundakadan.doctype.post_dated_cheque.post_dated_cheque import mark_bounced

		doc = self._cheque()
		mark_bounced(doc.name, reason="x")
		self.assertNotIn(doc.name, [c["name"] for c in self._call()["cheques"]])
		self.assertIn(doc.name, [c["name"] for c in self._call(status="Bounced")["cheques"]])
		self.assertIn(doc.name, [c["name"] for c in self._call(status="All")["cheques"]])
