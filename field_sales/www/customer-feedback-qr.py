import base64
import io

import frappe


def get_context(context):
    feedback_url = frappe.utils.get_url("/customer-feedback")
    qr_base64 = _generate_qr(feedback_url)
    context.feedback_url = feedback_url
    context.qr_base64 = qr_base64
    context.no_cache = 1
    return context


def _generate_qr(data):
    try:
        import qrcode  # ships with Frappe v15
        from qrcode.image.pil import PilImage

        img = qrcode.make(data, image_factory=PilImage, box_size=10, border=2)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("utf-8")
    except Exception:
        frappe.log_error(frappe.get_traceback(), "field_sales.customer_feedback_qr")
        return ""
