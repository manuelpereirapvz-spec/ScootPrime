from __future__ import annotations

from datetime import datetime
from io import BytesIO
from pathlib import Path
from textwrap import wrap

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

PRIMARY = colors.HexColor("#0F3D5E")
ACCENT = colors.HexColor("#1D8A68")
TEXT = colors.HexColor("#202426")
MUTED = colors.HexColor("#6D7673")
LINE = colors.HexColor("#D9E2DD")
PAPER = colors.HexColor("#F5F8F6")
WHITE = colors.white

COMPANY_NAME = "ScootPrime"
COMPANY_SUBTITLE = "Servico de Reparacao"
COMPANY_CONTACT = "Filipe - 937320683"
COMPANY_ADDRESS = ""
VALIDITY_NOTE = "Este orcamento e valido por 30 dias. Obrigado pela preferencia."
OCCURRENCE_NOTE = "Documento de registo de ocorrencia gerado pelo ScootPrime."


def _money(value) -> str:
    return f"{float(value or 0):.2f} EUR"


def _budget_date_token(date_text: str) -> str:
    try:
        return datetime.strptime(date_text, "%d/%m/%Y").strftime("%Y%m%d")
    except Exception:
        return datetime.now().strftime("%Y%m%d")


def budget_reference(budget) -> str:
    return f"ORC-{budget['id']}-{_budget_date_token(budget['data'])}"


def budget_filename(budget) -> str:
    return f"ORC_{budget['id']}_{_budget_date_token(budget['data'])}.pdf"


def occurrence_reference(occurrence) -> str:
    return f"OCC-{occurrence['id']}-{_budget_date_token(str(occurrence['data']).split()[0])}"


def occurrence_filename(occurrence) -> str:
    return f"OCC_{occurrence['id']}_{_budget_date_token(str(occurrence['data']).split()[0])}.pdf"


def stock_report_filename(low_only=False) -> str:
    suffix = "REPOSICAO" if low_only else "EXISTENTE"
    return f"STOCK_{suffix}_{datetime.now().strftime('%Y%m%d')}.pdf"


def _profile_value(profile, key, fallback):
    if not profile:
        return fallback
    return profile.get(key) or fallback


def _image_reader(brand_logo=None):
    if not brand_logo:
        return None
    try:
        if isinstance(brand_logo, (str, Path)):
            path = Path(brand_logo)
            return str(path) if path.exists() else None
        return ImageReader(BytesIO(brand_logo["dados"]))
    except Exception:
        return None


def _draw_wrapped(c, text, x, y, width_chars=85, leading=5 * mm, font="Helvetica", size=9, color=TEXT, max_lines=None):
    c.setFont(font, size)
    c.setFillColor(color)
    lines: list[str] = []
    for raw_line in (text or "-").splitlines() or ["-"]:
        lines.extend(wrap(raw_line, width_chars) or [""])
    if max_lines:
        lines = lines[:max_lines]
    for line in lines:
        c.drawString(x, y, line)
        y -= leading
    return y


def _draw_label_value(c, label, value, x, y, label_width=31 * mm):
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(PRIMARY)
    c.drawString(x, y, label)
    c.setFont("Helvetica", 9)
    c.setFillColor(TEXT)
    c.drawString(x + label_width, y, str(value or "-"))


def _draw_header(c, width, height, brand_logo=None, profile=None, document_title="ORCAMENTO"):
    company_name = _profile_value(profile, "store_name", COMPANY_NAME)
    company_subtitle = _profile_value(profile, "store_subtitle", COMPANY_SUBTITLE)
    company_contact = _profile_value(profile, "store_contact", COMPANY_CONTACT)
    company_address = _profile_value(profile, "store_address", COMPANY_ADDRESS)
    logo = _image_reader(brand_logo)
    if logo:
        c.drawImage(
            logo,
            18 * mm,
            height - 36 * mm,
            width=42 * mm,
            height=24 * mm,
            preserveAspectRatio=True,
            mask="auto",
        )
        title_x = 66 * mm
    else:
        c.setFillColor(PRIMARY)
        c.roundRect(18 * mm, height - 35 * mm, 22 * mm, 22 * mm, 6 * mm, fill=True, stroke=False)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredString(29 * mm, height - 22 * mm, "SP")
        title_x = 47 * mm

    c.setFillColor(PRIMARY)
    c.setFont("Helvetica-Bold", 28)
    c.drawString(title_x, height - 22 * mm, company_name[:26])
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 11)
    c.drawString(title_x, height - 30 * mm, company_subtitle[:48])
    c.drawString(title_x, height - 36 * mm, company_contact[:48])
    if company_address:
        c.setFont("Helvetica", 8)
        c.drawString(title_x, height - 41 * mm, company_address[:72])

    c.setFillColor(PRIMARY)
    c.roundRect(width - 68 * mm, height - 38 * mm, 50 * mm, 24 * mm, 5 * mm, fill=True, stroke=False)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(width - 43 * mm, height - 24 * mm, document_title[:12])


def _draw_client_and_meta(c, cliente, budget, width, y):
    left_x = 18 * mm
    right_x = 124 * mm
    card_h = 38 * mm

    c.setFillColor(WHITE)
    c.setStrokeColor(LINE)
    c.roundRect(left_x, y - card_h, 98 * mm, card_h, 5 * mm, fill=True, stroke=True)
    c.roundRect(right_x, y - card_h, width - right_x - 18 * mm, card_h, 5 * mm, fill=True, stroke=True)

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(PRIMARY)
    c.drawString(left_x + 6 * mm, y - 8 * mm, "Cliente")
    _draw_label_value(c, "Nome:", cliente["nome"], left_x + 6 * mm, y - 17 * mm, 19 * mm)
    _draw_label_value(c, "Morada:", cliente["morada"] or "-", left_x + 6 * mm, y - 25 * mm, 19 * mm)
    _draw_label_value(c, "Contacto:", cliente["contacto"] or "-", left_x + 6 * mm, y - 33 * mm, 19 * mm)

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(PRIMARY)
    c.drawString(right_x + 6 * mm, y - 8 * mm, "Dados do documento")
    _draw_label_value(c, "Numero:", budget_reference(budget), right_x + 6 * mm, y - 17 * mm, 26 * mm)
    _draw_label_value(c, "Data:", budget["data"], right_x + 6 * mm, y - 25 * mm, 26 * mm)
    _draw_label_value(c, "Validade:", "30 dias", right_x + 6 * mm, y - 33 * mm, 26 * mm)
    return y - card_h - 10 * mm


def _draw_section_title(c, title, x, y):
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(PRIMARY)
    c.drawString(x, y, title)
    c.setStrokeColor(ACCENT)
    c.setLineWidth(1.2)
    c.line(x, y - 2 * mm, x + 35 * mm, y - 2 * mm)


def _draw_description(c, budget, width, y):
    x = 18 * mm
    _draw_section_title(c, "Descricao do servico", x, y)
    box_top = y - 7 * mm
    box_h = 34 * mm
    c.setFillColor(PAPER)
    c.setStrokeColor(LINE)
    c.roundRect(x, box_top - box_h, width - 36 * mm, box_h, 5 * mm, fill=True, stroke=True)
    _draw_wrapped(c, budget["descricao"], x + 5 * mm, box_top - 7 * mm, width_chars=92, max_lines=7)
    return box_top - box_h - 10 * mm


def _draw_items_table(c, budget, materiais, width, y):
    x = 18 * mm
    table_w = width - 36 * mm
    _draw_section_title(c, "Itens do orcamento", x, y)
    y -= 8 * mm

    c.setFillColor(PRIMARY)
    c.roundRect(x, y - 8 * mm, table_w, 8 * mm, 3 * mm, fill=True, stroke=False)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(x + 5 * mm, y - 5 * mm, "DESCRICAO")
    c.drawCentredString(x + 132 * mm, y - 5 * mm, "QTD.")
    c.drawRightString(x + table_w - 5 * mm, y - 5 * mm, "VALOR")
    y -= 8 * mm

    rows = [("Servico de reparacao", "1", _money(budget["preco"]))]
    rows.extend((material["nome_material"], str(material["quantidade"]), "Incluido") for material in (materiais or [])[:8])

    for index, (description, quantity, value) in enumerate(rows):
        row_h = 9 * mm
        c.setFillColor(colors.HexColor("#FAFCFB") if index % 2 == 0 else WHITE)
        c.rect(x, y - row_h, table_w, row_h, fill=True, stroke=False)
        c.setStrokeColor(LINE)
        c.line(x, y - row_h, x + table_w, y - row_h)
        c.setFillColor(TEXT)
        c.setFont("Helvetica", 9)
        c.drawString(x + 5 * mm, y - 6 * mm, description[:70])
        c.drawCentredString(x + 132 * mm, y - 6 * mm, quantity)
        c.drawRightString(x + table_w - 5 * mm, y - 6 * mm, value)
        y -= row_h

    return y - 9 * mm


def _draw_totals(c, budget, width, y):
    box_w = 70 * mm
    x = width - 18 * mm - box_w
    line_h = 8 * mm
    paid = float(budget["valor_pago"] or 0)
    total = float(budget["total"] or 0)
    open_amount = max(0, total - paid)
    rows = [
        ("Subtotal", _money(budget["preco"]), False),
        ("IVA (23%)", _money(budget["iva"]), False),
        ("Total", _money(total), True),
    ]
    if paid:
        rows.append(("Valor pago", _money(paid), False))
        rows.append(("Por liquidar", _money(open_amount), True))

    box_h = line_h * len(rows) + 5 * mm
    c.setFillColor(WHITE)
    c.setStrokeColor(LINE)
    c.roundRect(x, y - box_h, box_w, box_h, 5 * mm, fill=True, stroke=True)
    y_line = y - 7 * mm
    for label, value, strong in rows:
        c.setFont("Helvetica-Bold" if strong else "Helvetica", 10 if strong else 9)
        c.setFillColor(PRIMARY if strong else MUTED)
        c.drawString(x + 5 * mm, y_line, label)
        c.setFillColor(TEXT)
        c.drawRightString(x + box_w - 5 * mm, y_line, value)
        y_line -= line_h
    return y - box_h - 11 * mm


def _draw_footer(c, width, profile=None, note=VALIDITY_NOTE):
    company_name = _profile_value(profile, "store_name", COMPANY_NAME)
    footer_y = 20 * mm
    c.setStrokeColor(LINE)
    c.line(18 * mm, footer_y + 9 * mm, width - 18 * mm, footer_y + 9 * mm)
    c.setFont("Helvetica", 8)
    c.setFillColor(MUTED)
    c.drawString(18 * mm, footer_y, note)
    c.drawRightString(width - 18 * mm, footer_y, company_name)


def build_budget_pdf(cliente, budget, materiais=None, brand_logo_path=None, store_profile=None) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setTitle(budget_reference(budget))
    c.setAuthor(_profile_value(store_profile, "store_name", COMPANY_NAME))
    c.setSubject("Orcamento de reparacao")

    _draw_header(c, width, height, brand_logo_path, store_profile, "ORCAMENTO")
    y = height - 54 * mm
    y = _draw_client_and_meta(c, cliente, budget, width, y)
    y = _draw_description(c, budget, width, y)
    y = _draw_items_table(c, budget, materiais, width, y)
    _draw_totals(c, budget, width, y)
    _draw_footer(c, width, store_profile, VALIDITY_NOTE)

    c.save()
    return buffer.getvalue()


def _draw_occurrence_meta(c, occurrence, width, y):
    left_x = 18 * mm
    right_x = 124 * mm
    card_h = 38 * mm

    c.setFillColor(WHITE)
    c.setStrokeColor(LINE)
    c.roundRect(left_x, y - card_h, 98 * mm, card_h, 5 * mm, fill=True, stroke=True)
    c.roundRect(right_x, y - card_h, width - right_x - 18 * mm, card_h, 5 * mm, fill=True, stroke=True)

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(PRIMARY)
    c.drawString(left_x + 6 * mm, y - 8 * mm, "Cliente")
    _draw_label_value(c, "Nome:", occurrence["cliente_nome"] or "-", left_x + 6 * mm, y - 17 * mm, 19 * mm)
    _draw_label_value(c, "Morada:", occurrence["morada"] or "-", left_x + 6 * mm, y - 25 * mm, 19 * mm)
    _draw_label_value(c, "Contacto:", occurrence["contacto"] or "-", left_x + 6 * mm, y - 33 * mm, 19 * mm)

    c.setFont("Helvetica-Bold", 10)
    c.setFillColor(PRIMARY)
    c.drawString(right_x + 6 * mm, y - 8 * mm, "Dados da ocorrencia")
    _draw_label_value(c, "Numero:", occurrence_reference(occurrence), right_x + 6 * mm, y - 17 * mm, 26 * mm)
    _draw_label_value(c, "Data:", occurrence["data"], right_x + 6 * mm, y - 25 * mm, 26 * mm)
    _draw_label_value(c, "Estado:", "Registada", right_x + 6 * mm, y - 33 * mm, 26 * mm)
    return y - card_h - 10 * mm


def build_occurrence_pdf(occurrence, brand_logo_path=None, store_profile=None) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setTitle(occurrence_reference(occurrence))
    c.setAuthor(_profile_value(store_profile, "store_name", COMPANY_NAME))
    c.setSubject("Registo de ocorrencia")

    _draw_header(c, width, height, brand_logo_path, store_profile, "OCORRENCIA")
    y = height - 54 * mm
    y = _draw_occurrence_meta(c, occurrence, width, y)

    x = 18 * mm
    _draw_section_title(c, "Descricao da ocorrencia", x, y)
    box_top = y - 7 * mm
    box_h = 74 * mm
    c.setFillColor(PAPER)
    c.setStrokeColor(LINE)
    c.roundRect(x, box_top - box_h, width - 36 * mm, box_h, 5 * mm, fill=True, stroke=True)
    _draw_wrapped(c, occurrence["descricao"], x + 5 * mm, box_top - 8 * mm, width_chars=92, leading=5 * mm, max_lines=13)

    _draw_footer(c, width, store_profile, OCCURRENCE_NOTE)
    c.save()
    return buffer.getvalue()


def _draw_stock_page_header(c, width, height, brand_logo_path, store_profile, title, subtitle):
    _draw_header(c, width, height, brand_logo_path, store_profile, title)
    y = height - 55 * mm
    c.setFillColor(PAPER)
    c.setStrokeColor(LINE)
    c.roundRect(18 * mm, y - 22 * mm, width - 36 * mm, 22 * mm, 5 * mm, fill=True, stroke=True)
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(PRIMARY)
    c.drawString(24 * mm, y - 8 * mm, subtitle)
    c.setFont("Helvetica", 9)
    c.setFillColor(MUTED)
    c.drawString(24 * mm, y - 16 * mm, f"Gerado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    return y - 34 * mm


def _draw_stock_table_header(c, x, y, table_w):
    c.setFillColor(PRIMARY)
    c.roundRect(x, y - 8 * mm, table_w, 8 * mm, 3 * mm, fill=True, stroke=False)
    c.setFillColor(WHITE)
    c.setFont("Helvetica-Bold", 7.5)
    c.drawString(x + 4 * mm, y - 5 * mm, "PRODUTO")
    c.drawString(x + 66 * mm, y - 5 * mm, "CATEGORIA")
    c.drawCentredString(x + 112 * mm, y - 5 * mm, "QTD.")
    c.drawCentredString(x + 130 * mm, y - 5 * mm, "MIN.")
    c.drawString(x + 144 * mm, y - 5 * mm, "LOCAL")
    c.drawRightString(x + table_w - 4 * mm, y - 5 * mm, "ESTADO")
    return y - 8 * mm


def build_stock_report_pdf(materiais, low_only=False, brand_logo_path=None, store_profile=None) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    title = "REPOSICAO" if low_only else "STOCK"
    subtitle = "Material em falta ou para reposicao" if low_only else "Stock existente"
    company_name = _profile_value(store_profile, "store_name", COMPANY_NAME)

    c.setTitle(subtitle)
    c.setAuthor(company_name)
    c.setSubject("Relatorio de stock")

    y = _draw_stock_page_header(c, width, height, brand_logo_path, store_profile, title, subtitle)
    x = 18 * mm
    table_w = width - 36 * mm
    y = _draw_stock_table_header(c, x, y, table_w)

    rows = list(materiais or [])
    if not rows:
        c.setFont("Helvetica", 10)
        c.setFillColor(MUTED)
        c.drawString(x + 4 * mm, y - 8 * mm, "Sem materiais para apresentar.")
    else:
        for index, item in enumerate(rows):
            if y < 36 * mm:
                _draw_footer(c, width, store_profile, "Relatorio gerado pelo ScootPrime.")
                c.showPage()
                y = _draw_stock_page_header(c, width, height, brand_logo_path, store_profile, title, subtitle)
                y = _draw_stock_table_header(c, x, y, table_w)

            quantity = int(item["quantidade"] or 0)
            minimum = int(item["stock_minimo"] or 0)
            status = "REPOR" if minimum > 0 and quantity <= minimum else "OK"
            row_h = 9 * mm
            c.setFillColor(colors.HexColor("#FFF6E6") if status == "REPOR" else (colors.HexColor("#FAFCFB") if index % 2 == 0 else WHITE))
            c.rect(x, y - row_h, table_w, row_h, fill=True, stroke=False)
            c.setStrokeColor(LINE)
            c.line(x, y - row_h, x + table_w, y - row_h)
            c.setFont("Helvetica", 8)
            c.setFillColor(TEXT)
            c.drawString(x + 4 * mm, y - 6 * mm, str(item["nome"])[:38])
            c.drawString(x + 66 * mm, y - 6 * mm, str(item["categoria"] or "-")[:24])
            c.drawCentredString(x + 112 * mm, y - 6 * mm, str(quantity))
            c.drawCentredString(x + 130 * mm, y - 6 * mm, str(minimum))
            c.drawString(x + 144 * mm, y - 6 * mm, str(item["localizacao"] or "-")[:18])
            c.setFont("Helvetica-Bold", 8)
            c.setFillColor(colors.HexColor("#B56A00") if status == "REPOR" else ACCENT)
            c.drawRightString(x + table_w - 4 * mm, y - 6 * mm, status)
            y -= row_h

    _draw_footer(c, width, store_profile, "Relatorio gerado pelo ScootPrime.")
    c.save()
    return buffer.getvalue()
