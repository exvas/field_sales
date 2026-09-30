"""Who sees every executive's entries on mobile.

A manager named in Chundakadan Settings -- either by role or by a Manager
Details row -- gets the whole team's lists instead of their own. The point
of putting it in Settings is that replacing the manager is a configuration
change, never a code change.
"""

import unittest

import frappe

from field_sales.Api.auth import _caller_has_view_all_role, _with_sales_person

ROLE = "View All Txn Test Role"
MANAGER = "viewall.manager@example.com"
PLAIN = "viewall.plain@example.com"


class TestFilterHelper(unittest.TestCase):
	def test_a_named_sales_person_is_always_filtered(self):
		self.assertEqual(
			_with_sales_person({"docstatus": 1}, "Razeel"),
			{"docstatus": 1, "custom_sales_person": "Razeel"},
		)

	def test_no_sales_person_leaves_the_filter_open(self):
		for blank in (None, ""):
			self.assertEqual(_with_sales_person({"docstatus": 1}, blank), {"docstatus": 1})

	def test_the_field_name_can_differ(self):
		self.assertEqual(
			_with_sales_person({}, "Razeel", "sales_person"), {"sales_person": "Razeel"}
		)

	def test_it_does_not_disturb_the_other_filters(self):
		filters = {"party_type": "Customer", "party": "CUST-1"}
		out = _with_sales_person(filters, "Razeel")
		self.assertEqual(out["party"], "CUST-1")
		self.assertEqual(out["party_type"], "Customer")


class TestWhoGetsTheBypass(unittest.TestCase):
	def setUp(self):
		# fixtures live in setUp, not setUpClass: tearDown rolls the
		# transaction back and would take a class-level fixture with it
		frappe.set_user("Administrator")
		if not frappe.db.exists("Role", ROLE):
			frappe.get_doc({"doctype": "Role", "role_name": ROLE, "desk_access": 1}).insert()
		for email in (MANAGER, PLAIN):
			if not frappe.db.exists("User", email):
				frappe.get_doc({
					"doctype": "User", "email": email, "first_name": email.split("@")[0],
					"send_welcome_email": 0, "user_type": "System User",
				}).insert()
		frappe.get_doc("User", MANAGER).add_roles(ROLE)
		for email in (MANAGER, PLAIN):
			frappe.clear_cache(user=email)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def _configure(self, role):
		frappe.db.set_single_value("Chundakadan Settings", "view_all_transaction_role", role or "")

	def test_the_configured_role_gets_everything(self):
		self._configure(ROLE)
		frappe.set_user(MANAGER)
		self.assertTrue(_caller_has_view_all_role())

	def test_everybody_else_stays_on_their_own_list(self):
		self._configure(ROLE)
		frappe.set_user(PLAIN)
		self.assertFalse(_caller_has_view_all_role())

	def test_no_role_configured_means_nobody_is_let_through(self):
		self._configure(None)
		frappe.set_user(MANAGER)
		self.assertFalse(_caller_has_view_all_role())
		frappe.set_user(PLAIN)
		self.assertFalse(_caller_has_view_all_role())

	def test_changing_the_configured_role_moves_the_privilege(self):
		"""Replacing the manager must be a Settings edit, not a code change."""
		self._configure(ROLE)
		frappe.set_user(MANAGER)
		self.assertTrue(_caller_has_view_all_role())
		frappe.set_user("Administrator")
		self._configure("Some Other Role")
		frappe.set_user(MANAGER)
		self.assertFalse(_caller_has_view_all_role())

	def test_administrator_always_sees_everything(self):
		self._configure(None)
		frappe.set_user("Administrator")
		self.assertTrue(_caller_has_view_all_role())

	def test_guest_never_does(self):
		self._configure(ROLE)
		frappe.set_user("Guest")
		self.assertFalse(_caller_has_view_all_role())


if __name__ == "__main__":
	unittest.main()
