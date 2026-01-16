from flask import Blueprint, request, send_file, jsonify
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
import os
import uuid



def generate_pdf(grammar, start_symbol, first, follow):
    file_name = f"grammar_notes_{uuid.uuid4().hex}.pdf"
    file_path = os.path.join("/tmp", file_name)

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(file_path, pagesize=A4)

    story = []

    # ---------- TITLE ----------
    story.append(Paragraph("<b>Compiler Design Notes</b>", styles["Title"]))
    story.append(Paragraph(
        "Grammar, FIRST and FOLLOW (Auto-generated)",
        styles["Normal"]
    ))
    story.append(Spacer(1, 12))

    # ---------- INPUT GRAMMAR ----------
    story.append(Paragraph("<b>1. Input Grammar</b>", styles["Heading2"]))
    for nt, productions in grammar.items():
        for p in productions:
            story.append(Paragraph(f"{nt} → {p}", styles["Normal"]))

    story.append(Spacer(1, 12))

    # ---------- GRAMMAR INFO ----------
    story.append(Paragraph("<b>2. Grammar Definition</b>", styles["Heading2"]))
    story.append(Paragraph("Type: Context-Free Grammar (CFG)", styles["Normal"]))
    story.append(Paragraph(f"Start Symbol: {start_symbol}", styles["Normal"]))

    non_terminals = ", ".join(grammar.keys())
    story.append(Paragraph(f"Non-terminals: {{ {non_terminals} }}", styles["Normal"]))

    story.append(Spacer(1, 12))

    # ---------- FIRST ----------
    story.append(Paragraph("<b>3. FIRST Set</b>", styles["Heading2"]))
    story.append(Paragraph(
        "FIRST(X) is the set of terminals that begin strings derivable from X.",
        styles["Normal"]
    ))

    for nt, values in first.items():
        story.append(
            Paragraph(f"FIRST({nt}) = {{ {', '.join(values)} }}", styles["Normal"])
        )

    story.append(Spacer(1, 12))

    # ---------- FOLLOW ----------
    story.append(Paragraph("<b>4. FOLLOW Set</b>", styles["Heading2"]))
    story.append(Paragraph(
        "FOLLOW(A) is the set of terminals that can appear immediately to the right of A.",
        styles["Normal"]
    ))

    for nt, values in follow.items():
        story.append(
            Paragraph(f"FOLLOW({nt}) = {{ {', '.join(values)} }}", styles["Normal"])
        )

    story.append(Spacer(1, 12))

    # ---------- SUMMARY TABLE ----------
    story.append(Paragraph("<b>5. FIRST & FOLLOW Summary</b>", styles["Heading2"]))

    table_data = [["Non-Terminal", "FIRST", "FOLLOW"]]
    for nt in grammar.keys():
        table_data.append([
            nt,
            ", ".join(first.get(nt, [])),
            ", ".join(follow.get(nt, []))
        ])

    table = Table(table_data, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey)
    ]))

    story.append(table)

    story.append(Spacer(1, 12))

    # ---------- EXAM NOTES ----------
    story.append(Paragraph("<b>6. Exam Notes</b>", styles["Heading2"]))
    story.append(Paragraph(
        "- FIRST helps in predicting derivations<br/>"
        "- FOLLOW defines valid symbols after a non-terminal<br/>"
        "- Used in LL(1) and SLR parsing",
        styles["Normal"]
    ))

    doc.build(story)
    return file_path




