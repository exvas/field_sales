"""Cheque Bounce — records a returned cheque and runs the three accounting
actions atomically:

  1. Cancel the original Payment Entry (restores Customer outstanding).
  2. Create a Journal Entry for the bank's bounce fee
     (Dr Bank Charges, Cr Bank).
  3. If `charge_to_customer` is set, create a second Journal Entry to
     recover that fee from the customer (Dr Customer, Cr Cheque Bounce
     Income).

The doc itself is submittable. On submit the three actions run inside one
transaction so a failure in any step rolls back the others. The created
docs are linked back to the Cheque Bounce row for audit.
"""

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, nowdate


class ChequeBounce(Document):
    def validate(self):
        if not self.bounce_date:
            self.bounce_date = nowdate()

        if flt(self.bounce_charge_amount) < 0:
            frappe.throw(_("Bounce Charge Amount cannot be negative."))

        if self.charge_to_customer and not self.cheque_bounce_income_account:
            frappe.throw(
                _("Cheque Bounce Income Account is required when Charge to Customer is checked.")
            )

        pe = frappe.get_doc("Payment Entry", self.payment_entry)
        if pe.docstatus != 1:
            frappe.throw(
                _("Payment Entry {0} must be Submitted before reporting a bounce.").format(
                    self.payment_entry
                )
            )
        if pe.payment_type != "Receive":
            frappe.throw(
                _("Cheque Bounce only applies to incoming (Receive) Payment Entries.")
            )
        if (pe.mode_of_payment or "").lower() not in ("cheque", "bank draft"):
            frappe.msgprint(
                _("Warning: Payment Entry {0} mode of payment is '{1}', not Cheque. Proceeding anyway.").format(
                    self.payment_entry, pe.mode_of_payment or "(blank)"
                ),
                indicator="orange",
                alert=True,
            )

    def on_submit(self):
        pe = frappe.get_doc("Payment Entry", self.payment_entry)

        # Step 1: cancel the PE. Frappe will refuse if it's reconciled with
        # invoices or has downstream submitted docs — that's the right
        # behaviour, surface the error to the user with context.
        try:
            pe.cancel()
            self.db_set("cancelled_payment_entry", pe.name)
        except frappe.LinkExistsError as e:
            frappe.throw(
                _(
                    "Cannot cancel Payment Entry {0} — it is linked to other submitted documents "
                    "(invoice reconciliation, etc.). Unreconcile it first, then submit this Cheque Bounce. "
                    "Details: {1}"
                ).format(self.payment_entry, str(e))
            )

        # Step 2: bank charges JE
        bank_je = self._make_bank_charge_je(pe)
        self.db_set("bank_charge_journal_entry", bank_je.name)

        # Step 3: customer recovery JE (optional)
        if self.charge_to_customer:
            cust_je = self._make_customer_debit_je(pe)
            self.db_set("customer_debit_journal_entry", cust_je.name)

        self._bump_customer_bounce_count()

        frappe.msgprint(
            _(
                "Cheque Bounce recorded. Payment Entry {0} cancelled. "
                "Bank charge JE: {1}. Customer debit JE: {2}."
            ).format(
                pe.name,
                self.bank_charge_journal_entry,
                self.customer_debit_journal_entry or "(skipped)",
            ),
            indicator="green",
            alert=True,
        )

    def on_cancel(self):
        # If the user cancels the Cheque Bounce, the linked JEs should be
        # cancelled too (so the books stay consistent). The original PE
        # cancellation is NOT reversed automatically — restoring a cancelled
        # PE means amending it, which is a separate manual decision.
        for fieldname in ("bank_charge_journal_entry", "customer_debit_journal_entry"):
            je_name = self.get(fieldname)
            if je_name and frappe.db.exists("Journal Entry", je_name):
                je = frappe.get_doc("Journal Entry", je_name)
                if je.docstatus == 1:
                    try:
                        je.cancel()
                    except Exception:
                        frappe.log_error(
                            frappe.get_traceback(),
                            "field_sales.cheque_bounce.on_cancel",
                        )

    # ----- helpers -----------------------------------------------------

    def _make_bank_charge_je(self, pe):
        """Dr Bank Charges, Cr Bank — books the fee as expense."""
        je = frappe.new_doc("Journal Entry")
        je.voucher_type = "Bank Entry"
        je.posting_date = self.bounce_date or nowdate()
        je.company = pe.company
        je.user_remark = "Cheque bounce charge for {0} (cheque {1})".format(
            pe.name, self.cheque_no or "?"
        )

        je.append("accounts", {
            "account": self.bank_charges_account,
            "debit_in_account_currency": flt(self.bounce_charge_amount),
            "credit_in_account_currency": 0,
        })
        je.append("accounts", {
            "account": self.bank_account,
            "debit_in_account_currency": 0,
            "credit_in_account_currency": flt(self.bounce_charge_amount),
        })

        je.insert(ignore_permissions=True)
        je.submit()
        return je

    def _make_customer_debit_je(self, pe):
        """Dr Customer, Cr Cheque Bounce Income — passes the fee to customer.

        The customer side requires `party_type=Customer` and `party=<name>`
        so it shows up on the customer's statement and outstanding.
        """
        # Resolve the Receivable account for this customer + company.
        receivable_account = pe.paid_from  # the receivable account the PE was crediting
        if not receivable_account:
            receivable_account = frappe.db.get_value(
                "Company", pe.company, "default_receivable_account"
            )
        if not receivable_account:
            frappe.throw(
                _("Could not determine a Receivable account for company {0}.").format(pe.company)
            )

        je = frappe.new_doc("Journal Entry")
        je.voucher_type = "Debit Note"
        je.posting_date = self.bounce_date or nowdate()
        je.company = pe.company
        je.user_remark = "Cheque bounce charge recovery from {0} (cheque {1})".format(
            self.customer, self.cheque_no or "?"
        )

        je.append("accounts", {
            "account": receivable_account,
            "party_type": "Customer",
            "party": self.customer,
            "debit_in_account_currency": flt(self.bounce_charge_amount),
            "credit_in_account_currency": 0,
        })
        je.append("accounts", {
            "account": self.cheque_bounce_income_account,
            "debit_in_account_currency": 0,
            "credit_in_account_currency": flt(self.bounce_charge_amount),
        })

        je.insert(ignore_permissions=True)
        je.submit()
        return je

    def _bump_customer_bounce_count(self):
        """Increment the Customer's custom_cheque_bounce_count if the
        field exists (added by patch v1_1.add_customer_bounce_count).
        Silently no-op if the field is missing."""
        try:
            if not frappe.get_meta("Customer").has_field("custom_cheque_bounce_count"):
                return
            current = (
                frappe.db.get_value("Customer", self.customer, "custom_cheque_bounce_count")
                or 0
            )
            frappe.db.set_value(
                "Customer",
                self.customer,
                "custom_cheque_bounce_count",
                int(current) + 1,
            )
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                "field_sales.cheque_bounce.bump_customer_count",
            )
