"""Genera la guía imprimible desde su fuente Markdown. Requiere reportlab."""

import re
from html import escape
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parent.parent
FONT_DIR = Path("C:/Windows/Fonts")
for name, filename in [("Arial", "arial.ttf"), ("Arial-Bold", "arialbd.ttf")]:
    pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / filename)))
pdfmetrics.registerFontFamily("Arial", normal="Arial", bold="Arial-Bold")

BODY = ParagraphStyle("body", fontName="Arial", fontSize=10.5, leading=15,
                      spaceAfter=8, textColor=colors.HexColor("#26312e"))
TITLE = ParagraphStyle("title", parent=BODY, fontName="Arial-Bold", fontSize=22,
                       leading=27, spaceAfter=17, textColor=colors.HexColor("#234c40"))
H2 = ParagraphStyle("heading", parent=BODY, fontName="Arial-Bold", fontSize=13,
                    leading=17, spaceBefore=9, spaceAfter=8, keepWithNext=True)
CELL = ParagraphStyle("cell", parent=BODY, fontSize=9.5, leading=13, spaceAfter=0)


def rich(text):
    text = escape(text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r'<font name="Courier" size="9">\1</font>', text)
    return text


def footer(canvas, doc):
    canvas.setTitle("Guía para presentar EntreLibros · Grupo 85")
    canvas.setAuthor("Grupo 85")
    canvas.setFont("Arial", 8)
    canvas.setFillColor(colors.HexColor("#5a6d65"))
    canvas.drawString(43, A4[1] - 30, "ENTRELIBROS  /  GUÍA DE EXPOSICIÓN")
    canvas.drawRightString(A4[0] - 43, A4[1] - 30, "Grupo 85 · Biblioteca")
    canvas.drawString(43, 24, "Preparación de defensa · Noviembre de 2026")
    canvas.drawRightString(A4[0] - 43, 24, str(doc.page))


def build():
    lines = (ROOT / "docs/guia-exposicion.md").read_text(encoding="utf-8").splitlines()
    story, index = [], 0
    while index < len(lines):
        line = lines[index].strip()
        if not line:
            index += 1
            continue
        if line == "<!-- page -->":
            story.append(PageBreak())
        elif line.startswith("# "):
            story.append(Paragraph(rich(line[2:]), TITLE))
        elif line.startswith("## "):
            story.append(Paragraph(rich(line[3:]), H2))
        elif line.startswith("|"):
            rows = []
            while index < len(lines) and lines[index].strip().startswith("|"):
                row = [s.strip() for s in lines[index].strip().strip("|").split("|")]
                if not all(re.fullmatch(r"[-: ]+", s) for s in row):
                    rows.append([Paragraph(rich(s), CELL) for s in row])
                index += 1
            table = Table(rows, colWidths=[112, A4[0] - 198], repeatRows=1, hAlign=TA_LEFT)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8eeeb")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LINEBELOW", (0, 0), (-1, -1), .3, colors.HexColor("#c9d3cd")),
            ]))
            story.extend([table, Spacer(1, 10)])
            continue
        else:
            story.append(Paragraph(rich(line), BODY))
        index += 1
    target = ROOT / "docs/Guia-exposicion-grupo-85.pdf"
    doc = SimpleDocTemplate(str(target), pagesize=A4, leftMargin=43, rightMargin=43,
                            topMargin=53, bottomMargin=44)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(target)


if __name__ == "__main__":
    build()
