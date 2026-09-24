"""
app.py — Bangalore Market Intelligence Dashboard
Run: streamlit run app.py
(Triggering reload)
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import sys, importlib
if "ai.analyst" in sys.modules:
    importlib.reload(sys.modules["ai.analyst"])
from ai.analyst import analyse, analyse_expansion_scenario

from analytics.queries import (
    get_city_summary,
    get_market_comparison,
    get_market_detail,
    get_transactions,
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Bangalore Market Intelligence | Autopilot Offices",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.block-container { padding-top: 1.2rem !important; }
header[data-testid="stHeader"] { background: transparent; }

button[data-baseweb="tab"] {
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    padding: 0.6rem 1.2rem !important;
    color: #94a3b8 !important;
    border-radius: 6px 6px 0 0 !important;
    transition: all 0.2s ease;
}
button[data-baseweb="tab"][aria-selected="true"] {
    color: #e2e8f0 !important;
    background: rgba(59, 130, 246, 0.08) !important;
    border-bottom: 2px solid #3b82f6 !important;
}
div[data-baseweb="tab-border"] { display: none; }

div[data-testid="stMetric"] {
    background: linear-gradient(135deg, #0c1929 0%, #111d2e 100%);
    border: 1px solid #1e3a5f;
    border-radius: 10px;
    padding: 0.8rem 1rem 0.7rem 1rem;
    transition: border-color 0.2s ease;
}
div[data-testid="stMetric"]:hover { border-color: #3b82f6; }
div[data-testid="stMetric"] label {
    color: #64748b !important;
    font-size: 0.72rem !important;
    font-weight: 500 !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    font-size: 1.3rem !important;
    font-weight: 600 !important;
    color: #e2e8f0 !important;
}
div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
    font-size: 0.72rem !important;
}

.section-hdr {
    font-size: 0.92rem;
    font-weight: 600;
    color: #cbd5e1;
    border-bottom: 1px solid rgba(59, 130, 246, 0.25);
    padding-bottom: 0.4rem;
    margin: 1.5rem 0 0.8rem 0;
    letter-spacing: 0.01em;
}

.market-card {
    background: linear-gradient(135deg, #0c1929, #111d2e);
    border: 1px solid #1e3a5f;
    border-left: 3px solid #3b82f6;
    border-radius: 0 10px 10px 0;
    padding: 0.75rem 1rem;
    margin-bottom: 0.5rem;
    transition: border-color 0.2s ease, transform 0.15s ease;
}
.market-card:hover { border-color: #3b82f6; transform: translateX(2px); }
.market-card-name { font-weight: 600; font-size: 0.88rem; color: #93c5fd; }
.market-card-sub  { font-size: 0.78rem; color: #94a3b8; margin-top: 0.2rem; line-height: 1.5; }

.note-box {
    background: linear-gradient(135deg, #0c1929, #0f2132);
    border: 1px solid #1e3a5f;
    border-radius: 10px;
    padding: 0.85rem 1.2rem;
    font-size: 0.82rem;
    color: #94a3b8;
    margin-bottom: 1.2rem;
    line-height: 1.55;
}

.insight-card {
    background: linear-gradient(135deg, #0c2340, #0f2d4a);
    border-left: 4px solid #3b82f6;
    border-radius: 0 12px 12px 0;
    padding: 1.1rem 1.4rem;
    font-size: 1rem;
    color: #e2e8f0;
    line-height: 1.65;
    margin: 0.5rem 0 1rem 0;
}

.intent-badge {
    background: rgba(59, 130, 246, 0.08);
    border: 1px solid #1e3a5f;
    border-radius: 8px;
    padding: 0.45rem 1rem;
    font-size: 0.78rem;
    color: #64748b;
    margin-bottom: 1rem;
    display: inline-block;
}
.intent-badge b { color: #93c5fd; }

.evidence-item {
    background: rgba(16, 185, 129, 0.06);
    border: 1px solid rgba(16, 185, 129, 0.15);
    border-radius: 6px;
    padding: 0.35rem 0.75rem;
    margin-bottom: 0.35rem;
    font-size: 0.82rem;
    color: #a7f3d0;
}

.footnote {
    margin-top: 1.5rem;
    padding: 0.65rem 1rem;
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid #1e293b;
    border-radius: 8px;
    font-size: 0.73rem;
    color: #64748b;
    line-height: 1.55;
}

div[data-testid="stExpander"] {
    border: 1px solid #1e3a5f !important;
    border-radius: 10px !important;
    margin-bottom: 0.6rem;
}

div[data-testid="stDataFrame"] {
    border: 1px solid #1e3a5f;
    border-radius: 10px;
    overflow: hidden;
}

button[kind="primary"] {
    background: linear-gradient(135deg, #2563eb, #3b82f6) !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em;
}

div.stButton > button[kind="secondary"] {
    border: 1px solid #1e3a5f !important;
    border-radius: 8px !important;
    color: #94a3b8 !important;
    font-size: 0.78rem !important;
    padding: 0.4rem 0.8rem !important;
    text-align: left !important;
    transition: all 0.2s ease;
}
div.stButton > button[kind="secondary"]:hover {
    border-color: #3b82f6 !important;
    color: #e2e8f0 !important;
    background: rgba(59, 130, 246, 0.06) !important;
}

hr { border-color: rgba(30, 58, 95, 0.4) !important; margin: 1rem 0 !important; }
</style>
""", unsafe_allow_html=True)

# ── Design constants ──────────────────────────────────────────────────────────
MARKET_COLORS = {
    "ORR":               "#3b82f6",
    "Whitefield":        "#10b981",
    "SBD":               "#a78bfa",
    "North Bangalore":   "#fb923c",
    "Electronic City":   "#f43f5e",
    "Central Bangalore": "#e879f9",
    "PBD West":          "#22d3ee",
    "Koramangala":       "#a3e635",
    "Hebbal":            "#fbbf24",
    "Marathahalli":      "#34d399",
}

BASE_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", size=12, color="#cbd5e1"),
    margin=dict(l=10, r=20, t=40, b=10),
)

# ── Cached data loaders ───────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def _city():     return get_city_summary()
@st.cache_data(ttl=300)
def _markets():  return get_market_comparison()
@st.cache_data(ttl=300)
def _txns():     return get_transactions()

# ── Signal helpers ────────────────────────────────────────────────────────────
def vac_signal(v):
    if v < 8:   return "🟢 Tight"
    if v < 15:  return "🟡 Moderate"
    return "🔴 High"

def vac_color(v):
    if v < 8:   return "#34d399"
    if v < 15:  return "#fbbf24"
    return "#f87171"

def comp_signal(level):
    return {"High": "🔴 High", "Medium": "🟡 Medium",
            "Low": "🟢 Low", "None": "⚪ None"}.get(level, level)

def rank3(series, ascending=True):
    """Rank a numeric series into Low / Medium / High thirds."""
    p33, p67 = series.quantile(0.33), series.quantile(0.67)
    def _label(x):
        if ascending:
            return "Low" if x <= p33 else ("Medium" if x <= p67 else "High")
        return "High" if x <= p33 else ("Medium" if x <= p67 else "Low")
    return series.apply(_label)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1: Market Overview
# ══════════════════════════════════════════════════════════════════════════════
def render_overview():
    city = _city()
    mf   = _markets()

    q1 = city[city["period"] == "Q1-2026"].iloc[0]
    q2 = city[city["period"] == "Q2-2026"].iloc[0]

    total_supply  = mf["grade_a_supply_msf"].sum()
    h1_absorption = q1["net_absorption_msf"] + q2["net_absorption_msf"]
    h1_supply     = q1["new_supply_msf"]     + q2["new_supply_msf"]
    h1_leasing    = q1["gross_leasing_msf"]  + q2["gross_leasing_msf"]
    vac_delta     = q2["vacancy_pct"]        - q1["vacancy_pct"]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Grade A Supply",     f"{total_supply:.0f} MSF")
    c2.metric("City Vacancy (Q2)",  f"{q2['vacancy_pct']:.1f}%",
              delta=f"{vac_delta:+.1f}pp vs Q1", delta_color="inverse")
    c3.metric("H1 Net Absorption",  f"{h1_absorption:.1f} MSF")
    c4.metric("H1 New Supply",      f"{h1_supply:.1f} MSF")
    c5.metric("H1 Gross Leasing",   f"{h1_leasing:.1f} MSF")

    st.markdown("")

    col_l, col_r = st.columns([3, 2])

    with col_l:
        st.markdown('<p class="section-hdr">Q1 vs Q2 2026 — City Metrics (MSF)</p>',
                    unsafe_allow_html=True)
        metrics = ["net_absorption_msf", "gross_leasing_msf", "new_supply_msf"]
        labels  = ["Net Absorption", "Gross Leasing", "New Supply"]
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name="Q1-2026", x=labels,
            y=[q1[m] for m in metrics],
            marker_color="#334155",
            text=[f"{q1[m]:.1f}" for m in metrics], textposition="outside",
        ))
        fig.add_trace(go.Bar(
            name="Q2-2026", x=labels,
            y=[q2[m] for m in metrics],
            marker_color="#3b82f6",
            text=[f"{q2[m]:.1f}" for m in metrics], textposition="outside",
        ))
        fig.update_layout(**BASE_LAYOUT, barmode="group",
                          yaxis_title="MSF", height=320,
                          legend=dict(orientation="h", yanchor="bottom", y=1.02))
        st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.markdown('<p class="section-hdr">Grade A Supply by Micro-Market</p>',
                    unsafe_allow_html=True)
        fig = go.Figure(go.Pie(
            labels=mf["market_name"],
            values=mf["grade_a_supply_msf"],
            hole=0.5,
            marker_colors=[MARKET_COLORS.get(m, "#3b82f6") for m in mf["market_name"]],
            textinfo="percent",
            textposition="inside",
            hovertemplate="<b>%{label}</b><br>%{value:.1f} MSF (%{percent})<extra></extra>",
        ))
        fig.update_layout(**BASE_LAYOUT, height=320,
                          showlegend=True, legend=dict(font=dict(size=10)))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<p class="section-hdr">Market at a Glance</p>', unsafe_allow_html=True)
    cols = st.columns(2)
    for i, (_, row) in enumerate(mf.iterrows()):
        parts = []
        parts.append(f"vacancy {row['vacancy_pct']:.0f}% — "
                     + ("tight market" if row["vacancy_pct"] < 8
                        else "high availability" if row["vacancy_pct"] > 15
                        else "moderate availability"))
        if row["absorption_msf"] >= 0.5:
            parts.append(f"strong leasing demand ({row['absorption_msf']:.2f} MSF absorbed)")
        else:
            parts.append(f"limited absorption ({row['absorption_msf']:.2f} MSF)")
        if row["competition_level"] == "None":
            parts.append("no established managed-office operators")
        elif row["competition_level"] == "High":
            parts.append(f"heavy managed-office competition ({row['operator_count']} operators)")
        with cols[i % 2]:
            st.markdown(f"""
<div class="market-card">
  <div class="market-card-name">📍 {row['market_name']}
    &nbsp;<span style="color:#64748b;font-weight:400;font-size:0.75rem">
    ₹{row['avg_asking_rent']:.0f}/sqft/mo</span>
  </div>
  <div class="market-card-sub">{" · ".join(parts).capitalize()}.</div>
</div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2: Micro-Market Comparison
# ══════════════════════════════════════════════════════════════════════════════
def render_comparison():
    df   = _markets()
    txns = _txns()

    st.markdown('<p class="section-hdr">Key Metrics — All Micro-Markets</p>',
                unsafe_allow_html=True)

    tbl = df[["market_name", "grade_a_supply_msf", "vacancy_pct",
              "avg_asking_rent", "absorption_msf", "new_supply_msf",
              "competition_level"]].copy()
    tbl["Vacancy Signal"] = df["vacancy_pct"].apply(vac_signal)
    tbl["Competition"]    = df["competition_level"].apply(comp_signal)
    tbl.columns = ["Market", "Supply (MSF)", "Vacancy %", "Rent ₹/sqft",
                   "Absorption MSF", "New Supply MSF", "Comp. Level",
                   "Vacancy", "Competition"]
    show = tbl[["Market", "Supply (MSF)", "Vacancy %", "Vacancy",
                "Rent ₹/sqft", "Absorption MSF", "New Supply MSF", "Competition"]]
    styled = (show.style
              .format({"Supply (MSF)": "{:.1f}", "Vacancy %": "{:.1f}%",
                       "Rent ₹/sqft": "₹{:.0f}", "Absorption MSF": "{:.2f}",
                       "New Supply MSF": "{:.2f}"})
              .hide(axis="index"))
    st.dataframe(styled, use_container_width=True, height=285)
    st.markdown("")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown('<p class="section-hdr">Vacancy % by Market</p>', unsafe_allow_html=True)
        d = df.sort_values("vacancy_pct", ascending=True)
        fig = go.Figure(go.Bar(
            x=d["vacancy_pct"], y=d["market_name"], orientation="h",
            marker_color=[vac_color(v) for v in d["vacancy_pct"]],
            text=[f"{v:.1f}%" for v in d["vacancy_pct"]], textposition="outside",
        ))
        fig.add_vline(x=10, line_dash="dot", line_color="#475569", annotation_text="10% threshold")
        fig.update_layout(**BASE_LAYOUT, xaxis_title="Vacancy %", height=280,
                          xaxis=dict(range=[0, d["vacancy_pct"].max() * 1.3]))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<p class="section-hdr">Avg Asking Rent (₹/sqft/month)</p>', unsafe_allow_html=True)
        d = df.sort_values("avg_asking_rent", ascending=True)
        fig = go.Figure(go.Bar(
            x=d["avg_asking_rent"], y=d["market_name"], orientation="h",
            marker_color=[MARKET_COLORS.get(m, "#3b82f6") for m in d["market_name"]],
            text=[f"₹{v:.0f}" for v in d["avg_asking_rent"]], textposition="outside",
        ))
        fig.add_vline(x=80, line_dash="dot", line_color="#fb923c", annotation_text="₹80 target")
        fig.update_layout(**BASE_LAYOUT, xaxis_title="₹/sqft/month", height=280,
                          xaxis=dict(range=[0, d["avg_asking_rent"].max() * 1.35]))
        st.plotly_chart(fig, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown('<p class="section-hdr">Net Absorption by Market (MSF)</p>', unsafe_allow_html=True)
        d = df.sort_values("absorption_msf", ascending=True)
        fig = go.Figure(go.Bar(
            x=d["absorption_msf"], y=d["market_name"], orientation="h",
            marker_color=[MARKET_COLORS.get(m, "#3b82f6") for m in d["market_name"]],
            text=[f"{v:.2f}" for v in d["absorption_msf"]], textposition="outside",
        ))
        fig.update_layout(**BASE_LAYOUT, xaxis_title="MSF", height=280,
                          xaxis=dict(range=[0, d["absorption_msf"].max() * 1.25]))
        st.plotly_chart(fig, use_container_width=True)

    with col4:
        st.markdown('<p class="section-hdr">Managed-Office Competition</p>', unsafe_allow_html=True)
        comp = df[["market_name", "operators", "wework_centres",
                   "pricing_min", "pricing_max", "competition_level"]].copy()
        comp["Pricing"] = comp.apply(
            lambda r: f"₹{r['pricing_min']:.0f}–{r['pricing_max']:.0f}"
                      if pd.notna(r["pricing_min"]) else "N/A", axis=1)
        comp["Centres"] = comp["wework_centres"].fillna(0).astype(int)
        comp["Level"]   = comp["competition_level"].apply(comp_signal)
        out = comp[["market_name", "Centres", "Pricing", "Level"]].copy()
        out.columns = ["Market", "WeWork Centres", "Pricing/seat/mo", "Level"]
        st.dataframe(out.set_index("Market"), use_container_width=True, height=280)

    st.markdown('<p class="section-hdr">Recent Major Transactions (H1 2026)</p>', unsafe_allow_html=True)
    t = txns[["company", "market_name", "area_leased_sqft", "est_seats",
               "transaction_date", "rent_per_sqft", "sector", "transaction_type"]].copy()
    t.columns = ["Company", "Market", "Area (sqft)", "Est. Seats",
                 "Date", "Rent ₹/sqft", "Sector", "Type"]
    t["Area (sqft)"] = t["Area (sqft)"].apply(lambda x: f"{x:,}" if pd.notna(x) else "N/A")
    t["Rent ₹/sqft"] = t["Rent ₹/sqft"].apply(
        lambda x: f"₹{x:.1f}" if pd.notna(x) else "Not disclosed")
    st.dataframe(t.set_index("Company"), use_container_width=True, height=300)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3: Market Opportunity View
# ══════════════════════════════════════════════════════════════════════════════
def render_opportunity():
    df = _markets()

    st.markdown(
        '<div class="note-box">📖 <b>How to read:</b> Bubble size = net absorption (demand strength). '
        'X-axis = vacancy (right = more space available). Y-axis = asking rent (up = more expensive). '
        'Markets in the <b>bottom-left</b> (tight + affordable) are most attractive for Autopilot. '
        'The dashed lines mark the <b>₹80/sqft target rent</b> and <b>median vacancy</b>.</div>',
        unsafe_allow_html=True,
    )

    df_p = df.copy()
    df_p["bubble_size"] = (df_p["absorption_msf"].fillna(0).clip(lower=0.05) * 90).round(1)

    fig = go.Figure()
    for _, row in df_p.iterrows():
        color = MARKET_COLORS.get(row["market_name"], "#3b82f6")
        ht = (f"<b>{row['market_name']}</b><br>"
              f"Vacancy: {row['vacancy_pct']:.1f}%<br>"
              f"Rent: ₹{row['avg_asking_rent']:.0f}/sqft<br>"
              f"Absorption: {row['absorption_msf']:.2f} MSF<br>"
              f"Competition: {row['competition_level']}<extra></extra>")
        fig.add_trace(go.Scatter(
            x=[row["vacancy_pct"]], y=[row["avg_asking_rent"]],
            mode="markers+text",
            marker=dict(size=row["bubble_size"], color=color, opacity=0.85,
                        line=dict(width=1.5, color="rgba(255,255,255,0.5)")),
            text=[row["market_name"]], textposition="top center",
            textfont=dict(size=11, color="#e2e8f0"),
            hovertemplate=ht, name=row["market_name"], showlegend=False,
        ))

    median_vac = df["vacancy_pct"].median()
    fig.add_vline(x=median_vac, line_dash="dot", line_color="#475569", line_width=1.2)
    fig.add_hline(y=80, line_dash="dot", line_color="#fb923c", line_width=1.2,
                  annotation_text="₹80 target rent  ", annotation_font_color="#fb923c",
                  annotation_position="right")

    x_lo = df["vacancy_pct"].min() - 1
    x_hi = df["vacancy_pct"].max() + 2
    for xa, ya, txt in [
        (x_lo, 66,  "Sweet Spot\n(Affordable + Active)"),
        (x_hi, 66,  "Emerging / Supply Risk\n(Affordable + Available)"),
        (x_lo, 155, "Premium\n(Expensive + Active)"),
        (x_hi, 155, "Caution\n(Expensive + Available)"),
    ]:
        fig.add_annotation(x=xa, y=ya, text=txt, showarrow=False,
                           font=dict(size=9, color="#475569"), align="left")

    fig.update_layout(
        **BASE_LAYOUT,
        title=dict(text="Opportunity Matrix: Vacancy vs Rent  (bubble = absorption)",
                   font=dict(size=14)),
        xaxis=dict(title="Vacancy %", gridcolor="#1e293b",
                   range=[df["vacancy_pct"].min() - 3, df["vacancy_pct"].max() + 5]),
        yaxis=dict(title="Avg Rent ₹/sqft", gridcolor="#1e293b",
                   range=[df["avg_asking_rent"].min() - 30, df["avg_asking_rent"].max() + 40]),
        height=520,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown('<p class="section-hdr">Opportunity Scoring by Dimension</p>', unsafe_allow_html=True)
    st.caption(
        "Each dimension scored separately from source data. "
        "No composite magic number — reviewers can see exactly why each market ranks as it does."
    )

    score = df[["market_name"]].copy()
    dr = rank3(df["absorption_ratio"], ascending=True)
    score["Demand"]      = dr.map({"Low": "🔴 Weak", "Medium": "🟡 Moderate", "High": "🟢 Strong"})
    er = rank3(df["avg_asking_rent"], ascending=False)
    score["Economics"]   = er.map({"Low": "🔴 Expensive", "Medium": "🟡 Moderate", "High": "🟢 Affordable"})
    vr = rank3(df["vacancy_pct"], ascending=False)
    score["Vacancy"]     = vr.map({"Low": "🔴 High vac.", "Medium": "🟡 Moderate", "High": "🟢 Tight"})
    score["Competition"] = df["competition_level"].map({
        "None": "🟢 Open", "Low": "🟢 Low", "Medium": "🟡 Medium", "High": "🔴 Saturated"
    })

    from contextlib import closing
    from database.connection import get_connection
    with closing(get_connection()) as conn:
        cat = pd.read_sql_query(
            "SELECT market_name, upcoming_infrastructure FROM market_catalysts", conn
        )
    infra_map = dict(zip(cat["market_name"], cat["upcoming_infrastructure"]))
    score["Infrastructure"] = df["market_name"].apply(
        lambda m: "🟢 Metro served" if infra_map.get(m) and "metro" in str(infra_map.get(m, "")).lower()
                  else "🟡 Planned" if infra_map.get(m) else "⚪ N/A"
    )
    score = score.rename(columns={"market_name": "Market"}).set_index("Market")
    st.dataframe(score, use_container_width=True, height=275)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4: AI Market Analyst
# ══════════════════════════════════════════════════════════════════════════════
def render_ai_analyst():
    st.markdown(
        '<div class="note-box">'
        '🤖 <b>Evidence-grounded AI Analyst</b> — '
        'Every answer is retrieved from the SQLite database first, then sent to the LLM. '
        'The AI only makes claims supported by the evidence shown below each answer.</div>',
        unsafe_allow_html=True,
    )

    with st.form("ai_analyst_form"):
        question = st.text_input(
            "Ask a market question:",
            placeholder="e.g. What is driving demand in ORR?",
            key="ai_question",
        )
        run = st.form_submit_button("🔍  Analyse", type="primary")

    if not run or not question.strip():
        return

    with st.spinner("Retrieving evidence from database and analysing..."):
        result = analyse(question)

    resp    = result["response"]
    intent  = result["intent"]
    ev_text = result["evidence_text"]

    scope = (', '.join(intent['mentioned_markets'])
             if intent['mentioned_markets'] else 'all markets')
    st.markdown(
        f'<div class="intent-badge">'
        f'Category: <b>{intent["category"]}</b> &nbsp;·&nbsp; Scope: <b>{scope}</b></div>',
        unsafe_allow_html=True,
    )

    st.markdown("#### 💡 Insight")
    st.markdown(
        f'<div class="insight-card">{resp.get("insight", "No insight returned.")}</div>',
        unsafe_allow_html=True,
    )

    st.markdown("#### 📊 Evidence")
    evidence_points = resp.get("evidence_cited", [])
    if evidence_points:
        for pt in evidence_points:
            st.markdown(f'<div class="evidence-item">📌 {pt}</div>', unsafe_allow_html=True)
    else:
        st.caption("No specific evidence points returned.")

    st.markdown("")

    with st.expander("🧠 Reasoning", expanded=True):
        st.markdown(resp.get("reasoning", "No reasoning returned."))
    with st.expander("⚠️ Risks & Limitations"):
        st.markdown(resp.get("risks", "No risks returned."))
    with st.expander("🔍 Evidence package sent to LLM"):
        st.code(ev_text, language="text")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5: Expansion Scenario
# ══════════════════════════════════════════════════════════════════════════════
def render_expansion_scenario():
    st.markdown(
        '<div class="note-box">🔍 <b>Expansion Scenario</b> — '
        'Enter your requirements. We will compare all available Bangalore micro-markets '
        'using actual database data and provide an evidence-based market-fit summary for each.</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    with c1: seats       = st.number_input("Required Seats", min_value=10, max_value=50000, value=500, step=50, key="exp_seats")
    with c2: target_rent = st.number_input("Target Rent (₹/sq.ft/mo)", min_value=10.0, max_value=500.0, value=80.0, step=5.0, key="exp_rent")
    with c3: client_size = st.number_input("Min Client Size (employees)", min_value=10, max_value=10000, value=100, step=10, key="exp_client")
    with c4: st.text_input("City", value="Bangalore", disabled=True, key="exp_city")

    if not st.button("🔍 Analyse All Markets", type="primary"):
        return

    required_area = seats * 60  # 60 sqft/seat industry standard

    with st.spinner("Fetching market data and analysing..."):
        # ── 1. Fetch all market data ──────────────────────────────────────────
        df = _markets()  # fundamentals + competition, latest quarter

        # Fetch latest demand per market
        from contextlib import closing
        from database.connection import get_connection
        with closing(get_connection()) as conn:
            demand_df = pd.read_sql_query("""
                WITH latest AS (
                    SELECT market_name,
                           MAX(year * 10 + CAST(REPLACE(quarter,'Q','') AS INTEGER)) AS sk
                    FROM demand_indicators GROUP BY market_name
                )
                SELECT d.market_name, d.leasing_activity_sqft, d.major_occupiers
                FROM demand_indicators d
                JOIN latest l ON d.market_name = l.market_name
                  AND (d.year * 10 + CAST(REPLACE(d.quarter,'Q','') AS INTEGER)) = l.sk
            """, conn)
            catalysts_df = pd.read_sql_query(
                "SELECT market_name, upcoming_infrastructure FROM market_catalysts", conn
            )
            txn_df = pd.read_sql_query("""
                SELECT market_name, COUNT(*) as txn_count, SUM(area_leased_sqft) as total_leased
                FROM transactions GROUP BY market_name
            """, conn)

        # Merge all into one working DataFrame
        work = df.merge(demand_df, on="market_name", how="left") \
                  .merge(catalysts_df, on="market_name", how="left") \
                  .merge(txn_df, on="market_name", how="left")

        # ── 2. Build comparison table ─────────────────────────────────────────
        def fmt(v, fmt_str, suffix="", fallback="N/A"):
            try:
                return f"{v:{fmt_str}}{suffix}" if pd.notna(v) else fallback
            except Exception:
                return fallback

        table_rows = []
        for _, r in work.iterrows():
            rent = r["avg_asking_rent"]
            if pd.isna(rent):
                rent_status = "N/A"
            elif rent <= target_rent:
                rent_status = "✅ Within budget"
            else:
                rent_status = "❌ Exceeds budget"
            table_rows.append({
                "Market":              r["market_name"],
                "Avg Rent (₹/sqft)":   fmt(r["avg_asking_rent"], ".0f"),
                "vs Target":           f"{'▲' if pd.notna(r['avg_asking_rent']) and r['avg_asking_rent'] > target_rent else ('▼' if pd.notna(r['avg_asking_rent']) else '—')} {fmt(abs(r['avg_asking_rent'] - target_rent) if pd.notna(r['avg_asking_rent']) else None, '.0f', ' ₹')}",
                "Vacancy %":           fmt(r["vacancy_pct"], ".1f", "%"),
                "Absorption (sqft)":   fmt(r["absorption_sqft"], ",.0f"),
                "Leasing Act. (sqft)": fmt(r.get("leasing_activity_sqft"), ",.0f"),
                "Operators":           r["operators"] if pd.notna(r.get("operators")) else "N/A",
                "Infrastructure":      (str(r["upcoming_infrastructure"])[:40] + "...") if pd.notna(r.get("upcoming_infrastructure")) and len(str(r.get("upcoming_infrastructure", ""))) > 40 else (r.get("upcoming_infrastructure") or "N/A"),
                "Transactions":        fmt(r.get("txn_count"), ".0f", " deals"),
                "Rent Feasible":       rent_status,
            })

        table_df = pd.DataFrame(table_rows).set_index("Market")
        st.markdown('<p class="section-hdr">📋 Market Comparison Table</p>', unsafe_allow_html=True)
        st.caption(f"All markets | Required area: {required_area:,} sqft ({seats} seats @ 60 sqft/seat) | Target rent: ₹{target_rent:.0f}/sqft")
        st.dataframe(table_df, use_container_width=True)

        # ── 3. Split into feasible vs excluded ───────────────────────────────
        feasible = work[pd.notna(work["avg_asking_rent"]) & (work["avg_asking_rent"] <= target_rent)]
        excluded = work[pd.notna(work["avg_asking_rent"]) & (work["avg_asking_rent"] > target_rent)]
        unknown  = work[pd.isna(work["avg_asking_rent"])]

        # ── 4. Build evidence ONLY for feasible markets ───────────────────────
        ev_lines = []
        for _, r in feasible.iterrows():
            ev_lines.append(
                f"\n--- {r['market_name']} ---\n"
                f"  Avg Rent: ₹{fmt(r['avg_asking_rent'], '.0f')}/sqft | Vacancy: {fmt(r['vacancy_pct'], '.1f', '%')} | "
                f"Absorption: {fmt(r['absorption_sqft'], ',.0f', ' sqft')} | New Supply: {fmt(r['new_supply_sqft'], ',.0f', ' sqft')}\n"
                f"  Leasing Activity: {fmt(r.get('leasing_activity_sqft'), ',.0f', ' sqft')} | "
                f"Major Occupiers: {r.get('major_occupiers') or 'N/A'}\n"
                f"  Operators: {r['operators'] if pd.notna(r.get('operators')) else 'N/A'} | "
                f"WeWork Centres: {fmt(r.get('wework_centres'), '.0f')}\n"
                f"  Managed-office pricing: ₹{fmt(r.get('pricing_min'), '.0f')} – ₹{fmt(r.get('pricing_max'), '.0f')}/seat/mo\n"
                f"  Infrastructure: {r.get('upcoming_infrastructure') or 'N/A'}\n"
                f"  Transactions: {fmt(r.get('txn_count'), '.0f', ' deals')}, Total leased: {fmt(r.get('total_leased'), ',.0f', ' sqft')}"
            )

        # ── 5. LLM call only for feasible markets ────────────────────────────
        summaries = {}
        if not feasible.empty:
            feasible_names = feasible["market_name"].tolist()
            summaries = analyse_expansion_scenario(
                seats, target_rent, client_size, "\n".join(ev_lines), feasible_names
            )

        # ── 6. Display per-market results ─────────────────────────────────────
        st.markdown('<p class="section-hdr">🧠 Market Fit Assessment</p>', unsafe_allow_html=True)

        if "error" in summaries:
            st.error(summaries["error"])

        # Feasible markets — full AI analysis
        for _, r in feasible.iterrows():
            mkt = r["market_name"]
            with st.expander(f"{mkt}  —  ₹{fmt(r['avg_asking_rent'], '.0f')}/sqft | Vacancy {fmt(r['vacancy_pct'], '.1f', '%')}", expanded=False):
                st.markdown(f"**AI Summary:** {summaries.get(mkt, 'Analysis not available.')}")
                st.markdown(
                    f"**Evidence:** Avg Rent ₹{fmt(r['avg_asking_rent'], '.0f')}/sqft · "
                    f"Vacancy {fmt(r['vacancy_pct'], '.1f', '%')} · "
                    f"Absorption {fmt(r['absorption_sqft'], ',.0f', ' sqft')} · "
                    f"Leasing {fmt(r.get('leasing_activity_sqft'), ',.0f', ' sqft')} · "
                    f"Operators: {r['operators'] if pd.notna(r.get('operators')) else 'N/A'}"
                )

        # Excluded markets — rent over budget, no further analysis
        for _, r in excluded.iterrows():
            mkt = r["market_name"]
            with st.expander(f"{mkt}  —  ₹{fmt(r['avg_asking_rent'], '.0f')}/sqft  *(excluded)*", expanded=False):
                st.warning(
                    f"**Excluded** — Market rent ₹{fmt(r['avg_asking_rent'], '.0f')}/sqft "
                    f"exceeds the target budget of ₹{target_rent:.0f}/sqft. "
                    f"No further analysis performed."
                )

        # Unknown rent markets
        for _, r in unknown.iterrows():
            mkt = r["market_name"]
            with st.expander(f"{mkt}  —  Rent N/A", expanded=False):
                st.info("**Rent data unavailable** — Cannot determine budget feasibility. No analysis performed.")

        st.caption("Source: Bangalore Market Intelligence DB (Q2-2026). Markets with rent > target are excluded. No scores invented.")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN LAYOUT
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div style="display:flex;align-items:center;gap:0.8rem;margin-bottom:0.5rem">
  <div style="background:linear-gradient(135deg,#2563eb,#3b82f6);width:44px;height:44px;
              border-radius:10px;display:flex;align-items:center;justify-content:center;
              font-size:1.5rem;flex-shrink:0">🏢</div>
  <div>
    <h1 style="margin:0;font-size:1.5rem;font-weight:700;color:#f1f5f9;letter-spacing:-0.01em">
      Bangalore Market Intelligence</h1>
    <p style="margin:0;font-size:0.78rem;color:#64748b;letter-spacing:0.02em">
      Autopilot Offices &nbsp;·&nbsp; Commercial Real Estate &nbsp;·&nbsp; Q2 2026
      &nbsp;·&nbsp;
      <span style="color:#60a5fa">Evidence-grounded insights for expansion decisions</span>
    </p>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊  Market Overview",
    "📋  Micro-Market Comparison",
    "🎯  Market Opportunity",
    "🤖  AI Market Analyst",
    "🔍  Expansion Scenario",
])

with tab1:  render_overview()
with tab2:  render_comparison()
with tab3:  render_opportunity()
with tab4:  render_ai_analyst()
with tab5:  render_expansion_scenario()
