# Copyright (c) 2026, vijila@teambackoffice.com and contributors
# For license information, please see license.txt

"""Companion controller for the Customer Feedback Web Form.

Frappe v15 calls `web_form_module.get_context(context)` during page
render (see frappe/website/doctype/web_form/web_form.py
add_custom_context_and_script). The function must exist on the module
or rendering throws AttributeError; an empty body is fine when the
form needs no extra context massaging.
"""


def get_context(context):
    # No extra context needed — the Web Form JSON drives field rendering.
    # Defensively mark the page non-cacheable so live label/option edits
    # in the desk show up on next page load.
    try:
        context.no_cache = 1
    except Exception:
        pass
    return context
