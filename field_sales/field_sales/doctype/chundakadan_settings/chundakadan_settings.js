// Copyright (c) 2025, vijila@teambackoffice.com and contributors
// For license information, please see license.txt

// MOP mapping grid — narrow the Account dropdown and auto-fetch the
// default when Mode of Payment is picked. Without this the user sees
// thousands of GL accounts and has to guess which one matches the mode.

frappe.ui.form.on('Chundakadan Settings', {
    refresh(frm) {
        // Filter Account dropdown to Bank/Cash accounts scoped to the
        // selected Company on the same row. Frappe re-runs get_query
        // every time the user opens the dropdown, so the filter stays
        // in sync with the row's current Company / Mode of Payment.
        frm.set_query('account', 'mop_mapping', function (doc, cdt, cdn) {
            const row = locals[cdt][cdn];
            const account_types_for_mode = {
                'Cash': ['Cash'],
                'Cheque': ['Bank'],
                'Bank Draft': ['Bank'],
                'Bank Transfer': ['Bank'],
                'Wire Transfer': ['Bank'],
                'Credit Card': ['Bank'],
                'Debit Card': ['Bank'],
            };
            const types = account_types_for_mode[row.mode_of_payment] || ['Bank', 'Cash'];
            const filters = {
                account_type: ['in', types],
                is_group: 0,
            };
            if (row.company) filters.company = row.company;
            return { filters };
        });
    },
});

frappe.ui.form.on('Chundakadan Sales Person MOP', {
    mode_of_payment(frm, cdt, cdn) {
        // When the user picks a Mode of Payment, pre-fill Account from
        // the standard `Mode of Payment Account` default (parent=mode,
        // company=row.company). Skips silently if either is missing or
        // no default account is configured.
        const row = locals[cdt][cdn];
        if (!row.mode_of_payment || !row.company) return;
        frappe.db.get_value(
            'Mode of Payment Account',
            { parent: row.mode_of_payment, company: row.company },
            'default_account'
        ).then((r) => {
            const acct = r && r.message && r.message.default_account;
            if (acct && !row.account) {
                frappe.model.set_value(cdt, cdn, 'account', acct);
            }
        });
    },
    company(frm, cdt, cdn) {
        // If user changes Company AFTER picking Mode of Payment, blank
        // the Account so the wrong-company account doesn't linger, then
        // re-resolve via the mode_of_payment handler.
        const row = locals[cdt][cdn];
        if (row.account) {
            frappe.model.set_value(cdt, cdn, 'account', '');
        }
        if (row.mode_of_payment && row.company) {
            frappe.db.get_value(
                'Mode of Payment Account',
                { parent: row.mode_of_payment, company: row.company },
                'default_account'
            ).then((r) => {
                const acct = r && r.message && r.message.default_account;
                if (acct) frappe.model.set_value(cdt, cdn, 'account', acct);
            });
        }
    },
});
