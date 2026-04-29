"""print_service — render POS receipt / invoice as HTML, PDF, or JPG.

PDF is generated with wkhtmltopdf when available; falls back to HTML-only.
JPG export uses wkhtmltoimage when available.
"""
import os
import subprocess
import tempfile
from jinja2 import Environment


def _wkhtmltopdf_available() -> bool:
    try:
        subprocess.run(["wkhtmltopdf", "--version"], capture_output=True, timeout=3)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _wkhtmltoimage_available() -> bool:
    try:
        subprocess.run(["wkhtmltoimage", "--version"], capture_output=True, timeout=3)
        return True
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def render_receipt_html(order_id: int, template_html: str = None, css: str = None) -> str:
    """Return rendered HTML string for a POS order receipt."""
    from aras.erp.erp_pos.models.order import PosOrder

    order = PosOrder.get_or_404(order_id)
    session = order.session
    terminal = session.terminal
    company = terminal.company if terminal else None

    default_tpl = _default_receipt_template()
    body = template_html or default_tpl

    env = Environment(autoescape=True)
    tpl = env.from_string(body)
    rendered_body = tpl.render(
        order=order,
        session=session,
        terminal=terminal,
        company=company,
        lines=list(order.lines),
        payments=list(order.payments),
    )

    receipt_css = css or _default_receipt_css()
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8">
<style>{receipt_css}</style>
</head>
<body>{rendered_body}</body>
</html>"""


def render_invoice_html(invoice_id: int, template_html: str = None, css: str = None) -> str:
    """Return rendered HTML string for a Sales Invoice (for print format)."""
    from aras.erp.erp_acc.models.invoice import AccSalesInvoice

    inv = AccSalesInvoice.get_or_404(invoice_id)
    company = inv.company
    customer = inv.customer

    default_tpl = _default_invoice_template()
    body = template_html or default_tpl

    env = Environment(autoescape=True)
    tpl = env.from_string(body)
    rendered_body = tpl.render(
        invoice=inv,
        company=company,
        customer=customer,
        lines=list(inv.lines),
    )

    invoice_css = css or _default_invoice_css()
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8">
<style>{invoice_css}</style>
</head>
<body>{rendered_body}</body>
</html>"""


def html_to_pdf(html: str, paper_size: str = "A5", orientation: str = "portrait",
                margin_mm: int = 8) -> bytes:
    """Convert HTML to PDF bytes via wkhtmltopdf. Raises RuntimeError if unavailable."""
    if not _wkhtmltopdf_available():
        raise RuntimeError("wkhtmltopdf not installed")

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
        f.write(html)
        html_path = f.name

    pdf_path = html_path.replace(".html", ".pdf")
    try:
        subprocess.run([
            "wkhtmltopdf",
            f"--page-size", paper_size,
            f"--orientation", orientation,
            f"--margin-top", f"{margin_mm}mm",
            f"--margin-right", f"{margin_mm}mm",
            f"--margin-bottom", f"{margin_mm}mm",
            f"--margin-left", f"{margin_mm}mm",
            "--disable-smart-shrinking",
            "--no-background",
            html_path, pdf_path,
        ], check=True, capture_output=True, timeout=30)

        with open(pdf_path, "rb") as f:
            return f.read()
    finally:
        os.unlink(html_path)
        if os.path.exists(pdf_path):
            os.unlink(pdf_path)


def html_to_jpg(html: str, width: int = 400) -> bytes:
    """Convert HTML to JPG bytes via wkhtmltoimage. Raises RuntimeError if unavailable."""
    if not _wkhtmltoimage_available():
        raise RuntimeError("wkhtmltoimage not installed")

    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
        f.write(html)
        html_path = f.name

    img_path = html_path.replace(".html", ".jpg")
    try:
        subprocess.run([
            "wkhtmltoimage",
            "--format", "jpg",
            "--width", str(width),
            "--quality", "90",
            html_path, img_path,
        ], check=True, capture_output=True, timeout=30)

        with open(img_path, "rb") as f:
            return f.read()
    finally:
        os.unlink(html_path)
        if os.path.exists(img_path):
            os.unlink(img_path)


def _get_print_template(doc_type: str, company_id: int):
    """Return default PrintTemplate for doc_type/company, or None."""
    from aras.erp.erp_core.models.print_template import PrintTemplate
    return PrintTemplate.find(company_id=company_id, doc_type=doc_type, is_default=True)


def _default_receipt_template() -> str:
    return """<div class="receipt">
  {% if company %}<div class="co-name">{{ company.name }}</div>{% endif %}
  {% if terminal and terminal.receipt_header %}<div class="co-sub">{{ terminal.receipt_header }}</div>{% endif %}
  <div class="divider">————————————————</div>
  <table class="items">
    <thead><tr><th>Item</th><th>Qty</th><th class="r">Total</th></tr></thead>
    <tbody>
    {% for l in lines %}
    <tr>
      <td>{{ l.product_name }}</td>
      <td>{{ l.qty }}</td>
      <td class="r">{{ "{:,.0f}".format(l.subtotal) }}</td>
    </tr>
    {% endfor %}
    </tbody>
  </table>
  <div class="divider">————————————————</div>
  <div class="totals">
    <div><span>Subtotal</span><span>{{ "{:,.0f}".format(order.subtotal) }}</span></div>
    {% if order.tax_amt %}<div><span>Tax</span><span>{{ "{:,.0f}".format(order.tax_amt) }}</span></div>{% endif %}
    <div class="grand"><span>TOTAL</span><span>{{ "{:,.0f}".format(order.total) }}</span></div>
    {% for p in payments %}
    <div><span>{{ p.method|upper }}</span><span>{{ "{:,.0f}".format(p.amount) }}</span></div>
    {% endfor %}
    {% if order.change_amt %}<div><span>Change</span><span>{{ "{:,.0f}".format(order.change_amt) }}</span></div>{% endif %}
  </div>
  <div class="divider">————————————————</div>
  <div class="ref">{{ order.name }}</div>
  <div class="ref">{{ order.created_at.strftime('%d/%m/%Y %H:%M') if order.created_at else '' }}</div>
  {% if terminal and terminal.receipt_footer %}<div class="footer">{{ terminal.receipt_footer }}</div>{% endif %}
  <div class="footer">Thank you!</div>
</div>"""


def _default_receipt_css() -> str:
    return """
body { font-family: 'Courier New', monospace; font-size: 12px; margin: 0; padding: 8px; width: 300px; }
.receipt { width: 100%; }
.co-name { text-align: center; font-weight: bold; font-size: 15px; margin-bottom: 2px; }
.co-sub  { text-align: center; font-size: 11px; color: #555; margin-bottom: 4px; }
.divider { text-align: center; color: #999; margin: 6px 0; font-size: 10px; }
.items   { width: 100%; border-collapse: collapse; margin: 4px 0; }
.items th, .items td { padding: 2px 0; vertical-align: top; }
.items th { border-bottom: 1px dashed #ccc; font-size: 10px; text-transform: uppercase; }
.r { text-align: right; }
.totals  { margin: 4px 0; }
.totals div { display: flex; justify-content: space-between; padding: 1px 0; }
.grand   { font-weight: bold; font-size: 14px; border-top: 1px dashed #ccc; padding-top: 3px; margin-top: 3px; }
.ref     { text-align: center; font-size: 10px; color: #666; margin-top: 2px; }
.footer  { text-align: center; font-size: 11px; margin-top: 6px; color: #444; }
@media print { body { margin: 0; } }
"""


def _default_invoice_template() -> str:
    return """<div class="inv-wrap">
  <div class="inv-header">
    <div class="inv-company">
      {% if company %}<h2>{{ company.name }}</h2>{% endif %}
    </div>
    <div class="inv-meta">
      <h1>INVOICE</h1>
      <div class="inv-num">{{ invoice.name }}</div>
      <div class="inv-date">Date: {{ invoice.invoice_date.strftime('%d %b %Y') }}</div>
      {% if invoice.due_date %}<div class="inv-date">Due: {{ invoice.due_date.strftime('%d %b %Y') }}</div>{% endif %}
    </div>
  </div>
  {% if customer %}
  <div class="inv-to">
    <div class="label">Bill To</div>
    <div>{{ customer.name }}</div>
  </div>
  {% endif %}
  <table class="inv-lines">
    <thead>
      <tr><th>#</th><th>Description</th><th class="r">Qty</th><th class="r">Price</th><th class="r">Amount</th></tr>
    </thead>
    <tbody>
    {% for l in lines %}
    <tr>
      <td>{{ loop.index }}</td>
      <td>{{ l.description }}</td>
      <td class="r">{{ l.qty }}</td>
      <td class="r">{{ "{:,.2f}".format(l.unit_price) }}</td>
      <td class="r">{{ "{:,.2f}".format(l.subtotal) }}</td>
    </tr>
    {% endfor %}
    </tbody>
  </table>
  <div class="inv-totals">
    <div><span>Subtotal</span><span>{{ "{:,.2f}".format(invoice.subtotal) }}</span></div>
    {% if invoice.discount_amt %}<div><span>Discount</span><span>({{ "{:,.2f}".format(invoice.discount_amt) }})</span></div>{% endif %}
    {% if invoice.tax_amt %}<div><span>Tax</span><span>{{ "{:,.2f}".format(invoice.tax_amt) }}</span></div>{% endif %}
    <div class="grand"><span>Total</span><span>{{ "{:,.2f}".format(invoice.total) }}</span></div>
  </div>
  {% if invoice.notes %}<div class="inv-notes">{{ invoice.notes }}</div>{% endif %}
</div>"""


def _default_invoice_css() -> str:
    return """
body { font-family: Arial, sans-serif; font-size: 12px; margin: 0; padding: 24px; color: #222; }
.inv-wrap { max-width: 700px; margin: auto; }
.inv-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24px; }
.inv-company h2 { margin: 0; font-size: 20px; }
.inv-meta { text-align: right; }
.inv-meta h1 { margin: 0; font-size: 28px; color: #1a56db; letter-spacing: 2px; }
.inv-num  { font-size: 13px; font-weight: bold; margin-top: 4px; }
.inv-date { font-size: 11px; color: #555; }
.inv-to   { margin-bottom: 16px; }
.inv-to .label { font-size: 10px; text-transform: uppercase; color: #888; margin-bottom: 2px; }
.inv-lines { width: 100%; border-collapse: collapse; margin-bottom: 16px; }
.inv-lines th { background: #f3f4f6; padding: 6px 8px; text-align: left; font-size: 11px; border-bottom: 2px solid #e5e7eb; }
.inv-lines td { padding: 6px 8px; border-bottom: 1px solid #f0f0f0; }
.r { text-align: right; }
.inv-totals { float: right; width: 260px; }
.inv-totals div { display: flex; justify-content: space-between; padding: 3px 0; }
.grand { font-weight: bold; font-size: 14px; border-top: 2px solid #222; padding-top: 4px; margin-top: 4px; }
.inv-notes { clear: both; margin-top: 24px; padding: 12px; background: #f9fafb; border-radius: 4px; font-size: 11px; color: #555; }
@media print { body { padding: 12px; } }
"""
