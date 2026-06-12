import os 
import uuid
import matplotlib
matplotlib.use('Agg')
import logging
import matplotlib.pyplot as plt
# ticker is for formating the numbers in charts
import matplotlib.ticker as mticker
import pandas as pd

from datetime import datetime
# reportlab is for creating PDF
# A4 is the standard page size in many words for creating PDF
from reportlab.lib.pagesizes import A4 
from reportlab.lib import colors
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
    )
# cm is for controlling the standard margin
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image,
    Table, TableStyle, HRFlowable, PageBreak
)
# TA_CENTER is for centring the text inside the PDF
from reportlab.lib.enums import TA_CENTER
from config import CHART_DIR, REPORTS_DIR, PALETTE
from data_loader import (
    df,
    NUMERIC_COLS,
    CATEGORICAL_COLS,
    DATE_COLS,
    CAT_VALUES
)

logger = logging.getLogger(__name__)

def safe(val):
    """
    converts any value to a string.
    Handles NaT, NaN without crashing.
    Reportlab accept just strings and dates.
    """
    if val is None:
        return ""
    # converts any NaN to an empty string
    # NaN has for float type
    if isinstance(val, float) and pd.isna(val):
        return ""
    try:
        if pd.isnull(val):
            return ""
    except Exception as e:
        pass

    # Checks if the value accepts the 'strftime' method
    if hasattr(val, 'strftime'):
        return val.strftime('%Y-%m-%d')
    
    return str(val)

def best_num():
    """
    Gets the numerical column the user mention in the question.
    """
    for keyword in ['sales','revenue','profit','amount','total','price']:
        for col in NUMERIC_COLS:
            if keyword in col:
                return col
            
    return (
        NUMERIC_COLS[0] 
        if NUMERIC_COLS 
        else None
    )

def best_cat():
    """
    Gets the categorical column the user mention in the question.
    """
    for col in CATEGORICAL_COLS:
        n = df[col].nunique()
        if 2 <= n <=60:
            return col
        
    return (
        CATEGORICAL_COLS[0]
        if CATEGORICAL_COLS
        else df.columns[0]
    )

def pick_columns(question):
    q = question.lower()
    num = None
    for c in NUMERIC_COLS:
        words = c.replace('_', ' ').split()
        if any(w in q for w in words):
            num = c
            break
    if num is None:
        num = best_num()

    cat = None
    for c in CATEGORICAL_COLS:
        words = c.replace('_', ' ').split()
        if any(w in q for w in words):
            cat = c
            break
    if cat is None:
        cat = best_cat()

    return num, cat

def parse_filters(question):
    """
    exctract all the filters keywords from the question.
    assign these filters in a dictionary so they can be easily called.
    """
    q = question.lower()
    filters = {
        'category': None,
        'segment': None,
        'region': None,
        'ship_mode': None,
        'year': None,
        'state': None
    }
    text_filters = ['category', 'segment', 'region', 'ship_mode', 'state']
    for col in text_filters:
        if col not in CAT_VALUES:
            continue

        for value in CAT_VALUES[col]:
            if value.lower() in q:
                filters[col] = value
                break
    words = question.replace(',', ' ').replace('.', ' ').split()
    for word in words:
                clean = "".join(c for c in word if c.isdigit())
                if len(clean) == 4:
                    year_candidate = int(clean)
                    if 2000 <= year_candidate <=2026:
                        filters['year'] = year_candidate
                        break
    
    return filters

def apply_filters(data, filters):
    """
    Apply the filters that the user mentioned.
    so we don't get everytime all the data and choose the ones we need.
    """
    description_parts = []

    logger.info(f"Rows before filters: {len(data)}")
    if filters['category'] and 'category' in data.columns:
        data = data[
            data["category"].str.lower() == filters["category"].lower()
        ]
        description_parts.append(filters["category"])
        logger.info(f"After category filter: {len(data)}")

    if filters["segment"] and "segment" in data.columns:
        data = data[
            data["segment"].str.lower() == filters["segment"].lower()
        ]
        description_parts.append(filters["segment"])
        logger.info(f"After segment filter: {len(data)}")

    if filters["region"] and "region" in data.columns:
        data = data[
            data["region"].str.lower() == filters["region"].lower()
        ]
        description_parts.append(filters["region"])
        logger.info(f"After region filter: {len(data)}")

    if filters["ship_mode"] and "ship_mode" in data.columns:
        data = data[
            data["ship_mode"].str.lower() == filters["ship_mode"].lower()
        ]
        description_parts.append(filters["ship_mode"])
        logger.info(f"After ship Mode filter: {len(data)}")

    if filters["state"] and "state" in data.columns:
        data = data[
            data["state"].str.lower() == filters["state"].lower()
        ]
        description_parts.append(filters["state"])
        logger.info(f"After state filter: {len(data)}")

    if filters["year"]:
        date_col = 'order_date' if 'order_date' in data.columns else None

        logger.info(f"Date column found: {date_col}")

        if date_col:
            logger.info(
            f"Years available: {data[date_col].dt.year.unique()}"
            )

            data = data[
                data[date_col].dt.year == filters["year"]
            ]

            logger.info(
            f"Rows after year filter: {len(data)}"
            )

            description_parts.append(str(filters["year"]))
            
    if description_parts:
        description = ' · '.join(description_parts)
    else:
        description = 'Full sales overview'
        logger.info(f"After year filter: {len(data)}")

    return data, description

def save(fig):
    """
    Saves a matplotlib figure and returns the file path.
    """
    # 'hex[:8]' creates just 8 unique id
    fname = f'rpt_{uuid.uuid4().hex[:8]}.png'
    fpath = os.path.join(CHART_DIR, fname)
    plt.savefig(fpath, dpi=120, bbox_inches="tight", facecolor="#0f1117")
    plt.close("all")
    return fpath

def style(ax, title, xlabel="", ylabel=""):
    """
    Applies the parameters to all the charts.
    """
    ax.figure.patch.set_facecolor("#0f1117")
    ax.set_facecolor("#1a1d27")
    ax.set_title(title, color="#e8eaf0", fontsize=12, pad=10, fontweight="bold")
    ax.set_xlabel(xlabel, color="#9ca3af", fontsize=9)
    ax.set_ylabel(ylabel, color="#9ca3af", fontsize=9)
    # Control the numbers on axes
    ax.tick_params(colors="#9ca3af", labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor("#2d3047")
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(
            lambda x, _: f"{x:,.0f}" if abs(x) >= 1 else f"{x:.2f}"
        )
    )
    ax.grid(axis="y", color="#2d3047", linewidth=0.5, linestyle="--", alpha=0.6)

def make_charts(data, col, cat_col):
    """
    Creates three charts from the filtered data:
    - bar chart: values by category
    - pie chart: share by category
    - trend chart: monthly trend over time (if date column exists) 
    """

    charts = {}
    top = (
        data.groupby(cat_col)[col]
        .sum()
        .sort_values(ascending=False)
        .head(15)
    )
    fig, ax = plt.subplots(figsize=(9, 4))
    ax.bar(
        range(len(top)),
        top.values,
        color=[PALETTE[i % len(PALETTE)] for i in range(len(top))],
        edgecolor="#0f1117",
    )
    ax.set_xticks(range(len(top)))
    ax.set_xticklabels(top.index, rotation=40, ha="right", fontsize=8)
    for i, v in enumerate(top.values):
        ax.text(
            i, v * 1.01, f"{v:,.0f}",
            ha="center", va="bottom",
            color="#e8eaf0", fontsize=7,
        )
    style(
        ax,
        f"{col.replace('_',' ').title()} by {cat_col.replace('_',' ').title()}",
        cat_col, col,
    )
    fig.tight_layout()
    charts["bar"] = save(fig)

    pie_d = (
        data.groupby(cat_col)[col]
        .sum()
        .sort_values(ascending=False)
        .head(8)
    )
    fig, ax = plt.subplots(figsize=(6, 6))
    _, texts, autos = ax.pie(
        pie_d.values,
        labels=pie_d.index,
        autopct="%1.1f%%",
        colors=PALETTE[:len(pie_d)],
        startangle=140,
        pctdistance=0.82,
    )
    for t in texts:
        t.set_color("#9ca3af")
        t.set_fontsize(9)
    for t in autos:
        t.set_color("#0f1117")
        t.set_fontsize(8)
        t.set_fontweight("bold")
    ax.set_title(
        f"Share by {cat_col.replace('_',' ').title()}",
        color="#e8eaf0", fontsize=11,
    )
    fig.patch.set_facecolor("#0f1117")
    fig.tight_layout()
    charts["pie"] = save(fig)

    # Only created if a date column exists in the filtered data
    date_col = next(
        (c for c in df.columns if "order" in c and "date" in c
         and c in data.columns),
        None,
    )
    if date_col:
        dated = data[[date_col, col]].copy()
        dated[date_col] = pd.to_datetime(dated[date_col], errors="coerce")
        dated = dated.dropna(subset=[date_col])
        if not dated.empty:
            trend = (
                dated.set_index(date_col)[col]
                .resample("ME")
                .sum()
                .dropna()
            )
            if len(trend) >= 2:
                fig, ax = plt.subplots(figsize=(9, 3.5))
                ax.fill_between(
                    trend.index, trend.values,
                    alpha=0.15, color=PALETTE[0],
                )
                ax.plot(
                    trend.index, trend.values,
                    color=PALETTE[0], linewidth=2,
                    marker="o", markersize=4,
                    markerfacecolor=PALETTE[2],
                )
                style(
                    ax,
                    f"Monthly {col.replace('_',' ').title()} Trend",
                    "Date", col,
                )
                fig.tight_layout()
                charts["trend"] = save(fig)

    return charts

def build_pdf(charts, kpis, data, col, cat_col, title_note):
    """
    Builds the PDF report file based on all the filters applied.
    """
    fname = f'report_{uuid.uuid4().hex[:8]}.pdf'
    fpath = os.path.join(REPORTS_DIR, fname)
    
    doc = SimpleDocTemplate(
        fpath, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )

    styles = getSampleStyleSheet()

    T = ParagraphStyle(
        "T", parent=styles["Title"],
        fontSize=20, textColor=colors.HexColor("#1F3864"),
        spaceAfter=4, alignment=TA_CENTER,
    )
    S = ParagraphStyle(
        "S", parent=styles["Normal"],
        fontSize=10, textColor=colors.HexColor("#6b7591"),
        alignment=TA_CENTER, spaceAfter=12,
    )
    H = ParagraphStyle(
        "H", parent=styles["Heading2"],
        fontSize=13, textColor=colors.HexColor("#2E75B6"),
        spaceBefore=14, spaceAfter=8,
    )
    N = ParagraphStyle(
        "N", parent=styles["Normal"],
        fontSize=9, textColor=colors.HexColor("#444"),
        spaceAfter=14,
    )
    F = ParagraphStyle(
        "F", parent=styles["Normal"],
        fontSize=8, textColor=colors.HexColor("#999"),
        alignment=TA_CENTER,
    )

    story = []
    story += [
        Spacer(1, 1*cm),
        Paragraph('Sales Intelligence Report', T),
        Paragraph(
            f'Generated {datetime.now().strftime('%B %d, %Y %H:%M')} · NexusAI',
            S
        ),
        # title_note now shows the filter e.g. "Technology · 2021"
        Paragraph(f"Scope: {title_note}", N),
        HRFlowable(
            width="100%", thickness=2,
            color=colors.HexColor("#2E75B6"),
            spaceAfter=16,
        ),
    ]

    # ── KPI table ─────────────────────────────────────────────
    story.append(Paragraph("Key Performance Indicators", H))
    rows = [
        ["Metric", "Value"],
        [f"Total {col.replace('_',' ').title()}",   f"{kpis['total']:,.2f}"],
        ["Average per record",                       f"{kpis['avg']:,.2f}"],
        ["Records analysed",                         f"{kpis['count']:,}"],
        [f"Top {cat_col.replace('_',' ').title()}",  safe(kpis['top_item'])],
        ["Top value",                                f"{kpis['top_val']:,.2f}"],
        [f"Unique {cat_col.replace('_',' ').title()}s", str(kpis['n_cats'])],
    ]
    t = Table(rows, colWidths=[9*cm, 8*cm])
    t.setStyle(TableStyle([
        ("BACKGROUND",     (0,0), (-1,0), colors.HexColor("#1F3864")),
        ("TEXTCOLOR",      (0,0), (-1,0), colors.white),
        ("FONTNAME",       (0,0), (-1,0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1),
         [colors.HexColor("#EAF2FB"), colors.white]),
        ("FONTSIZE",       (0,0), (-1,-1), 10),
        ("GRID",           (0,0), (-1,-1), 0.5, colors.HexColor("#CCC")),
        ("LEFTPADDING",    (0,0), (-1,-1), 10),
        ("TOPPADDING",     (0,0), (-1,-1), 7),
        ("BOTTOMPADDING",  (0,0), (-1,-1), 7),
    ]))
    story += [t, Spacer(1, 0.5*cm)]

    # ── Charts ────────────────────────────────────────────────
    story += [
        Paragraph(
            f"{col.replace('_',' ').title()} by "
            f"{cat_col.replace('_',' ').title()}",
            H,
        ),
        Image(charts["bar"], width=16*cm, height=7*cm),
        Spacer(1, 0.4*cm),
    ]
    if "trend" in charts:
        story += [
            Paragraph("Monthly Trend", H),
            Image(charts["trend"], width=16*cm, height=6*cm),
            Spacer(1, 0.4*cm),
        ]
    story.append(PageBreak())
    story += [
        Paragraph("Distribution", H),
        Image(charts["pie"], width=10*cm, height=10*cm),
        Spacer(1, 0.4*cm),
    ]

    # ── Full breakdown table ───────────────────────────────────
    story.append(Paragraph("Complete Breakdown", H))
    summary = (
        data.groupby(cat_col)[col]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )
    total_v       = summary[col].sum()
    summary["pct"] = (summary[col] / total_v * 100).map("{:.1f}%".format)
    summary[col]   = summary[col].map("{:,.2f}".format)
    summary.columns = [
        cat_col.replace("_", " ").title(),
        col.replace("_", " ").title(),
        "Share %",
    ]
    tbl = (
        [list(summary.columns)]
        + [[safe(v) for v in r] for _, r in summary.iterrows()]
    )
    dt = Table(tbl, colWidths=[8*cm, 5*cm, 4*cm], repeatRows=1)
    dt.setStyle(TableStyle([
        ("BACKGROUND",     (0,0), (-1,0), colors.HexColor("#2E75B6")),
        ("TEXTCOLOR",      (0,0), (-1,0), colors.white),
        ("FONTNAME",       (0,0), (-1,0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1),
         [colors.HexColor("#EAF2FB"), colors.white]),
        ("FONTSIZE",       (0,0), (-1,-1), 9),
        ("GRID",           (0,0), (-1,-1), 0.4, colors.HexColor("#CCC")),
        ("LEFTPADDING",    (0,0), (-1,-1), 8),
        ("TOPPADDING",     (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",  (0,0), (-1,-1), 5),
    ]))
    story += [
        dt,
        Spacer(1, 0.5*cm),
        HRFlowable(
            width="100%", thickness=1,
            color=colors.HexColor("#CCC"),
            spaceBefore=10,
        ),
        Paragraph(
            f"NexusAI · {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            F,
        ),
    ]

    doc.build(story)
    return f"/static/reports/{fname}"
    
def generate_report(question="", lang='en'):
    """
    The main function called by orchestrator.py
    """

    try:
        col, cat_col = pick_columns(question)
        if not col:
            return {
                'text': 'No numeric column found.',
                'chart': None
            }
        
        filters = parse_filters(question)
        logger.info(f"Filters = {filters}")

        base_data = df.copy()
        # Keep just the numerical and categorical and date column if existed
        keep = [col, cat_col] + [c for c in df.columns if 'date' in c]
        # Keep just columns that exists in df.columns
        keep = [c for c in keep if c in base_data.columns]
        # remove rows that has null values in filter columns
        base_data = base_data[keep].dropna(subset=[col, cat_col])
        logger.info(f"Filters found: {filters}")
        logger.info(f"Rows before filtering: {len(base_data)}")
        print(base_data.columns.tolist())
        filtered_data, description = apply_filters(base_data, filters)
        if filtered_data.empty:
            if lang == 'fr':
                msg = (
                    f"Aucune donnée trouvée pour : {description}.\n"
                    f"Vérifiez les valeurs et réessayez."
                )
            else:
                msg = (
                    f"No data found for: {description}.\n"
                    f"Please check the values and try again."
                )
            return {
                'text': msg,
                'chart': None
                }
        
        grp = (
            filtered_data.groupby(cat_col)[col]
            .sum()
            .sort_values(ascending=False)
        )
        kpis = {
            "total":    filtered_data[col].sum(),
            "avg":      filtered_data[col].mean(),
            "count":    len(filtered_data),
            "top_item": grp.index[0]  if not grp.empty else "N/A",
            "top_val":  grp.iloc[0]   if not grp.empty else 0,
            "n_cats":   filtered_data[cat_col].nunique(),
        }
        
        charts = make_charts(filtered_data, col, cat_col)

        url = build_pdf(charts, kpis, filtered_data, col, cat_col, description)

        # Build the chat response message
        t = kpis['total']
        c = kpis['count']
        ti = safe(kpis['top_item'])
        tv = kpis['top_val']

        if lang == "fr":
            text = (
                f"✅ Rapport généré pour : {description}\n\n"
                f"📊 Points clés :\n"
                f"  • Total {col} : {t:,.2f}\n"
                f"  • Enregistrements : {c:,}\n"
                f"  • Meilleur {cat_col} : {ti} ({tv:,.2f})\n\n"
                f"📄 Téléchargez ci-dessous."
            )
        else:
            text = (
                f"✅ Report generated for: {description}\n\n"
                f"📊 Highlights:\n"
                f"  • Total {col}: {t:,.2f}\n"
                f"  • Records: {c:,}\n"
                f"  • Top {cat_col}: {ti} ({tv:,.2f})\n\n"
                f"📄 Download below."
            )

        return {"text": text, "chart": None, "report_url": url}

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"text": f"Report error: {e}", "chart": None}
