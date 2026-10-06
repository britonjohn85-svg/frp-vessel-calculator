# app.py
# Streamlit UI for the FRP Vessel Media Calculator

import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from io import BytesIO
from datetime import datetime
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from calculations import (
    calculate_sand,
    calculate_activated_carbon,
    calculate_resin,
    calculate_activated_alumina,
    calculate_mixed_bed,
    calculate_system_summary,
)


# ============================================================
# PAGE CONFIG — WITH VESSEL ICON
# ============================================================
try:
    img = Image.open("vessel_icon.png").convert("RGBA")
    max_dim = max(img.size)
    square = Image.new("RGBA", (max_dim, max_dim), (255, 255, 255, 0))
    square.paste(img, ((max_dim - img.width) // 2, (max_dim - img.height) // 2))
    square = square.resize((256, 256), Image.LANCZOS)
    vessel_icon = square
except Exception:
    vessel_icon = "🛢️"

st.set_page_config(
    page_title="FRP Vessel Media Calculator",
    page_icon=vessel_icon,
    layout="wide",
)

st.title("🛢️ FRP Vessel Media Calculator")
st.markdown("Calculate the media bags required for your FRP vessel system.")


# ============================================================
# LAYER COLORS
# ============================================================
LAYER_COLORS = {
    "Freeboard": "#FFFFFF",
    "Grade D": "#8B4513",
    "Grade C": "#D2691E",
    "Grade C (bottom)": "#D2691E",
    "Grade B (bottom)": "#DAA520",
    "Grade B (middle)": "#DAA520",
    "Grade B (top)": "#DAA520",
    "Grade A": "#F4E4BC",
    "Activated Carbon": "#2C2C2C",
    "Resin": "#FFD700",
    "Activated Alumina": "#4682B4",
}


# ============================================================
# LAYERING DIAGRAM
# ============================================================
def generate_layering_image(layering: list, vessel_model: str, freeboard: float = 0.40) -> BytesIO:
    fig, ax = plt.subplots(figsize=(3.5, 6))
    freeboard_height_units = 5 * freeboard
    media_height_units = 5 * (1 - freeboard)
    reversed_layers = list(reversed(layering))
    total_bags = sum(layer["bags"] for layer in reversed_layers) or 1

    freeboard_bottom = media_height_units
    rect = mpatches.Rectangle(
        (0, freeboard_bottom), 1, freeboard_height_units,
        facecolor="#F0F0F0", edgecolor="black", linewidth=1, hatch="//"
    )
    ax.add_patch(rect)
    ax.text(
        0.5, freeboard_bottom + freeboard_height_units / 2,
        f"FREEBOARD\n({int(freeboard*100)}% empty)",
        ha="center", va="center", fontsize=8, color="#666666"
    )

    bottom = 0
    for layer in reversed_layers:
        height = (layer["bags"] / total_bags) * media_height_units
        color = LAYER_COLORS.get(layer["media"], "#888888")
        rect = mpatches.Rectangle(
            (0, bottom), 1, height, facecolor=color, edgecolor="black", linewidth=1
        )
        ax.add_patch(rect)
        label = f"{layer['media']}\n{layer['bags']} bags"
        text_color = "white" if layer["media"] in ["Activated Carbon", "Grade D"] else "black"
        ax.text(0.5, bottom + height / 2, label,
                ha="center", va="center", fontsize=7, color=text_color)
        bottom += height

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 5.2)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(f"Vessel {vessel_model}\n(Top → Bottom)", fontsize=9)
    plt.tight_layout()

    buf = BytesIO()
    plt.savefig(buf, format="png", dpi=100)
    plt.close(fig)
    buf.seek(0)
    return buf


# ============================================================
# PDF REPORT GENERATOR — WITH PAGE NUMBERS & TIMES NEW ROMAN
# ============================================================
def generate_pdf_report(
    sand_results, ac_results, resin_results, alumina_results,
    mixed_results, summary, shared_b_per_vessel, use_extra_sand
) -> BytesIO:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=50,
        bottomMargin=50,
        leftMargin=40,
        rightMargin=40,
    )
    styles = getSampleStyleSheet()

    # --- Custom styles using Times-Roman ---
    title_style = ParagraphStyle(
        "CustomTitle", parent=styles["Title"],
        fontName="Times-Bold", fontSize=18, leading=22, alignment=1,
    )
    heading_style = ParagraphStyle(
        "CustomHeading", parent=styles["Heading2"],
        fontName="Times-Bold", fontSize=13, leading=16,
        spaceBefore=10, spaceAfter=4,
    )
    normal_style = ParagraphStyle(
        "CustomNormal", parent=styles["Normal"],
        fontName="Times-Roman", fontSize=11, leading=14,
    )
    italic_style = ParagraphStyle(
        "CustomItalic", parent=styles["Normal"],
        fontName="Times-Italic", fontSize=10, leading=13,
        textColor=colors.grey,
    )

    # ============================================================
    # FOOTER — PAGE NUMBER (runs on every page)
    # ============================================================
    def draw_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont("Times-Roman", 9)
        canvas.setFillColor(colors.grey)
        canvas.drawCentredString(A4[0] / 2, 25, f"Page {doc.page}")
        canvas.restoreState()

    # ============================================================
    # BUILD THE STORY
    # ============================================================
    story = []

    # --- Title ---
    story.append(Paragraph("<b>FRP Vessel Media Calculation Report</b>", title_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        normal_style
    ))
    story.append(Spacer(1, 20))

    # --- Sand vessels ---
    for i, result in enumerate(sand_results):
        story.append(Paragraph(
            f"<b>Sand Vessel {i+1} — {result['vessel_model']}</b>", heading_style
        ))
        story.append(Paragraph(f"Total Sand Bags: {result['total_bags']}", normal_style))
        story.append(Paragraph(
            f"Grade A: {result['grade_a']} | Grade B: {result['grade_b']} | "
            f"Grade C: {result['grade_c']} | Grade D: {result['grade_d']}",
            normal_style
        ))
        story.append(Paragraph("<b>Layering (Bottom → Top):</b>", normal_style))
        for layer in result['layering']:
            story.append(Paragraph(f"• {layer['media']}: {layer['bags']} bags", normal_style))
        story.append(Spacer(1, 12))

    # --- A.C. vessels ---
    for i, result in enumerate(ac_results):
        story.append(Paragraph(
            f"<b>Activated Carbon Vessel {i+1} — {result['vessel_model']}</b>",
            heading_style
        ))
        story.append(Paragraph(f"A.C. Bags: {result['ac_bags']}", normal_style))
        story.append(Paragraph("<b>Layering (Bottom → Top):</b>", normal_style))
        for layer in result['layering']:
            story.append(Paragraph(f"• {layer['media']}: {layer['bags']} bags", normal_style))
        if use_extra_sand and shared_b_per_vessel > 0:
            half = round(shared_b_per_vessel / 2, 2)
            story.append(Paragraph(
                f"<i>Shared Grade B from +2 extra bags: {half} bags top + {half} bags bottom</i>",
                italic_style
            ))
        story.append(Spacer(1, 12))

    # --- Resin vessels ---
    for i, result in enumerate(resin_results):
        story.append(Paragraph(
            f"<b>Resin Vessel {i+1} — {result['vessel_model']}</b>", heading_style
        ))
        story.append(Paragraph(f"Resin Bags: {result['resin_bags']}", normal_style))
        story.append(Paragraph("<b>Layering (Bottom → Top):</b>", normal_style))
        for layer in result['layering']:
            story.append(Paragraph(f"• {layer['media']}: {layer['bags']} bags", normal_style))
        if use_extra_sand and shared_b_per_vessel > 0:
            half = round(shared_b_per_vessel / 2, 2)
            story.append(Paragraph(
                f"<i>Shared Grade B from +2 extra bags: {half} bags top + {half} bags bottom</i>",
                italic_style
            ))
        story.append(Spacer(1, 12))

    # --- Alumina vessels ---
    for i, result in enumerate(alumina_results):
        story.append(Paragraph(
            f"<b>Activated Alumina Vessel {i+1} — {result['vessel_model']}</b>",
            heading_style
        ))
        story.append(Paragraph(f"Alumina Bags: {result['alumina_bags']}", normal_style))
        story.append(Paragraph("<b>Layering (Bottom → Top):</b>", normal_style))
        for layer in result['layering']:
            story.append(Paragraph(f"• {layer['media']}: {layer['bags']} bags", normal_style))
        if use_extra_sand and shared_b_per_vessel > 0:
            half = round(shared_b_per_vessel / 2, 2)
            story.append(Paragraph(
                f"<i>Shared Grade B from +2 extra bags: {half} bags top + {half} bags bottom</i>",
                italic_style
            ))
        story.append(Spacer(1, 12))

    # --- Mixed Bed vessels ---
    for i, result in enumerate(mixed_results):
        story.append(Paragraph(
            f"<b>Mixed Bed Vessel {i+1} — {result['vessel_model']}</b>", heading_style
        ))
        story.append(Paragraph(
            f"Sand: A={result['grade_a']} | B={result['grade_b']} | "
            f"C={result['grade_c']} | D={result['grade_d']}",
            normal_style
        ))
        story.append(Paragraph(f"A.C. Bags: {result['ac_bags']}", normal_style))
        story.append(Paragraph("<b>Layering (Bottom → Top):</b>", normal_style))
        for layer in result['layering']:
            story.append(Paragraph(f"• {layer['media']}: {layer['bags']} bags", normal_style))
        story.append(Spacer(1, 12))

    # --- Summary table ---
    story.append(Paragraph("<b>TOTAL ORDER SUMMARY</b>", heading_style))
    story.append(Spacer(1, 10))

    table_data = [["Media Type", "Grade", "Bags"]]
    if summary["sand"]["total"] > 0:
        table_data.append(["Sand", "Grade A", str(summary["sand"]["grade_a"])])
        table_data.append(["Sand", "Grade B", str(summary["sand"]["grade_b"])])
        table_data.append(["Sand", "Grade C", str(summary["sand"]["grade_c"])])
        table_data.append(["Sand", "Grade D", str(summary["sand"]["grade_d"])])
        table_data.append(["Sand", "TOTAL", str(summary["sand"]["total"])])
    if summary["ac"]["total"] > 0:
        table_data.append(["Activated Carbon", "—", str(summary["ac"]["total"])])
    if summary["resin"]["total"] > 0:
        table_data.append(["Resin", "—", str(summary["resin"]["total"])])
    if summary["alumina"]["total"] > 0:
        table_data.append(["Activated Alumina", "—", str(summary["alumina"]["total"])])
    if summary["mixed"]["ac"] > 0:
        table_data.append(["Mixed Bed — Sand A", "—", str(summary["mixed"]["sand_a"])])
        table_data.append(["Mixed Bed — Sand B", "—", str(summary["mixed"]["sand_b"])])
        table_data.append(["Mixed Bed — Sand C", "—", str(summary["mixed"]["sand_c"])])
        table_data.append(["Mixed Bed — Sand D", "—", str(summary["mixed"]["sand_d"])])
        table_data.append(["Mixed Bed — A.C.", "—", str(summary["mixed"]["ac"])])

    table = Table(table_data, colWidths=[200, 100, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, -1), 'Times-Roman'),
        ('FONTNAME', (0, 0), (-1, 0), 'Times-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))
    story.append(table)

    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "Note: For small vessel systems, the +2 extra Grade B bags are split equally across all "
        "support vessels (A.C., Resin, Alumina). For large vessel systems, the support sand is "
        "calculated separately using the 20% rule.",
        italic_style
    ))

    # ============================================================
    # BUILD PDF WITH FOOTER ON EVERY PAGE
    # ============================================================
    doc.build(
        story,
        onFirstPage=draw_footer,
        onLaterPages=draw_footer,
    )
    buf.seek(0)
    return buf


# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.header("🔧 System Configuration")
st.sidebar.subheader("Select Media Types")

use_sand = st.sidebar.checkbox("Sand Vessel", value=True)
use_ac = st.sidebar.checkbox("Activated Carbon (A.C.)", value=True)
use_resin = st.sidebar.checkbox("Softener Resin", value=True)
use_alumina = st.sidebar.checkbox("Activated Alumina", value=True)
use_mixed = st.sidebar.checkbox("Mixed Bed (Sand + A.C.)", value=False)


# ============================================================
# SESSION STATE
# ============================================================
if "sand_models" not in st.session_state:
    st.session_state.sand_models = ["1354"]
if "ac_models" not in st.session_state:
    st.session_state.ac_models = ["1354"]
if "resin_models" not in st.session_state:
    st.session_state.resin_models = ["1354"]
if "alumina_models" not in st.session_state:
    st.session_state.alumina_models = ["1354"]
if "mixed_models" not in st.session_state:
    st.session_state.mixed_models = ["1354"]


# ============================================================
# HELPER — RENDER MEDIA INPUTS
# ============================================================
def render_media_inputs(label, key, use_flag, icon):
    if not use_flag:
        return
    st.subheader(f"{icon} {label}")
    for i in range(len(st.session_state[key])):
        col_a, col_b = st.columns([4, 1])
        with col_a:
            st.session_state[key][i] = st.text_input(
                f"{label} Vessel {i+1} Model",
                value=st.session_state[key][i],
                key=f"{key}_input_{i}"
            )
        with col_b:
            st.write("")
            st.write("")
            if st.button("❌", key=f"{key}_remove_{i}"):
                st.session_state[key].pop(i)
                st.rerun()
    if st.button(f"➕ Add {label} Vessel", key=f"{key}_add"):
        st.session_state[key].append("")
        st.rerun()
    st.markdown("---")


# ============================================================
# MAIN INPUTS
# ============================================================
st.header("📋 Vessel Inputs")

render_media_inputs("Sand", "sand_models", use_sand, "🌱")
render_media_inputs("Activated Carbon", "ac_models", use_ac, "⚫")
render_media_inputs("Resin", "resin_models", use_resin, "💧")
render_media_inputs("Activated Alumina", "alumina_models", use_alumina, "🔵")
render_media_inputs("Mixed Bed", "mixed_models", use_mixed, "🔄")


# ============================================================
# CALCULATE BUTTON
# ============================================================
if st.button("🚀 Calculate", type="primary"):
    st.header("📊 Results")

    num_support_vessels = sum([
        1 if use_ac and any(m.strip() for m in st.session_state.ac_models) else 0,
        1 if use_resin and any(m.strip() for m in st.session_state.resin_models) else 0,
        1 if use_alumina and any(m.strip() for m in st.session_state.alumina_models) else 0,
    ])

    sand_results = []
    total_sand_bags_across_all = 0
    if use_sand:
        for model in st.session_state.sand_models:
            if model.strip():
                result = calculate_sand(model.strip())
                sand_results.append(result)
                total_sand_bags_across_all += result["total_bags"]

    is_large_vessel = total_sand_bags_across_all > 6
    use_extra_sand = not is_large_vessel and use_sand

    shared_b_per_vessel = 0.0
    if use_extra_sand and num_support_vessels > 0:
        shared_b_per_vessel = 2.0 / num_support_vessels

    ac_results = []
    resin_results = []
    alumina_results = []
    mixed_results = []

    if use_ac:
        for model in st.session_state.ac_models:
            if model.strip():
                ac_results.append(calculate_activated_carbon(model.strip(), use_extra_sand=use_extra_sand))
    if use_resin:
        for model in st.session_state.resin_models:
            if model.strip():
                resin_results.append(calculate_resin(model.strip(), use_extra_sand=use_extra_sand))
    if use_alumina:
        for model in st.session_state.alumina_models:
            if model.strip():
                alumina_results.append(calculate_activated_alumina(model.strip(), use_extra_sand=use_extra_sand))
    if use_mixed:
        for model in st.session_state.mixed_models:
            if model.strip():
                mixed_results.append(calculate_mixed_bed(model.strip()))

    # --- Per-vessel results ---
    st.subheader("📦 Per-Vessel Breakdown")

    for i, result in enumerate(sand_results):
        with st.expander(f"🌱 Sand Vessel {i+1} — {result['vessel_model']}", expanded=True):
            st.write(f"**Total Sand Bags Required:** {result['total_bags']} bags")
            st.write("**Grade Distribution:**")
            st.write(f"- Grade A: {result['grade_a']} bags")
            st.write(f"- Grade B: {result['grade_b']} bags")
            st.write(f"- Grade C: {result['grade_c']} bags")
            st.write(f"- Grade D: {result['grade_d']} bags")
            st.write("**Layering (Bottom → Top):**")
            for layer in result['layering']:
                st.write(f"- {layer['media']}: {layer['bags']} bags")
            img_buf = generate_layering_image(result['layering'], result['vessel_model'], freeboard=0.30)
            st.image(img_buf, caption=f"Layering Diagram — Vessel {result['vessel_model']}")

    for i, result in enumerate(ac_results):
        with st.expander(f"⚫ Activated Carbon Vessel {i+1} — {result['vessel_model']}", expanded=True):
            st.write(f"**A.C. Bags Required:** {result['ac_bags']} bags")
            layers = list(result['layering'])
            if use_extra_sand and shared_b_per_vessel > 0:
                half = round(shared_b_per_vessel / 2, 2)
                layers = [{"media": "Grade B (top)", "bags": half}] + layers + [{"media": "Grade B (bottom)", "bags": half}]
                st.info(f"Shared Grade B from +2 extra bags: {half} bags top + {half} bags bottom")
            st.write("**Layering (Bottom → Top):**")
            for layer in layers:
                st.write(f"- {layer['media']}: {layer['bags']} bags")
            img_buf = generate_layering_image(layers, result['vessel_model'], freeboard=0.40)
            st.image(img_buf, caption=f"Layering Diagram — Vessel {result['vessel_model']}")

    for i, result in enumerate(resin_results):
        with st.expander(f"💧 Resin Vessel {i+1} — {result['vessel_model']}", expanded=True):
            st.write(f"**Resin Bags Required:** {result['resin_bags']} bags")
            layers = list(result['layering'])
            if use_extra_sand and shared_b_per_vessel > 0:
                half = round(shared_b_per_vessel / 2, 2)
                layers = [{"media": "Grade B (top)", "bags": half}] + layers + [{"media": "Grade B (bottom)", "bags": half}]
                st.info(f"Shared Grade B from +2 extra bags: {half} bags top + {half} bags bottom")
            st.write("**Layering (Bottom → Top):**")
            for layer in layers:
                st.write(f"- {layer['media']}: {layer['bags']} bags")
            img_buf = generate_layering_image(layers, result['vessel_model'], freeboard=0.50)
            st.image(img_buf, caption=f"Layering Diagram — Vessel {result['vessel_model']}")

    for i, result in enumerate(alumina_results):
        with st.expander(f"🔵 Alumina Vessel {i+1} — {result['vessel_model']}", expanded=True):
            st.write(f"**Alumina Bags Required:** {result['alumina_bags']} bags")
            layers = list(result['layering'])
            if use_extra_sand and shared_b_per_vessel > 0:
                half = round(shared_b_per_vessel / 2, 2)
                layers = [{"media": "Grade B (top)", "bags": half}] + layers + [{"media": "Grade B (bottom)", "bags": half}]
                st.info(f"Shared Grade B from +2 extra bags: {half} bags top + {half} bags bottom")
            st.write("**Layering (Bottom → Top):**")
            for layer in layers:
                st.write(f"- {layer['media']}: {layer['bags']} bags")
            img_buf = generate_layering_image(layers, result['vessel_model'], freeboard=0.40)
            st.image(img_buf, caption=f"Layering Diagram — Vessel {result['vessel_model']}")

    for i, result in enumerate(mixed_results):
        with st.expander(f"🔄 Mixed Bed Vessel {i+1} — {result['vessel_model']}", expanded=True):
            st.write(f"**Sand Total Bags:** {result['sand_total_bags']} bags")
            st.write(f"- Grade A: {result['grade_a']} bags")
            st.write(f"- Grade B: {result['grade_b']} bags")
            st.write(f"- Grade C: {result['grade_c']} bags")
            st.write(f"- Grade D: {result['grade_d']} bags")
            st.write(f"**A.C. Bags Required:** {result['ac_bags']} bags")
            st.write("**Layering (Bottom → Top):**")
            for layer in result['layering']:
                st.write(f"- {layer['media']}: {layer['bags']} bags")
            img_buf = generate_layering_image(result['layering'], result['vessel_model'], freeboard=0.40)
            st.image(img_buf, caption=f"Layering Diagram — Vessel {result['vessel_model']}")

    # --- Summary ---
    st.subheader("🧾 Total Order Summary")

    system = {}
    if sand_results:
        agg_sand = {"grade_a": 0, "grade_b": 0, "grade_c": 0, "grade_d": 0, "total_bags": 0}
        for r in sand_results:
            agg_sand["grade_a"] += r["grade_a"]
            agg_sand["grade_b"] += r["grade_b"]
            agg_sand["grade_c"] += r["grade_c"]
            agg_sand["grade_d"] += r["grade_d"]
            agg_sand["total_bags"] += r["total_bags"]
        system["sand"] = agg_sand

    if ac_results:
        system["ac"] = {"ac_bags": sum(r["ac_bags"] for r in ac_results)}
    if resin_results:
        system["resin"] = {"resin_bags": sum(r["resin_bags"] for r in resin_results)}
    if alumina_results:
        system["alumina"] = {"alumina_bags": sum(r["alumina_bags"] for r in alumina_results)}
    if mixed_results:
        agg_mixed = {"grade_a": 0, "grade_b": 0, "grade_c": 0, "grade_d": 0, "ac_bags": 0}
        for r in mixed_results:
            agg_mixed["grade_a"] += r["grade_a"]
            agg_mixed["grade_b"] += r["grade_b"]
            agg_mixed["grade_c"] += r["grade_c"]
            agg_mixed["grade_d"] += r["grade_d"]
            agg_mixed["ac_bags"] += r["ac_bags"]
        system["mixed"] = agg_mixed

    summary = calculate_system_summary(system)

    if summary["sand"]["total"] > 0:
        st.write("**SAND (50 kg bags):**")
        st.write(f"- Grade A: {summary['sand']['grade_a']} bags")
        st.write(f"- Grade B: {summary['sand']['grade_b']} bags")
        st.write(f"- Grade C: {summary['sand']['grade_c']} bags")
        st.write(f"- Grade D: {summary['sand']['grade_d']} bags")
        st.write(f"- **Total Sand: {summary['sand']['total']} bags**")
    if summary["ac"]["total"] > 0:
        st.write(f"**ACTIVATED CARBON (25 kg bags):** {summary['ac']['total']} bags")
    if summary["resin"]["total"] > 0:
        st.write(f"**RESIN (25 kg bags):** {summary['resin']['total']} bags")
    if summary["alumina"]["total"] > 0:
        st.write(f"**ACTIVATED ALUMINA (25 kg bags):** {summary['alumina']['total']} bags")
    if summary["mixed"]["ac"] > 0:
        st.write("**MIXED BED:**")
        st.write(f"- Sand (Grade A): {summary['mixed']['sand_a']} bags")
        st.write(f"- Sand (Grade B): {summary['mixed']['sand_b']} bags")
        st.write(f"- Sand (Grade C): {summary['mixed']['sand_c']} bags")
        st.write(f"- Sand (Grade D): {summary['mixed']['sand_d']} bags")
        st.write(f"- Activated Carbon: {summary['mixed']['ac']} bags")

    st.info(
        "**Note:** For small vessel systems, the +2 extra Grade B bags are split equally across all "
        "support vessels (A.C., Resin, Alumina). Each support vessel shows half of its share at the top "
        "and half at the bottom. For large vessel systems, the support sand is calculated separately "
        "using the 20% rule (50% Grade C bottom, 25% Grade B middle, 25% Grade B top)."
    )

    # --- PDF Download ---
    st.markdown("---")
    st.subheader("📄 Download Report")
    pdf_buffer = generate_pdf_report(
        sand_results, ac_results, resin_results, alumina_results,
        mixed_results, summary, shared_b_per_vessel, use_extra_sand
    )
    st.download_button(
        label="📄 Download PDF Report",
        data=pdf_buffer,
        file_name=f"FRP_Vessel_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
        mime="application/pdf"
    )
    