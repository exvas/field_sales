"""Companion controller for customer-feedback-qr.html.

The HTML now resolves the feedback URL itself via Jinja's `frappe`
global (`frappe.utils.get_url("/customer-feedback")`) and pulls the QR
image from a public QR-generator service, so no Python-side QR
rendering is needed. This file just marks the page as non-cacheable
and provides a `feedback_url` backup variable for older cached
templates.
"""
import frappe


def get_context(context):
    context.no_cache = 1
    context.feedback_url = frappe.utils.get_url("/customer-feedback")
    return context
