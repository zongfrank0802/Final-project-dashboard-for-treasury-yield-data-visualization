import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from data.fetch_data import load_data, MATURITIES

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG  (must be the FIRST Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="U.S. Treasury Yield Curve Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL STYLES
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600&family=DM+Mono&display=swap');
    html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
    .stApp { background-color: #0f1117; }
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #141822 0%, #0f1117 100%);
        border-right: 1px solid #1e2433;
    }
    section[data-testid="stSidebar"] * { color: #c9d1e0 !important; }
    div[data-testid="metric-container"] {
        background: #141822;
        border: 1px solid #1e2433;
        border-radius: 12px;
        padding: 16px 20px;
    }
    div[data-testid="metric-container"] label { color: #7b8db0 !important; font-size: 0.78rem; }
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #e8edf5 !important; font-size: 1.5rem; font-weight: 600;
    }
    h1 { color: #e8edf5 !important; font-weight: 600; letter-spacing: -0.5px; }
    h2 { color: #c9d1e0 !important; font-weight: 500; font-size: 1.15rem; border-bottom: 1px solid #1e2433; padding-bottom: 8px; }
    h3 { color: #a0aec0 !important; font-weight: 400; font-size: 0.95rem; }
    hr { border-color: #1e2433 !important; }
    .info-box {
        background: #141822;
        border-left: 3px solid #3b82f6;
        border-radius: 0 8px 8px 0;
        padding: 12px 16px;
        margin: 8px 0 16px 0;
        color: #8fa3c0;
        font-size: 0.85rem;
        line-height: 1.6;
    }
    button[data-baseweb="tab"] { color: #7b8db0 !important; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #3b82f6 !important; border-bottom-color: #3b82f6 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def hex_to_rgba(hex_color: str, alpha: float = 0.08) -> str:
    """Convert a #rrggbb hex string to rgba(r,g,b,a) for Plotly fillcolor."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"

# ─────────────────────────────────────────────────────────────────────────────
# PLOTLY BASE LAYOUT  (unpacked into every chart's update_layout)
# NOTE: does NOT include xaxis/yaxis — set those via update_xaxes/update_yaxes
# ─────────────────────────────────────────────────────────────────────────────
CHART_BASE = dict(
    paper_bgcolor="#141822",
    plot_bgcolor="#141822",
    font=dict(family="DM Sans", color="#a0aec0", size=12),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="#1e2433"),
    margin=dict(l=50, r=30, t=50, b=50),
    hoverlabel=dict(bgcolor="#1e2433", font_color="#e8edf5", font_family="DM Mono"),
)

# Shared axis style applied via update_xaxes / update_yaxes
AXIS_STYLE = dict(gridcolor="#1e2433", linecolor="#1e2433", tickcolor="#1e2433")

# Colour palette
BLUE   = "#3b82f6"
AMBER  = "#f59e0b"
GREEN  = "#10b981"
RED    = "#ef4444"
PURPLE = "#8b5cf6"
TEAL   = "#14b8a6"

# ─────────────────────────────────────────────────────────────────────────────
# DATA LOADING  —  Live API Pipeline
# ─────────────────────────────────────────────────────────────────────────────
# Architecture (Path C):
#   U.S. Treasury XML API  →  fetch_data.load_data()  →  app.py  →  Streamlit
#
# Data is fetched live via requests.get() to the Treasury REST endpoint.
# Streamlit caches the result for 1 hour (ttl=3600) to avoid hammering the API
# on every widget interaction, but always reflects the latest available data.
# ─────────────────────────────────────────────────────────────────────────────
def get_data() -> pd.DataFrame:
    """Fetch live from Treasury API and add derived columns."""
    df = load_data()          # live API call — see data/fetch_data.py
    df["Date"] = pd.to_datetime(df["Date"])
    df = df.dropna(subset=MATURITIES, how="all")
    df["Spread_10Y_2Y"] = df["10Y"] - df["2Y"]
    df["Spread_10Y_3M"] = df["10Y"] - df["3M"]
    df["Year"]  = df["Date"].dt.year
    df["Month"] = df["Date"].dt.to_period("M").astype(str)
    return df

with st.spinner("Fetching    live data from U.S. Treasury API …"):
    df = get_data()

min_date = df["Date"].min().date()
max_date = df["Date"].max().date()

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Dashboard Controls")
    st.markdown("---")

    st.markdown("**📅 Date Range**")
    date_range = st.slider(
        "Select period",
        min_value=min_date, max_value=max_date,
        value=(pd.Timestamp("2015-01-01").date(), max_date),
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("**📐 Maturities to compare**")
    selected_mats = st.multiselect(
        "Pick maturities",
        options=MATURITIES,
        default=["2Y", "5Y", "10Y", "30Y"],
        label_visibility="collapsed",
    )

    st.markdown("---")
    smooth_window = st.select_slider(
        "**📊 Smoothing (rolling avg)**",
        options=[1, 5, 10, 21, 63],
        value=1,
        format_func=lambda x: "None" if x == 1 else f"{x}d MA",
    )

    st.markdown("---")
    show_recessions = st.toggle("**🟥 Show NBER Recessions**", value=True)

    st.markdown("---")
    st.markdown(
        "<div style='color:#4a5568;font-size:0.75rem;line-height:1.5'>"
        "Data: U.S. Treasury Dept.<br>"
        "Built with Streamlit + Plotly<br>"
        "Academic project — Spring 2025"
        "</div>",
        unsafe_allow_html=True,
    )

# Filter + smooth
mask = (df["Date"].dt.date >= date_range[0]) & (df["Date"].dt.date <= date_range[1])
dff  = df[mask].copy()
if smooth_window > 1:
    for col in MATURITIES + ["Spread_10Y_2Y", "Spread_10Y_3M"]:
        if col in dff.columns:
            dff[col] = dff[col].rolling(smooth_window, min_periods=1).mean()

# ─────────────────────────────────────────────────────────────────────────────
# RECESSION BANDS
# ─────────────────────────────────────────────────────────────────────────────
RECESSIONS = [
    ("2001-03-01", "2001-11-30", "Dot-com"),
    ("2007-12-01", "2009-06-30", "GFC"),
    ("2020-02-01", "2020-04-30", "COVID-19"),
]

def add_recession_bands(fig: go.Figure) -> go.Figure:
    if not show_recessions:
        return fig
    for start, end, label in RECESSIONS:
        fig.add_vrect(
            x0=start, x1=end,
            fillcolor="rgba(239,68,68,0.08)",
            layer="below", line_width=0,
            annotation_text=label,
            annotation_position="top left",
            annotation=dict(font_size=9, font_color="rgba(239,68,68,0.5)"),
        )
    return fig

# ─────────────────────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────────────────────
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("# 📈 U.S. Treasury Yield Curve")
    st.markdown(
        "<p style='color:#7b8db0;margin-top:-10px;font-size:0.9rem'>"
        "An interactive exploration of U.S. government bond yields from 2000–2024"
        "</p>",
        unsafe_allow_html=True,
    )
with col_h2:
    latest = df.iloc[-1]
    st.markdown(
        f"<div style='text-align:right;color:#4a5568;font-size:0.75rem;margin-top:12px'>"
        f"Latest data point<br>"
        f"<span style='color:#c9d1e0;font-size:0.9rem;font-weight:600'>"
        f"{latest['Date'].strftime('%b %d, %Y')}</span></div>",
        unsafe_allow_html=True,
    )

st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# KPI METRICS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("### Key Rates (Latest)")
latest_full = df.iloc[-1]
prev        = df.iloc[-6]

def delta_color(v):
    return "normal" if v >= 0 else "inverse"

m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    d = latest_full["2Y"] - prev["2Y"]
    st.metric("2-Year Yield",  f"{latest_full['2Y']:.2f}%",  f"{d:+.2f}%", delta_color=delta_color(d))
with m2:
    d = latest_full["5Y"] - prev["5Y"]
    st.metric("5-Year Yield",  f"{latest_full['5Y']:.2f}%",  f"{d:+.2f}%", delta_color=delta_color(d))
with m3:
    d = latest_full["10Y"] - prev["10Y"]
    st.metric("10-Year Yield", f"{latest_full['10Y']:.2f}%", f"{d:+.2f}%", delta_color=delta_color(d))
with m4:
    d = latest_full["30Y"] - prev["30Y"]
    st.metric("30-Year Yield", f"{latest_full['30Y']:.2f}%", f"{d:+.2f}%", delta_color=delta_color(d))
with m5:
    spread_val = latest_full["Spread_10Y_2Y"]
    st.metric("10Y–2Y Spread", f"{spread_val:+.2f}%",
              "⚠️ Inverted" if spread_val < 0 else "✅ Normal")

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🌊  Yield Curve Snapshot",
    "📉  Historical Trends",
    "🔀  Spread Analysis",
    "🔥  Heatmap",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — YIELD CURVE SNAPSHOT
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("## Yield Curve Shape — Interactive Date Picker")
    st.markdown(
        "<div class='info-box'>"
        "The yield curve plots interest rates across maturities on a single day. "
        "A <strong>normal</strong> curve slopes upward (longer = higher yield). "
        "An <strong>inverted</strong> curve (short > long) has historically preceded recessions."
        "</div>",
        unsafe_allow_html=True,
    )

    col_snap1, col_snap2 = st.columns([1, 3])

    with col_snap1:
        st.markdown("**Select a Date**")
        snap_date = st.date_input(
            "Snapshot date",
            value=df["Date"].iloc[-1].date(),
            min_value=min_date,
            max_value=max_date,
            label_visibility="collapsed",
        )

        st.markdown("**Quick presets**")
        presets = {
            "Pre-GFC (2007)":   "2007-06-01",
            "Post-GFC (2010)":  "2010-01-04",
            "COVID Low (2020)": "2020-08-03",
            "Hike Peak (2023)": "2023-10-02",
        }
        chosen_preset = st.selectbox(
            "Preset curves",
            ["— none —"] + list(presets.keys()),
            label_visibility="collapsed",
        )

    with col_snap2:
        dates_to_plot = {}

        snap_ts  = pd.Timestamp(snap_date)
        snap_row = df.loc[(df["Date"] - snap_ts).abs().idxmin()]
        dates_to_plot[snap_row["Date"].strftime("%b %d %Y")] = snap_row

        if chosen_preset != "— none —":
            p_ts  = pd.Timestamp(presets[chosen_preset])
            p_row = df.loc[(df["Date"] - p_ts).abs().idxmin()]
            dates_to_plot[p_row["Date"].strftime("%b %d %Y") + " ★"] = p_row

        SNAP_COLORS = [BLUE, AMBER, GREEN, RED, PURPLE]
        fig_snap = go.Figure()

        for idx, (label, row) in enumerate(dates_to_plot.items()):
            yields = [row[m] for m in MATURITIES]
            color  = SNAP_COLORS[idx % len(SNAP_COLORS)]

            fig_snap.add_trace(go.Scatter(
                x=MATURITIES, y=yields,
                mode="lines+markers",
                name=label,
                line=dict(color=color, width=3),
                marker=dict(size=8, symbol="circle",
                            line=dict(width=2, color="#141822")),
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Yield: <b>%{y:.2f}%</b><br>"
                    f"Date: {label}<extra></extra>"
                ),
            ))

            fig_snap.add_trace(go.Scatter(
                x=MATURITIES + MATURITIES[::-1],
                y=yields + [0] * len(MATURITIES),
                fill="toself",
                fillcolor=hex_to_rgba(color, 0.08),
                line=dict(color="rgba(0,0,0,0)"),
                showlegend=False,
                hoverinfo="skip",
            ))

        fig_snap.update_layout(**CHART_BASE, height=420,
                               title=dict(text="U.S. Treasury Yield Curve",
                                          font=dict(size=16, color="#e8edf5")))
        fig_snap.update_xaxes(title="Maturity", **AXIS_STYLE)
        fig_snap.update_yaxes(title="Yield (%)", rangemode="tozero", **AXIS_STYLE)
        st.plotly_chart(fig_snap, use_container_width=True)

        if snap_row["Spread_10Y_2Y"] < 0:
            st.warning(
                f"⚠️ **Inverted curve** on {snap_row['Date'].strftime('%b %d, %Y')} — "
                f"the 10Y–2Y spread is {snap_row['Spread_10Y_2Y']:+.2f}%. "
                "Historically, this has preceded every U.S. recession since the 1970s."
            )

    # Animated yield curve
    st.markdown("---")
    st.markdown("## 🎬 Animated Yield Curve (Monthly Snapshots)")
    st.markdown(
        "<div class='info-box'>"
        "Watch how the yield curve evolved month by month. Press ▶ to start the animation. "
        "Notice how the curve flattens or inverts before recessions, then steepens during recovery."
        "</div>",
        unsafe_allow_html=True,
    )

    monthly = (
        dff.set_index("Date")
        .resample("ME")[MATURITIES]
        .last()
        .reset_index()
        .dropna()
    )
    monthly["Month_Label"] = monthly["Date"].dt.strftime("%b %Y")

    anim_long = monthly.melt(
        id_vars=["Date", "Month_Label"],
        value_vars=MATURITIES,
        var_name="Maturity", value_name="Yield",
    )

    fig_anim = px.line(
        anim_long,
        x="Maturity", y="Yield",
        animation_frame="Month_Label",
        range_y=[0, max(anim_long["Yield"].max() + 0.5, 0.5)],
        color_discrete_sequence=[BLUE],
        markers=True,
        title="Animated Monthly Yield Curve",
    )
    fig_anim.update_traces(
        line=dict(width=3),
        marker=dict(size=9, line=dict(width=2, color="#141822")),
        hovertemplate="<b>%{x}</b><br>Yield: <b>%{y:.2f}%</b><extra></extra>",
    )
    fig_anim.update_layout(**CHART_BASE, height=400,
                           title=dict(font=dict(size=16, color="#e8edf5")))
    fig_anim.update_xaxes(title="Maturity", **AXIS_STYLE)
    fig_anim.update_yaxes(title="Yield (%)", **AXIS_STYLE)
    fig_anim.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 120
    fig_anim.layout.updatemenus[0].buttons[0].args[1]["transition"]["duration"] = 80
    st.plotly_chart(fig_anim, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — HISTORICAL YIELD TRENDS
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("## Historical Yield Trends")
    st.markdown(
        "<div class='info-box'>"
        "Use the sidebar to select maturities and apply a rolling average. "
        "Red shading marks NBER-designated U.S. recessions."
        "</div>",
        unsafe_allow_html=True,
    )

    if not selected_mats:
        st.info("👈  Please select at least one maturity from the sidebar.")
    else:
        mat_colours = {
            "1M": "#94a3b8", "2M": "#7dd3fc", "3M": "#38bdf8",
            "6M": "#22d3ee", "1Y": "#34d399", "2Y": GREEN,
            "3Y": TEAL,      "5Y": BLUE,      "7Y": PURPLE,
            "10Y": AMBER,    "20Y": "#f97316", "30Y": RED,
        }

        fig_hist = go.Figure()
        for mat in selected_mats:
            if mat not in dff.columns:
                continue
            fig_hist.add_trace(go.Scatter(
                x=dff["Date"], y=dff[mat],
                mode="lines", name=mat,
                line=dict(color=mat_colours.get(mat, BLUE), width=2),
                hovertemplate=(
                    f"<b>{mat} Treasury Yield</b><br>"
                    "Date: %{x|%b %d, %Y}<br>"
                    "Yield: <b>%{y:.2f}%</b><extra></extra>"
                ),
            ))

        fig_hist = add_recession_bands(fig_hist)
        fig_hist.update_layout(
            **CHART_BASE,
            title=dict(text="U.S. Treasury Yields Over Time",
                       font=dict(size=16, color="#e8edf5")),
            height=500,
            hovermode="x unified",
        )
        fig_hist.update_xaxes(
            title="Date",
            rangeslider=dict(visible=True, bgcolor="#0f1117", thickness=0.05),
            **AXIS_STYLE,
        )
        fig_hist.update_yaxes(title="Yield (%)", **AXIS_STYLE)
        st.plotly_chart(fig_hist, use_container_width=True)

        st.markdown("### Summary Statistics (filtered period)")
        stats_df = (
            dff[selected_mats]
            .agg(["min", "max", "mean", "std"])
            .T
            .rename(columns={"min": "Min %", "max": "Max %",
                             "mean": "Avg %", "std": "Std Dev"})
            .round(2)
        )
        st.dataframe(
            stats_df.style
                .background_gradient(axis=0, cmap="Blues", subset=["Avg %"])
                .format("{:.2f}"),
            use_container_width=True,
        )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — SPREAD ANALYSIS
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("## Yield Spread Analysis")
    st.markdown(
        "<div class='info-box'>"
        "The <strong>10Y–2Y spread</strong> is the most-watched recession predictor. "
        "When negative (inverted), it signals investors expect the Fed to cut rates — "
        "often because a recession is coming. Every U.S. recession since 1955 was preceded by an inversion."
        "</div>",
        unsafe_allow_html=True,
    )

    col_s1, col_s2 = st.columns([2, 1])

    with col_s1:
        fig_spread = go.Figure()

        fig_spread.add_hline(
            y=0, line_dash="dash", line_color="#ef4444",
            line_width=1, opacity=0.6,
            annotation_text="Inversion threshold",
            annotation_font_color="rgba(239,68,68,0.6)",
            annotation_position="bottom right",
        )

        pos_mask = dff["Spread_10Y_2Y"] >= 0
        neg_mask = dff["Spread_10Y_2Y"] <  0

        fig_spread.add_trace(go.Scatter(
            x=dff["Date"][pos_mask], y=dff["Spread_10Y_2Y"][pos_mask],
            fill="tozeroy", fillcolor="rgba(16,185,129,0.15)",
            line=dict(color=GREEN, width=1.5), name="Positive spread",
            hovertemplate="<b>10Y–2Y</b><br>%{x|%b %d, %Y}<br>%{y:+.2f}%<extra></extra>",
        ))
        fig_spread.add_trace(go.Scatter(
            x=dff["Date"][neg_mask], y=dff["Spread_10Y_2Y"][neg_mask],
            fill="tozeroy", fillcolor="rgba(239,68,68,0.15)",
            line=dict(color=RED, width=1.5), name="Inverted (negative)",
            hovertemplate="<b>10Y–2Y</b><br>%{x|%b %d, %Y}<br>%{y:+.2f}%<extra></extra>",
        ))
        fig_spread.add_trace(go.Scatter(
            x=dff["Date"], y=dff["Spread_10Y_3M"],
            line=dict(color=AMBER, width=1.5, dash="dot"),
            name="10Y–3M spread",
            hovertemplate="<b>10Y–3M</b><br>%{x|%b %d, %Y}<br>%{y:+.2f}%<extra></extra>",
        ))

        fig_spread = add_recession_bands(fig_spread)
        fig_spread.update_layout(
            **CHART_BASE,
            title=dict(text="Yield Spread: 10Y – 2Y and 10Y – 3M",
                       font=dict(size=16, color="#e8edf5")),
            height=420,
            hovermode="x unified",
        )
        fig_spread.update_xaxes(title="Date", **AXIS_STYLE)
        fig_spread.update_yaxes(title="Spread (percentage points)", **AXIS_STYLE)
        st.plotly_chart(fig_spread, use_container_width=True)

    with col_s2:
        st.markdown("### Current Signal")
        spread_now   = latest_full["Spread_10Y_2Y"]
        inverted_now = spread_now < 0
        status_color = "#ef4444" if inverted_now else "#10b981"
        status_label = "INVERTED ⚠️" if inverted_now else "NORMAL ✅"

        st.markdown(
            f"<div style='background:#141822;border:1px solid {status_color};"
            f"border-radius:12px;padding:20px;text-align:center;'>"
            f"<div style='color:#7b8db0;font-size:0.8rem;margin-bottom:4px'>10Y–2Y Spread</div>"
            f"<div style='color:{status_color};font-size:2rem;font-weight:700'>{spread_now:+.2f}%</div>"
            f"<div style='color:{status_color};font-size:0.9rem;margin-top:8px'>{status_label}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        inv_pct = (dff["Spread_10Y_2Y"] < 0).mean() * 100
        st.markdown(
            f"<div style='background:#141822;border:1px solid #1e2433;"
            f"border-radius:12px;padding:16px;'>"
            f"<div style='color:#7b8db0;font-size:0.8rem'>Days Inverted (filtered)</div>"
            f"<div style='color:#e8edf5;font-size:1.4rem;font-weight:600'>{inv_pct:.1f}%</div>"
            f"<div style='color:#4a5568;font-size:0.75rem;margin-top:6px'>of selected period</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)
        pct = (dff["Spread_10Y_2Y"] < spread_now).mean() * 100
        st.markdown(f"**Current spread is at the {pct:.0f}th percentile** of the selected period.")
        st.progress(int(pct))

    st.markdown("---")
    st.markdown("### Inversion Depth Over Time")
    inv_df = dff[dff["Spread_10Y_2Y"] < 0].copy()
    if not inv_df.empty:
        fig_inv = go.Figure(go.Bar(
            x=inv_df["Date"],
            y=inv_df["Spread_10Y_2Y"],
            marker_color="rgba(239,68,68,0.7)",
            marker_line_width=0,
            name="Inversion depth",
            hovertemplate="Date: %{x|%b %d, %Y}<br>Spread: <b>%{y:+.2f}%</b><extra></extra>",
        ))
        fig_inv.update_layout(
            **CHART_BASE,
            title=dict(text="Days When Yield Curve Was Inverted (10Y–2Y < 0)",
                       font=dict(size=14, color="#e8edf5")),
            height=280,
            bargap=0,
        )
        fig_inv.update_xaxes(title="Date", **AXIS_STYLE)
        fig_inv.update_yaxes(title="Spread (%)", **AXIS_STYLE)
        st.plotly_chart(fig_inv, use_container_width=True)
    else:
        st.info("No inversions in the selected period.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — HEATMAP
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("## Yield Heatmap — Annual Averages")
    st.markdown(
        "<div class='info-box'>"
        "Each row = one calendar year. Each column = one maturity. "
        "Darker blue = lower yields (post-GFC, COVID). Darker amber = higher yields."
        "</div>",
        unsafe_allow_html=True,
    )

    hm_mat = st.multiselect(
        "Maturities to include",
        options=MATURITIES,
        default=["3M", "1Y", "2Y", "5Y", "10Y", "30Y"],
        key="hm_mats",
    )

    if hm_mat:
        heat_df = dff.groupby("Year")[hm_mat].mean().round(2)

        fig_heat = go.Figure(go.Heatmap(
            z=heat_df.values,
            x=heat_df.columns.tolist(),
            y=heat_df.index.tolist(),
            colorscale=[
                [0.0,  "#1e3a5f"],
                [0.25, "#1d4ed8"],
                [0.5,  "#3b82f6"],
                [0.75, "#fbbf24"],
                [1.0,  "#b45309"],
            ],
            hoverongaps=False,
            hovertemplate=(
                "Year: <b>%{y}</b><br>"
                "Maturity: <b>%{x}</b><br>"
                "Avg Yield: <b>%{z:.2f}%</b><extra></extra>"
            ),
            colorbar=dict(
                title=dict(text="Yield (%)", font=dict(color="#a0aec0")),
                tickfont=dict(color="#a0aec0"),
                bgcolor="#141822",
                bordercolor="#1e2433",
            ),
        ))
        fig_heat.update_layout(
            **CHART_BASE,
            title=dict(text="Average Annual Treasury Yields by Maturity",
                       font=dict(size=16, color="#e8edf5")),
            height=max(350, len(heat_df) * 30 + 100),
        )
        fig_heat.update_xaxes(title="Maturity", side="top", **AXIS_STYLE)
        fig_heat.update_yaxes(title="Year", autorange="reversed", **AXIS_STYLE)
        st.plotly_chart(fig_heat, use_container_width=True)

        st.markdown("### Year-over-Year Change in Yields")
        yoy_df = heat_df.diff().round(2).dropna()
        fig_yoy = go.Figure(go.Heatmap(
            z=yoy_df.values,
            x=yoy_df.columns.tolist(),
            y=yoy_df.index.tolist(),
            zmid=0,
            colorscale="RdBu",
            reversescale=True,
            hoverongaps=False,
            hovertemplate=(
                "Year: <b>%{y}</b><br>"
                "Maturity: <b>%{x}</b><br>"
                "YoY Change: <b>%{z:+.2f}%</b><extra></extra>"
            ),
            colorbar=dict(
                title=dict(text="Delta Yield (%)", font=dict(color="#a0aec0")),
                tickfont=dict(color="#a0aec0"),
                bgcolor="#141822",
                bordercolor="#1e2433",
            ),
        ))
        fig_yoy.update_layout(
            **CHART_BASE,
            title=dict(text="Year-over-Year Change in Average Yields",
                       font=dict(size=14, color="#e8edf5")),
            height=max(300, len(yoy_df) * 28 + 100),
        )
        fig_yoy.update_xaxes(title="Maturity", side="top", **AXIS_STYLE)
        fig_yoy.update_yaxes(title="Year", autorange="reversed", **AXIS_STYLE)
        st.plotly_chart(fig_yoy, use_container_width=True)
    else:
        st.info("Please select at least one maturity.")


# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#4a5568;font-size:0.8rem;padding:16px 0;'>"
    "Data source: U.S. Department of the Treasury · Daily Yield Curve Rates · "
    "<a href='https://home.treasury.gov/resource-center/data-chart-center/interest-rates/' "
    "style='color:#3b82f6'>treasury.gov</a>"
    " &nbsp;|&nbsp; Built with Streamlit & Plotly &nbsp;|&nbsp; Academic Project 2025"
    "</div>",
    unsafe_allow_html=True,
)
