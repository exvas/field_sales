// field_sales: hide the "Add Multiple" item button on transaction forms.
//
// The button opens ERPNext's Select Item filter dialog (Item Group +
// custom Link fields on Item like our former Model & Size / Finish).
// The team prefers single-row add — this strips the button from each
// listed doctype's items grid on every refresh.
//
// Registered via hooks.app_include_js so it loads on every desk page
// and self-restricts via doctype-scoped form events.

(function () {
    const TARGETS = [
        "Sales Invoice",
        "Sales Order",
        "Quotation",
        "Delivery Note",
        "Purchase Invoice",
        "Purchase Order",
        "Purchase Receipt",
    ];

    const stripAddMultiple = (frm) => {
        const grid = frm && frm.fields_dict && frm.fields_dict.items
            ? frm.fields_dict.items.grid
            : null;
        if (!grid || !grid.wrapper) return;
        // Multiple class names across Frappe versions — cover them all.
        ["grid-add-multiple-rows", "grid-add-multi", "btn-add-multiple"]
            .forEach((cls) => $(grid.wrapper).find("." + cls).remove());
        // Also catch the menu item if the grid moved it under a menu.
        $(grid.wrapper)
            .find('a:contains("Add Multiple"), button:contains("Add Multiple")')
            .remove();
    };

    TARGETS.forEach((dt) => {
        frappe.ui.form.on(dt, {
            refresh: function (frm) {
                // Run now, and again after the grid finishes painting.
                stripAddMultiple(frm);
                setTimeout(() => stripAddMultiple(frm), 250);
            },
        });
    });
})();
