"""
app.py — Lagos Flood Hazard & Exposure Explorer
=================================================
Premium interactive dashboard integrating AHP flood hazard models,
population exposure analytics, and NIMET climate scenarios for
Lagos State, Nigeria.

Run:  streamlit run app.py
"""
import base64
import calendar
import io
import math
import os

import folium
import folium.raster_layers
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.colors import ListedColormap, BoundaryNorm
import numpy as np
import pandas as pd
import rasterio
from rasterio.warp import transform_bounds
from PIL import Image
import streamlit as st
from streamlit_folium import st_folium

import model_api as M

# ═══════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Lagos Flood Hazard Explorer",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════════
# CUSTOM CSS — premium dark theme
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

*, html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
}

/* Streamlit draws its icons as Material Symbols ligatures. The universal
   rule above would override the icon font too, and a ligature rendered in
   Inter shows its literal name — expanders printed "keyboard_arrow_right"
   on top of their labels. Exempt icon elements from the override. */
[data-testid="stIconMaterial"],
span[class*="material-symbols"],
.material-symbols-rounded {
    font-family: 'Material Symbols Rounded' !important;
    font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;
}

/* Hide default branding */
#MainMenu, footer, header {visibility: hidden;}

.main .block-container {
    padding-top: 1.2rem;
    padding-bottom: 1rem;
    max-width: 1500px;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0c1222 0%, #162032 100%);
    border-right: 1px solid rgba(100,116,139,0.15);
}

/* ── Metric Cards ── */
div[data-testid="stMetric"] {
    background: linear-gradient(145deg, rgba(15,23,42,0.85), rgba(30,41,59,0.7));
    border: 1px solid rgba(100,116,139,0.18);
    border-radius: 14px;
    padding: 1rem 1.2rem;
    backdrop-filter: blur(12px);
    box-shadow: 0 4px 20px rgba(0,0,0,0.25);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
div[data-testid="stMetric"]:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 28px rgba(0,0,0,0.35);
}
div[data-testid="stMetric"] label {
    color: #94a3b8 !important;
    font-weight: 600 !important;
    font-size: 0.78rem !important;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #f1f5f9 !important;
    font-weight: 700 !important;
}
div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
    font-weight: 600 !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 2px;
    background: rgba(15,23,42,0.5);
    border-radius: 14px;
    padding: 5px;
    border: 1px solid rgba(100,116,139,0.12);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 10px;
    color: #94a3b8;
    font-weight: 500;
    padding: 10px 18px;
    font-size: 0.9rem;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #0891b2, #7c3aed) !important;
    color: #ffffff !important;
    font-weight: 700;
    box-shadow: 0 3px 12px rgba(8,145,178,0.3);
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #0891b2 0%, #6366f1 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px;
    font-weight: 600;
    padding: 0.55rem 1.6rem;
    transition: all 0.25s cubic-bezier(0.4,0,0.2,1);
    box-shadow: 0 2px 10px rgba(6,182,212,0.2);
    letter-spacing: 0.02em;
}
.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(6,182,212,0.35);
}

.stDownloadButton > button {
    background: linear-gradient(135deg, #7c3aed 0%, #db2777 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px;
    font-weight: 600;
    box-shadow: 0 2px 10px rgba(124,58,237,0.2);
}
.stDownloadButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(124,58,237,0.35);
}

/* ── DataFrames ── */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(100,116,139,0.15);
    border-radius: 10px;
    overflow: hidden;
}

/* ── Slider ── */
.stSlider > div > div > div > div {
    background: linear-gradient(90deg, #0891b2, #6366f1) !important;
}

/* ── Dividers ── */
hr {
    border-color: rgba(100,116,139,0.15) !important;
}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS & HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

# Zone color scheme (index 0 = nodata/background)
ZONE_HEX = {0: "#0f172a", 1: "#1a9850", 2: "#a6d96a", 3: "#fee08b",
             4: "#f46d43", 5: "#a50026"}
ZONE_RGBA = {
    0: (0, 0, 0, 0),
    1: (26, 152, 80, 160),
    2: (166, 217, 106, 160),
    3: (254, 224, 139, 175),
    4: (244, 109, 67, 185),
    5: (165, 0, 38, 200),
}

PRESET_LOCATIONS = {
    "Lagos Island": (6.4550, 3.4000),
    "Lekki Phase 1": (6.4375, 3.4730),
    "Victoria Island": (6.4281, 3.4219),
    "Ikeja (Mainland)": (6.6018, 3.3515),
    "Apapa (Port)": (6.4417, 3.3672),
    "Epe": (6.5842, 3.9833),
    "Badagry": (6.4165, 2.8843),
    "Ikorodu": (6.6194, 3.5105),
}


def _fmt(val, unit="", decimals=1):
    """Format a numeric value safely (returns 'N/A' for None)."""
    if val is None:
        return "N/A"
    if isinstance(val, float):
        return f"{val:,.{decimals}f}{unit}"
    return str(val)


# ═══════════════════════════════════════════════════════════════════════════════
# CACHED DATA LOADERS
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def get_hazard_overlay():
    """Read hazard zones TIF, colorize, and return base64 PNG + WGS84 bounds."""
    with rasterio.open(M._core("flood_hazard_zones.tif")) as ds:
        bounds = transform_bounds(ds.crs, "EPSG:4326", *ds.bounds)
        factor = 2
        zones = ds.read(1, out_shape=(ds.height // factor, ds.width // factor))

    h, w = zones.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)
    for z, c in ZONE_RGBA.items():
        rgba[zones == z] = c

    img = Image.fromarray(rgba)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return b64, bounds


@st.cache_data(ttl=3600)
def get_lga_json():
    """Load LGA boundaries as GeoJSON string."""
    return M.lga_boundaries().to_json()


@st.cache_data(ttl=3600)
def get_exposure_lga():
    return M.exposure_by_lga()


@st.cache_data(ttl=3600)
def get_exposure_zone():
    return M.exposure_by_zone()


@st.cache_data(ttl=3600)
def get_baseline():
    return M.real_baseline_exposure()


@st.cache_data(ttl=3600)
def get_climatology():
    return M.climatology()


# ═══════════════════════════════════════════════════════════════════════════════
# CHART HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _dark_fig(figsize=(10, 6)):
    """Create a matplotlib figure pre-styled for the dark theme."""
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("#0f172a")
    ax.set_facecolor("#0f172a")
    ax.tick_params(colors="#94a3b8", labelsize=9)
    for spine in ax.spines.values():
        spine.set_color("#334155")
    return fig, ax


def plot_lga_exposure_bar(df):
    """Horizontal bar chart of LGA exposure, sorted descending."""
    df_s = df.sort_values("pct_high_very_high", ascending=True).copy()
    fig, ax = _dark_fig(figsize=(10, 8))

    cmap = plt.cm.RdYlGn_r
    norm = plt.Normalize(df_s["pct_high_very_high"].min(),
                         df_s["pct_high_very_high"].max())
    colors = cmap(norm(df_s["pct_high_very_high"]))

    bars = ax.barh(df_s["lga_name"], df_s["pct_high_very_high"],
                   color=colors, edgecolor="none", height=0.72)

    ax.set_xlabel("Population in High / Very High Zones (%)",
                  color="#94a3b8", fontsize=11, labelpad=10)
    ax.set_title("LGA Flood Exposure Ranking",
                 color="#e2e8f0", fontsize=15, fontweight="bold", pad=14)
    ax.xaxis.grid(True, alpha=0.08, color="#475569")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    for bar, val in zip(bars, df_s["pct_high_very_high"]):
        ax.text(bar.get_width() + 0.4, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}%", va="center", color="#cbd5e1", fontsize=8.5,
                fontweight="500")

    plt.tight_layout()
    return fig


def plot_zone_donut(baseline):
    """Donut chart of statewide zone population shares."""
    labels = list(M.ZONE_NAMES.values())
    sizes = [baseline.get(l, 0) for l in labels]
    colors_list = [ZONE_HEX[i] for i in range(1, 6)]

    fig, ax = _dark_fig(figsize=(5, 5))
    wedges, texts, autotexts = ax.pie(
        sizes, labels=None, colors=colors_list, autopct="%1.1f%%",
        startangle=140, pctdistance=0.78,
        wedgeprops=dict(width=0.42, edgecolor="#0f172a", linewidth=2))

    for t in autotexts:
        t.set_color("#e2e8f0")
        t.set_fontsize(9)
        t.set_fontweight("bold")

    ax.legend(labels, loc="center left", bbox_to_anchor=(1, 0.5),
              fontsize=9, frameon=False, labelcolor="#cbd5e1")
    ax.set_title("Population by Hazard Zone", color="#e2e8f0",
                 fontsize=13, fontweight="bold", pad=10)
    plt.tight_layout()
    return fig


def plot_scenario_zones(zones, title):
    """Render a recomputed hazard-zone array as a styled matplotlib image."""
    cmap = ListedColormap([ZONE_HEX[i] for i in range(6)])
    norm = BoundaryNorm(range(7), cmap.N)

    fig, ax = _dark_fig(figsize=(10, 7))
    ax.imshow(zones, cmap=cmap, norm=norm, interpolation="nearest")
    ax.set_title(title, color="#e2e8f0", fontsize=14, fontweight="bold", pad=12)
    ax.axis("off")

    handles = [plt.Rectangle((0, 0), 1, 1, color=ZONE_HEX[i]) for i in range(1, 6)]
    leg = ax.legend(handles, list(M.ZONE_NAMES.values()), loc="lower left",
                    fontsize=9, framealpha=0.85, facecolor="#1e293b",
                    edgecolor="#334155", labelcolor="#e2e8f0")
    plt.tight_layout()
    return fig


def plot_scenario_comparison(baseline, scenario_exp):
    """Grouped bar chart comparing baseline vs scenario population per zone."""
    labels = list(M.ZONE_NAMES.values())
    base_vals = [baseline.get(l, 0) for l in labels]
    scn_vals = [scenario_exp[l]["people"] for l in labels]

    x = np.arange(len(labels))
    width = 0.35

    fig, ax = _dark_fig(figsize=(10, 5))
    bars1 = ax.bar(x - width / 2, base_vals, width, label="Baseline",
                   color="#0891b2", edgecolor="none", alpha=0.85)
    bars2 = ax.bar(x + width / 2, scn_vals, width, label="Scenario",
                   color="#a855f7", edgecolor="none", alpha=0.85)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, color="#94a3b8", fontsize=10)
    ax.set_ylabel("Population", color="#94a3b8", fontsize=11)
    ax.set_title("Baseline vs Scenario — Population per Zone",
                 color="#e2e8f0", fontsize=14, fontweight="bold", pad=12)
    ax.legend(facecolor="#1e293b", edgecolor="#334155", labelcolor="#e2e8f0",
              fontsize=10)
    ax.yaxis.grid(True, alpha=0.08, color="#475569")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Format y-axis with millions
    ax.yaxis.set_major_formatter(plt.FuncFormatter(
        lambda v, _: f"{v / 1e6:.1f}M" if v >= 1e6 else f"{v / 1e3:.0f}K"))

    plt.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# DOWNLOAD HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _exposure_csv(exp_dict):
    """Convert scenario exposure dict to CSV bytes."""
    rows = []
    for zone, data in exp_dict.items():
        if isinstance(data, dict):
            rows.append({"Zone": zone, **data})
    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8")


def _zones_geotiff(zones, ref):
    """Write scenario zones to an in-memory GeoTIFF; return bytes."""
    from rasterio.io import MemoryFile
    profile = {
        "driver": "GTiff", "dtype": "uint8",
        "width": ref["width"], "height": ref["height"],
        "count": 1, "crs": ref["crs"], "transform": ref["transform"],
        "compress": "lzw", "nodata": 0,
    }
    with MemoryFile() as mem:
        with mem.open(**profile) as ds:
            ds.write(zones, 1)
        return mem.read()


# ═══════════════════════════════════════════════════════════════════════════════
# HEADER & DISCLAIMER
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div style="text-align:center; padding:0.8rem 0 0.3rem 0;">
    <h1 style="font-size:2.3rem; margin-bottom:0.15rem;
               background:linear-gradient(135deg,#06b6d4,#8b5cf6);
               -webkit-background-clip:text; -webkit-text-fill-color:transparent;
               font-weight:800; letter-spacing:-0.02em;">
        🌊 Lagos Flood Hazard Explorer
    </h1>
    <p style="color:#64748b; font-size:0.95rem; margin-top:0;">
        Interactive Decision-Support Tool &nbsp;·&nbsp; Hazard &nbsp;·&nbsp; Exposure &nbsp;·&nbsp; Scenarios
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div style="background:linear-gradient(135deg,rgba(245,158,11,0.08),rgba(239,68,68,0.08));
            border:1px solid rgba(245,158,11,0.25); border-radius:10px;
            padding:0.55rem 1rem; margin-bottom:0.8rem;">
    <span style="color:#fbbf24;">⚠️</span>
    <span style="color:#94a3b8; font-size:0.82rem;">
        This is a <strong style="color:#e2e8f0;">hazard &amp; exposure decision-support tool</strong>
        — <em>not</em> a dated flood forecast. It shows where flooding is likely and models
        what-if rainfall scenarios.
    </span>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:0.8rem 0;">
        <div style="font-size:2.2rem;">🎓</div>
        <div style="color:#e2e8f0; font-weight:700; font-size:1rem; margin-top:0.3rem;">
            Final Year Project
        </div>
        <div style="color:#64748b; font-size:0.78rem; margin-top:0.15rem;">
            Civil &amp; Environmental Engineering
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown("""
    <div style="font-size:0.82rem; line-height:1.7; color:#94a3b8;">
        <strong style="color:#cbd5e1;">Title:</strong><br>
        Flood Risk Analysis and Visualization Web Portal for Lagos State, Nigeria<br><br>
        <strong style="color:#cbd5e1;">Student:</strong><br>
        Attah Gbubemi David (190402060)<br><br>
        <strong style="color:#cbd5e1;">Supervisor:</strong><br>
        Dr O. C. Echeta<br><br>
        <strong style="color:#cbd5e1;">Institution:</strong><br>
        Department of Civil &amp; Environmental Engineering<br>
        University of Lagos<br><br>
        <strong style="color:#cbd5e1;">Model:</strong><br>
        AHP Multi-Criteria (8 factors)<br>
        Gumbel EV-I Return Periods<br>
        SCS-CN Runoff Recomputation<br>
        SWAT+ Ogun Streamflow (calibrated)
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown("""
    <div style="background:rgba(6,182,212,0.08); border:1px solid rgba(6,182,212,0.2);
                border-radius:8px; padding:0.6rem 0.8rem; margin-top:0.2rem;">
        <div style="color:#06b6d4; font-weight:700; font-size:0.78rem;
                    text-transform:uppercase; letter-spacing:0.06em; margin-bottom:0.3rem;">
            AHP Factor Weights
        </div>
        <table style="width:100%; font-size:0.75rem; color:#94a3b8;">
            <tr><td>Elevation</td>      <td style="text-align:right; color:#e2e8f0;">0.20</td></tr>
            <tr><td>TWI</td>            <td style="text-align:right; color:#e2e8f0;">0.18</td></tr>
            <tr><td>Dist. to Rivers</td><td style="text-align:right; color:#e2e8f0;">0.15</td></tr>
            <tr><td>Flow Accum.</td>    <td style="text-align:right; color:#e2e8f0;">0.12</td></tr>
            <tr><td>Runoff</td>         <td style="text-align:right; color:#e2e8f0;">0.12</td></tr>
            <tr><td>Slope</td>          <td style="text-align:right; color:#e2e8f0;">0.10</td></tr>
            <tr><td>Rainfall</td>       <td style="text-align:right; color:#e2e8f0;">0.08</td></tr>
            <tr><td>LULC</td>           <td style="text-align:right; color:#e2e8f0;">0.05</td></tr>
            <tr style="border-top:1px solid #334155;">
                <td style="font-weight:700; color:#cbd5e1;">Total</td>
                <td style="text-align:right; font-weight:700; color:#06b6d4;">1.00</td>
            </tr>
        </table>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════════

(tab_overview, tab_map, tab_query, tab_exposure, tab_scenario, tab_climate,
 tab_hydro, tab_valid) = st.tabs([
    "📖 Overview",
    "🗺️ Hazard Map",
    "📍 Point Query",
    "👥 Exposure",
    "🌧️ Scenario",
    "📊 Climate",
    "🌊 Hydrology (SWAT+)",
    "✅ Validation",
])

# ─────────────────────── TAB 1 — PROJECT OVERVIEW ────────────────────────────
with tab_overview:
    st.markdown("""
    <div style="max-width:900px;">
        <h2 style="color:#e2e8f0; font-weight:700; margin-bottom:0.5rem;">
            Flood Risk Analysis and Visualization Web Portal
        </h2>
        <p style="color:#64748b; font-size:0.9rem; font-style:italic; margin-bottom:1.2rem;">
            Lagos State, Nigeria — Final Year Project
        </p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown("""
        <div style="background:linear-gradient(145deg,rgba(15,23,42,0.8),rgba(30,41,59,0.6));
                    border:1px solid rgba(100,116,139,0.15); border-radius:14px;
                    padding:1.2rem 1.4rem; height:100%;">
            <div style="color:#f97316; font-weight:700; font-size:0.82rem;
                        text-transform:uppercase; letter-spacing:0.06em;
                        margin-bottom:0.6rem;">🔍 Problem Statement</div>
            <p style="color:#cbd5e1; font-size:0.85rem; line-height:1.65;">
                Lagos State, with over <strong>21 million residents</strong> in a low-lying
                coastal setting, faces recurring and devastating flooding. Rapid urbanization,
                inadequate drainage infrastructure, and increasingly variable rainfall
                amplify the risk. This project develops a <em>spatial decision-support
                framework</em> to quantify and visualize flood hazard and population exposure
                across all 20 Local Government Areas.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div style="background:linear-gradient(145deg,rgba(15,23,42,0.8),rgba(30,41,59,0.6));
                    border:1px solid rgba(100,116,139,0.15); border-radius:14px;
                    padding:1.2rem 1.4rem; height:100%;">
            <div style="color:#06b6d4; font-weight:700; font-size:0.82rem;
                        text-transform:uppercase; letter-spacing:0.06em;
                        margin-bottom:0.6rem;">🔬 Methodology</div>
            <p style="color:#cbd5e1; font-size:0.85rem; line-height:1.65;">
                <strong>AHP Weighted Overlay</strong> of 8 conditioning factors — elevation,
                TWI, proximity to rivers, flow accumulation, SCS-CN runoff depth, slope,
                extreme rainfall, and land-use — to produce a continuous <em>Flood Hazard
                Index (0–1)</em> classified into 5 zones.<br><br>
                <strong>Gumbel EV-I</strong> model fitted to 30 years of NIMET rainfall
                to estimate design storms for 2–100 year return periods.<br><br>
                <strong>WorldPop 2020</strong> grid for population exposure analysis.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown("""
        <div style="background:linear-gradient(145deg,rgba(15,23,42,0.8),rgba(30,41,59,0.6));
                    border:1px solid rgba(100,116,139,0.15); border-radius:14px;
                    padding:1.2rem 1.4rem; height:100%;">
            <div style="color:#a855f7; font-weight:700; font-size:0.82rem;
                        text-transform:uppercase; letter-spacing:0.06em;
                        margin-bottom:0.6rem;">📊 Key Findings</div>
            <p style="color:#cbd5e1; font-size:0.85rem; line-height:1.65;">
                <strong>~4.81 million people</strong> reside in High or Very High hazard
                zones — approximately <strong>22.8%</strong> of Lagos State's population.<br><br>
                Flood hazard is <strong>topography-dominated</strong>: elevation + TWI account
                for 38% of the index weight. Rainfall factors contribute 20%, meaning rainfall
                scenario effects are intentionally modest — the map is structurally realistic.<br><br>
                Annual mean temperature shows a <strong>statistically significant increasing
                trend</strong> (+0.44°C/decade), while annual rainfall shows no significant
                long-term trend.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height:0.8rem;'></div>", unsafe_allow_html=True)

    with st.expander("📚 Data Sources & Limitations", expanded=False):
        st.markdown("""
        **Statewide hazard & exposure model (AHP)**

        | Dataset | Source | Resolution / Period |
        |---------|--------|---------------------|
        | Elevation (DEM) | SRTM | 30 m |
        | Land Use / Land Cover | Sentinel-2 (Random Forest classification) | 10 m |
        | Rainfall | NiMet Ikeja station + CHIRPS validation | 1996–2025 (30 yr) |
        | Population | WorldPop | ~100 m |
        | Administrative boundaries | GADM v4.1 (20 Lagos LGAs) | — |
        | Rivers / drainage | HydroSHEDS / HydroRIVERS | 15 arc-sec |

        **Ogun catchment hydrological model (SWAT+)**

        | Dataset | Source | Resolution / Period |
        |---------|--------|---------------------|
        | Elevation (DEM) | Copernicus GLO-30 | 30 m → 90 m |
        | Land cover | ESA WorldCover v200 | 10 m → 90 m |
        | Soil | SoilGrids, 0–5 cm sand/clay | 250 m → 90 m |
        | Rainfall forcing | CHIRPS daily, 23 subbasin stations | 2010–2023 |
        | Temperature forcing | ERA5-Land daily tmax/tmin | 2010–2023 |
        | Discharge (calibration) | GEOGLOWS v2, reach 140585128 | Monthly, 2011–2023 |

        **Independent validation data**

        | Dataset | Source | Used for |
        |---------|--------|----------|
        | MOD16A2GF evapotranspiration | MODIS / NASA | SWAT+ ET check |
        | TerraClimate actual ET | Abatzoglou et al. (2018) | Second ET reference |
        | Flood extent, Jul–Nov 2012 | MODIS 250 m (NASA/DFO via HDX) | Hazard map validation |
        | Flood reports, 2022 | NEMA via HDX (62 Lagos records) | LGA-level check |

        **Limitations:**
        - The LULC classification has **~53% overall accuracy** — don't overstate fine-grained land-use effects.
        - AHP is a **multi-criteria index**, not a calibrated hydraulic model (no flood depth/velocity).
        - The hazard map **ranks** susceptibility well (enrichment rises to 1.61× in Very High) but
          discriminates weakly: AUC-ROC 0.62, below the 0.70 acceptance threshold.
        - SWAT+ was calibrated against **modelled** (GEOGLOWS) rather than gauged discharge.
        - Oyan Dam releases are not modelled, so the 2022 flood is outside the model's scope.
        - Scenario exposure numbers should be interpreted as **relative changes**, not absolute predictions.
        """)


# ─────────────────────── TAB 2 — HAZARD MAP ──────────────────────────────────
with tab_map:
    st.markdown("""
    <h3 style="color:#e2e8f0; font-weight:700; margin-bottom:0.3rem;">
        Baseline Flood Hazard Zones
    </h3>
    <p style="color:#64748b; font-size:0.85rem; margin-bottom:0.8rem;">
        AHP-weighted overlay of 8 conditioning factors. Click LGA polygons for names.
        Use layer controls (top-right) to toggle overlays.
    </p>
    """, unsafe_allow_html=True)

    map_col, legend_col = st.columns([4, 1])

    with map_col:
        b64_img, bounds = get_hazard_overlay()
        lga_json = get_lga_json()
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2

        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=10,
            tiles="CartoDB dark_matter",
            control_scale=True,
        )

        folium.raster_layers.ImageOverlay(
            image=f"data:image/png;base64,{b64_img}",
            bounds=[[bounds[1], bounds[0]], [bounds[3], bounds[2]]],
            opacity=0.75,
            name="Flood Hazard Zones",
        ).add_to(m)

        folium.GeoJson(
            lga_json,
            name="LGA Boundaries",
            style_function=lambda x: {
                "fillColor": "transparent",
                "color": "#06b6d4",
                "weight": 1.8,
                "dashArray": "6, 4",
            },
            tooltip=folium.GeoJsonTooltip(
                fields=["NAME_2"],
                aliases=["LGA:"],
                style="background-color:#1e293b;color:#e2e8f0;border:1px solid #334155;border-radius:4px;padding:6px 10px;font-size:13px;",
            ),
        ).add_to(m)

        folium.LayerControl(collapsed=False).add_to(m)

        st_folium(m, width=None, height=580, returned_objects=[])

    with legend_col:
        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background:rgba(15,23,42,0.85); border:1px solid rgba(100,116,139,0.15);
                    border-radius:12px; padding:1rem; font-size:0.82rem;">
            <div style="color:#e2e8f0; font-weight:700; margin-bottom:0.7rem;
                        text-transform:uppercase; font-size:0.75rem; letter-spacing:0.06em;">
                Hazard Zone Legend
            </div>
        """, unsafe_allow_html=True)

        for z in range(1, 6):
            color = ZONE_HEX[z]
            name = M.ZONE_NAMES[z]
            lo = M.ZONE_BREAKS[z - 1]
            hi = M.ZONE_BREAKS[z]
            st.markdown(f"""
            <div style="display:flex; align-items:center; margin-bottom:0.5rem;">
                <div style="width:18px; height:18px; border-radius:4px;
                            background:{color}; margin-right:8px; flex-shrink:0;
                            border:1px solid rgba(255,255,255,0.1);"></div>
                <div>
                    <span style="color:#e2e8f0; font-weight:600;">{name}</span><br>
                    <span style="color:#64748b; font-size:0.72rem;">{lo:.2f} – {hi:.2f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<div style='height:0.8rem;'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background:rgba(6,182,212,0.06); border:1px solid rgba(6,182,212,0.15);
                    border-radius:10px; padding:0.7rem 0.9rem;">
            <div style="color:#06b6d4; font-weight:600; font-size:0.75rem;
                        text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.3rem;">
                Map Details
            </div>
            <div style="color:#94a3b8; font-size:0.75rem; line-height:1.6;">
                CRS: EPSG:32631 (UTM 31N)<br>
                Classification: Equal Interval<br>
                Basemap: CartoDB Dark Matter<br>
                LGA Boundaries: GADM
            </div>
        </div>
        """, unsafe_allow_html=True)


# ─────────────────────── TAB 3 — POINT QUERY ─────────────────────────────────
with tab_query:
    st.markdown("""
    <h3 style="color:#e2e8f0; font-weight:700; margin-bottom:0.3rem;">
        Location Hazard Inspector
    </h3>
    <p style="color:#64748b; font-size:0.85rem; margin-bottom:0.8rem;">
        Enter coordinates (WGS84) or pick a preset to query all model layers at that point.
    </p>
    """, unsafe_allow_html=True)

    # Preset buttons
    st.markdown("""
    <div style="color:#94a3b8; font-size:0.78rem; font-weight:600;
                text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.3rem;">
        Quick Presets
    </div>
    """, unsafe_allow_html=True)

    preset_cols = st.columns(len(PRESET_LOCATIONS))
    selected_preset = None
    for i, (name, (plat, plon)) in enumerate(PRESET_LOCATIONS.items()):
        if preset_cols[i].button(name, key=f"preset_{i}", use_container_width=True):
            selected_preset = (plat, plon, name)

    st.markdown("<div style='height:0.4rem;'></div>", unsafe_allow_html=True)

    q_c1, q_c2, q_c3 = st.columns([1, 1, 1])
    default_lat = selected_preset[0] if selected_preset else 6.4550
    default_lon = selected_preset[1] if selected_preset else 3.4000

    with q_c1:
        lat = st.number_input("Latitude", value=default_lat, format="%.4f",
                              min_value=6.3, max_value=6.8, step=0.001,
                              key="query_lat")
    with q_c2:
        lon = st.number_input("Longitude", value=default_lon, format="%.4f",
                              min_value=2.7, max_value=4.4, step=0.001,
                              key="query_lon")
    with q_c3:
        st.markdown("<div style='height:1.7rem;'></div>", unsafe_allow_html=True)
        run_query = st.button("🔍  Query Location", use_container_width=True,
                              key="run_query")

    if run_query or selected_preset:
        query_lat = selected_preset[0] if selected_preset else lat
        query_lon = selected_preset[1] if selected_preset else lon

        with st.spinner("Sampling model layers..."):
            r = M.point_query(query_lat, query_lon)

        if r.get("hazard_zone") is not None:
            zone_idx = r["hazard_zone"]
            zone_name = r.get("hazard_zone_name", "Unknown")
            zone_color = ZONE_HEX.get(zone_idx, "#64748b")

            # Header card
            loc_label = selected_preset[2] if selected_preset else f"{query_lat:.4f}°N, {query_lon:.4f}°E"
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,rgba(15,23,42,0.9),rgba(30,41,59,0.7));
                        border:1px solid rgba(100,116,139,0.15); border-radius:14px;
                        padding:1rem 1.4rem; margin:0.5rem 0 0.8rem 0;">
                <div style="display:flex; align-items:center; gap:0.8rem;">
                    <div style="width:48px; height:48px; border-radius:12px;
                                background:{zone_color}; display:flex;
                                align-items:center; justify-content:center;
                                font-size:1.2rem; font-weight:800; color:white;">
                        {zone_idx}
                    </div>
                    <div>
                        <div style="color:#e2e8f0; font-size:1.15rem; font-weight:700;">
                            {zone_name} Hazard Zone
                        </div>
                        <div style="color:#64748b; font-size:0.82rem;">
                            📍 {loc_label}
                            {f" &nbsp;·&nbsp; LGA: {r.get('lga', 'N/A')}" if r.get('lga') else ""}
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Detail metrics
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Hazard Index",
                      _fmt(r.get("flood_hazard_index"), decimals=3))
            m2.metric("Elevation",
                      _fmt(r.get("elevation_m"), " m"))
            m3.metric("Slope",
                      _fmt(r.get("slope_deg"), "°"))
            m4.metric("TWI",
                      _fmt(r.get("twi"), decimals=2))
            m5.metric("Dist. to River",
                      _fmt(r.get("distance_to_rivers_m"), " m", decimals=0))

            mc1, mc2 = st.columns(2)
            mc1.metric("Runoff Depth",
                       _fmt(r.get("runoff_depth_mm"), " mm", decimals=1))
            mc2.metric("Local Government Area", r.get("lga") or "N/A")

            with st.expander("📋 Raw JSON Response"):
                st.json(r)

        else:
            st.warning("⚠️ This location falls outside the Lagos model extent or returned "
                       "no data. Try coordinates within Lagos State "
                       "(Lat ≈ 6.4–6.7°N, Lon ≈ 2.7–4.4°E).")


# ─────────────────────── TAB 4 — EXPOSURE DASHBOARD ──────────────────────────
with tab_exposure:
    st.markdown("""
    <h3 style="color:#e2e8f0; font-weight:700; margin-bottom:0.3rem;">
        Population Exposure Dashboard
    </h3>
    <p style="color:#64748b; font-size:0.85rem; margin-bottom:0.8rem;">
        Baseline population exposure to flood hazard across all 20 Local Government Areas.
        Data source: WorldPop 2020 gridded population.
    </p>
    """, unsafe_allow_html=True)

    baseline = get_baseline()
    df_lga = get_exposure_lga().sort_values("pct_high_very_high", ascending=False)

    # Top-line metrics
    met1, met2, met3, met4 = st.columns(4)
    met1.metric("Total Population (Model)",
                f"{baseline.get('total', 0):,.0f}")
    met2.metric("High + Very High Zones",
                f"{baseline.get('High+VeryHigh', 0):,.0f}")
    met3.metric("% in High / Very High",
                f"{100 * baseline.get('High+VeryHigh', 0) / max(baseline.get('total', 1), 1):.1f}%")
    met4.metric("Most Exposed LGA",
                df_lga.iloc[0]["lga_name"] if not df_lga.empty else "N/A",
                f"{df_lga.iloc[0]['pct_high_very_high']:.1f}% exposed" if not df_lga.empty else "")

    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

    chart_col, donut_col = st.columns([3, 1.3])

    with chart_col:
        fig_bar = plot_lga_exposure_bar(df_lga)
        st.pyplot(fig_bar, use_container_width=True)
        plt.close(fig_bar)

    with donut_col:
        fig_donut = plot_zone_donut(baseline)
        st.pyplot(fig_donut, use_container_width=True)
        plt.close(fig_donut)

    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)

    with st.expander("📋 Full LGA Exposure Table", expanded=False):
        st.dataframe(df_lga, use_container_width=True, hide_index=True)

    # Download
    csv_bytes = df_lga.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️  Download Exposure Data (CSV)", csv_bytes,
        file_name="lagos_exposure_by_lga.csv", mime="text/csv",
    )


# ─────────────────────── TAB 5 — SCENARIO SIMULATOR ──────────────────────────
with tab_scenario:
    st.markdown("""
    <h3 style="color:#e2e8f0; font-weight:700; margin-bottom:0.3rem;">
        Rainfall What-If Scenario Simulator
    </h3>
    <p style="color:#64748b; font-size:0.85rem; margin-bottom:0.8rem;">
        Adjust rainfall intensity and recompute the flood hazard map and population exposure
        in real time. Requires the <code>models/factors/</code> folder (~284 MB).
    </p>
    """, unsafe_allow_html=True)

    factors_available = os.path.isdir(M.FACT) and os.path.exists(
        os.path.join(M.FACT, "dem.tif"))

    if not factors_available:
        st.error("⚠️ The `models/factors/` directory is missing or incomplete. "
                 "The scenario simulator requires the full factor rasters (~284 MB). "
                 "Copy the `factors/` folder into `models/` and restart.")
    else:
        sc1, sc2 = st.columns(2)

        with sc1:
            mode = st.radio("Scenario input mode:", ["📊 Percentage change",
                            "🌧️ NIMET return-period storm"],
                            horizontal=True, key="scenario_mode")

        with sc2:
            st.markdown("")  # spacer

        if "📊" in mode:
            pct = st.slider("Rainfall change (%)", min_value=-50, max_value=100,
                            value=30, step=5, key="rain_pct")
            scale = 1 + pct / 100
            st.markdown(f"""
            <div style="color:#94a3b8; font-size:0.85rem;">
                Rainfall multiplier: <strong style="color:#06b6d4;">×{scale:.2f}</strong>
                &nbsp;({'increase' if pct > 0 else 'decrease' if pct < 0 else 'baseline'})
            </div>
            """, unsafe_allow_html=True)
        else:
            T = st.select_slider("Return period (years)",
                                 options=[2, 5, 10, 25, 50, 100], value=100,
                                 key="return_period_slider")
            design = M.design_rainfall(T)
            scale = design / 1822.0
            st.markdown(f"""
            <div style="color:#94a3b8; font-size:0.85rem;">
                {T}-year design rainfall ≈ <strong style="color:#a855f7;">
                {design:,.0f} mm</strong> → ×{scale:.2f} of the 1,822 mm annual mean
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height:0.3rem;'></div>", unsafe_allow_html=True)

        if st.button("🚀  Run Scenario", use_container_width=False, key="run_scenario"):
            baseline_exp = get_baseline()

            with st.spinner("Recomputing hazard index + exposure (first run may take a moment)..."):
                exp, zones = M.scenario_exposure(scale)
                _, _, ref = M.recompute_hazard(scale)

            hv = exp["High+VeryHigh"]

            # Result metrics
            r1, r2, r3 = st.columns(3)
            r1.metric("High + Very High (Projected)",
                      f"{hv['people']:,.0f}",
                      f"{hv['delta']:+,.0f} people")
            r2.metric("Change (%)",
                      f"{hv['pct_change']:+.2f}%")
            r3.metric("Rainfall Scale",
                      f"×{scale:.2f}")

            st.markdown("<div style='height:0.4rem;'></div>", unsafe_allow_html=True)

            map_c, chart_c = st.columns([1.2, 1])

            with map_c:
                fig_zones = plot_scenario_zones(
                    zones[::4, ::4],
                    f"Hazard Zones — Rainfall ×{scale:.2f}")
                st.pyplot(fig_zones, use_container_width=True)
                plt.close(fig_zones)

            with chart_c:
                fig_comp = plot_scenario_comparison(baseline_exp, exp)
                st.pyplot(fig_comp, use_container_width=True)
                plt.close(fig_comp)

            st.markdown("""
            <div style="background:linear-gradient(135deg,rgba(245,158,11,0.06),rgba(239,68,68,0.06));
                        border:1px solid rgba(245,158,11,0.2); border-radius:8px;
                        padding:0.55rem 1rem; margin:0.6rem 0;">
                <span style="color:#fbbf24; font-size:0.85rem;">ℹ️</span>
                <span style="color:#94a3b8; font-size:0.8rem;">
                    Absolute numbers are anchored to the validated baseline; the scenario applies
                    the model's relative zone shift. Rainfall drives 0.20 of the 1.0 index weight,
                    so effects are modest — Lagos hazard is topography-dominated.
                </span>
            </div>
            """, unsafe_allow_html=True)

            # Downloads
            st.markdown("<div style='height:0.4rem;'></div>", unsafe_allow_html=True)
            dl1, dl2 = st.columns(2)

            with dl1:
                st.download_button(
                    "⬇️  Download Scenario Exposure (CSV)",
                    _exposure_csv(exp),
                    file_name=f"scenario_exposure_x{scale:.2f}.csv",
                    mime="text/csv",
                )

            with dl2:
                tiff_bytes = _zones_geotiff(zones, ref)
                st.download_button(
                    "⬇️  Download Scenario Zones (GeoTIFF)",
                    tiff_bytes,
                    file_name=f"scenario_zones_x{scale:.2f}.tif",
                    mime="image/tiff",
                )


# ─────────────────────── TAB 6 — CLIMATE CENTER ──────────────────────────────
with tab_climate:
    st.markdown("""
    <h3 style="color:#e2e8f0; font-weight:700; margin-bottom:0.3rem;">
        Climate Analysis &amp; Trend Center
    </h3>
    <p style="color:#64748b; font-size:0.85rem; margin-bottom:0.8rem;">
        30-year analysis of NiMet Ikeja station data (1996–2025): rainfall trends,
        temperature, humidity, and Gumbel return-period estimates.
    </p>
    """, unsafe_allow_html=True)

    # Return-period calculator
    calc1, calc2 = st.columns(2)

    with calc1:
        st.markdown("""
        <div style="background:linear-gradient(145deg,rgba(15,23,42,0.8),rgba(30,41,59,0.6));
                    border:1px solid rgba(100,116,139,0.15); border-radius:14px;
                    padding:1rem 1.2rem;">
            <div style="color:#06b6d4; font-weight:700; font-size:0.78rem;
                        text-transform:uppercase; letter-spacing:0.06em; margin-bottom:0.5rem;">
                Return Period → Design Rainfall
            </div>
        </div>
        """, unsafe_allow_html=True)
        T_input = st.number_input("Return period (years)", min_value=2,
                                  max_value=1000, value=100, step=1,
                                  key="calc_T")
        dr = M.design_rainfall(T_input)
        st.metric("Design Rainfall", f"{dr:,.0f} mm")

    with calc2:
        st.markdown("""
        <div style="background:linear-gradient(145deg,rgba(15,23,42,0.8),rgba(30,41,59,0.6));
                    border:1px solid rgba(100,116,139,0.15); border-radius:14px;
                    padding:1rem 1.2rem;">
            <div style="color:#a855f7; font-weight:700; font-size:0.78rem;
                        text-transform:uppercase; letter-spacing:0.06em; margin-bottom:0.5rem;">
                Observed Rainfall → Return Period
            </div>
        </div>
        """, unsafe_allow_html=True)
        rain_input = st.number_input("Annual rainfall (mm)", min_value=500,
                                     max_value=6000, value=3932, step=50,
                                     key="calc_rain")
        rp = M.return_period(rain_input)
        rp_label = f"{rp:,.0f} years" if rp < 10000 else "> 10,000 years"
        st.metric("Return Period", rp_label)

    st.divider()

    # NIMET charts
    st.markdown("""
    <div style="color:#e2e8f0; font-weight:700; font-size:1.05rem; margin-bottom:0.6rem;">
        📈 NIMET Climate Charts
    </div>
    """, unsafe_allow_html=True)

    chart_files = [
        ("fig_nimet_climatology.png", "Monthly Climatology",
         "30-year mean monthly rainfall, temperature, and relative humidity at Ikeja."),
        ("fig_nimet_rainfall_trend.png", "Annual Rainfall Trend",
         "Annual total rainfall with Mann-Kendall trend test (no significant trend detected)."),
        ("fig_nimet_temp_rh_trend.png", "Temperature & Humidity Trends",
         "Significant warming trend of +0.44°C/decade; humidity shows no significant trend."),
        ("fig_nimet_return_periods.png", "Gumbel Return Periods",
         "Estimated design rainfall depths for various return periods (2–100 years)."),
        ("fig_nimet_chirps_validation.png", "CHIRPS Validation",
         "Cross-validation of NIMET station data against CHIRPS satellite rainfall estimates (r = 0.77)."),
    ]

    for i in range(0, len(chart_files), 2):
        cols = st.columns(2)
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(chart_files):
                fname, title, desc = chart_files[idx]
                fpath = M._core(fname)
                with col:
                    if os.path.exists(fpath):
                        st.markdown(f"""
                        <div style="color:#e2e8f0; font-weight:600; font-size:0.9rem;
                                    margin-bottom:0.2rem;">{title}</div>
                        <div style="color:#64748b; font-size:0.78rem;
                                    margin-bottom:0.4rem;">{desc}</div>
                        """, unsafe_allow_html=True)
                        st.image(fpath, use_container_width=True)
                    else:
                        st.info(f"Chart not found: {fname}")

    st.divider()

    # Climatology table
    with st.expander("📋 Monthly Climatology Table", expanded=False):
        clim = get_climatology()
        st.dataframe(clim, use_container_width=True, hide_index=True)

    csv_clim = get_climatology().to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️  Download Climatology Data (CSV)", csv_clim,
        file_name="nimet_climatology_1996_2025.csv", mime="text/csv",
    )

# ─────────────────────── TAB 7 — SWAT+ HYDROLOGY ─────────────────────────────
with tab_hydro:
    st.markdown("## 🌊 Ogun River Hydrology — SWAT+ Model")
    st.markdown(
        "A **calibrated, process-based SWAT+ model** of the **Ogun River catchment** "
        "(~19,915 km²) — the largest fluvial input to the Lagos Lagoon. Where the statewide "
        "hazard map is a multi-criteria *susceptibility* index, this simulates the actual "
        "**rainfall → runoff → streamflow** process, day by day, across 23 subbasins."
    )
    if not M.swat_available():
        st.info("SWAT+ results not bundled. Build the model per `swat/METHODOLOGY_LOG.md`.")
    else:
        cal = M.swat_calibration()
        st.markdown("### ✅ Calibration performance")
        c1, c2, c3 = st.columns(3)
        c1.metric("NSE", f"{cal['nse']:.2f}", "target ≥ 0.50")
        c2.metric("R²", f"{cal['r2']:.2f}", "target ≥ 0.60")
        c3.metric("PBIAS", f"{cal['pbias']:+.1f}%", "target ±25%")
        st.caption(
            f"Monthly discharge vs GEOGLOWS at the Ogun outlet ({cal['period']}). "
            f"Independent validation 2018–2023: NSE {cal['validation_2018_2023']['nse']:.2f}, "
            f"R² {cal['validation_2018_2023']['r2']:.2f} — validation ≥ calibration, so the "
            "model generalises rather than overfitting."
        )

        st.markdown("### 📈 Monthly discharge — observed vs simulated")
        _hy = M.swat_hydrograph()
        _mo = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        _dfh = pd.DataFrame({
            "Observed (GEOGLOWS)": [h["obs"] for h in _hy],
            "Simulated (SWAT+)": [h["sim"] for h in _hy],
        }, index=_mo)
        st.line_chart(_dfh, height=320)
        st.caption("Mean monthly outlet discharge (m³/s). The Sept–Oct peak matches the Lagos flood season.")

        st.markdown("### 🌧️ Rainfall scenarios (process-based)")
        _sc = M.swat_scenarios()
        _dfs = pd.DataFrame(_sc)
        st.dataframe(
            _dfs.rename(columns={"label": "Scenario", "mean": "Mean flow (m³/s)",
                                 "peak": "Peak month (m³/s)", "d_mean": "Δ mean %",
                                 "d_peak": "Δ peak %"})[
                ["Scenario", "Mean flow (m³/s)", "Peak month (m³/s)", "Δ mean %", "Δ peak %"]],
            use_container_width=True, hide_index=True,
        )
        st.bar_chart(_dfs.set_index("label")[["mean", "peak"]], height=280)
        st.caption(
            "A **+10% rainfall increase drives ~+15% mean flow** — the nonlinear rainfall–runoff "
            "amplification a process model captures, unlike a linear index."
        )

        _s = M.swat_summary()
        _ex = _s["extreme_year"]
        st.markdown(
            f"**Extreme historical (wettest simulated year): {_ex['year']}** — "
            f"annual mean {_ex['annual_mean']} m³/s, peak month {_ex['peak_month']} m³/s."
        )
        st.warning("⚠️ " + _s["note_2022"])
        st.caption(
            "Calibrated against GEOGLOWS modelled discharge (a recognised data-scarce approach). "
            "Oyan Dam regulation is not modelled — a documented limitation. "
            "Full build & calibration trail: `swat/METHODOLOGY_LOG.md`."
        )


# ─────────────────────── TAB 8 — INDEPENDENT VALIDATION ──────────────────────
with tab_valid:
    st.markdown("## ✅ Independent Validation")
    st.markdown(
        "Checks the model was **not** tuned to. The SWAT+ parameters were fitted to "
        "discharge alone and the AHP map was built from expert weights, so everything "
        "below is an out-of-sample test. Results are mixed — they are reported as found."
    )

    if not M.validation_available():
        st.info("Validation results not bundled. Run `validation/build_validation_bundle.py`.")
    else:
        _v = M.validation_summary()
        _et = M.et_validation()
        _sp = M.spatial_validation()
        _a = _sp["test_a_pixel_level"]
        _b = _sp["test_b_lga_level"]

        # ── 1. ET check ──────────────────────────────────────────────────────
        st.markdown("### 1 · Evapotranspiration — a second variable, never calibrated to")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Monthly NSE", f"{_et['monthly']['nse']:.2f}")
        c2.metric("Monthly R²", f"{_et['monthly']['r2']:.2f}")
        c3.metric("PBIAS", f"{_et['monthly']['pbias']:+.1f}%",
                  help="Within the ±25% Moriasi band")
        c4.metric("Annual ET", f"{_et['annual_mm']['swat']:.0f} mm",
                  delta=f"{_et['annual_mm']['swat'] - _et['annual_mm']['reference']:+.0f} vs ref")

        _c = _et["climatology"]
        st.line_chart(
            pd.DataFrame(
                {"Reference ET": _c["ref_mm"], "SWAT+ simulated ET": _c["sim_mm"]},
                # zero-padded so Streamlit's alphabetical index sort stays chronological
                index=[f"{m:02d} {calendar.month_abbr[m]}" for m in range(1, 13)],
            ),
            height=260,
        )
        st.markdown(
            f"**Verdict — {_v['honest_status']['et_independent_check']}**"
        )
        _alt = M.et_validation_corroborating()
        if _alt:
            st.success(
                "✅ **Two independent references agree.** MODIS MOD16 "
                f"({_et['annual_mm']['reference']:.0f} mm/yr) and TerraClimate "
                f"({_alt['annual_mm']['reference']:.0f} mm/yr) were tested separately "
                "and show the same damped seasonal cycle. The finding is robust, not "
                "an artefact of one product."
            )
        st.caption(
            f"Primary reference: {_et['reference_product']} — a true satellite ET "
            "retrieval, the product specified for this validation. Regenerate with "
            "`swat/validation/fetch_mod16_et_gee.js`, then "
            "`et_validation.py --reference <csv>`."
        )

        # ── 2. Calibration trade-off ─────────────────────────────────────────
        st.markdown("### 2 · Why the parameters were not re-tuned to ET")
        _t = M.calibration_tradeoff()
        st.dataframe(
            pd.DataFrame([{
                "petco": r["petco"],
                "Discharge NSE": r["discharge"]["nse"],
                "Discharge R²": r["discharge"]["r2"],
                "Discharge PBIAS %": r["discharge"]["pbias"],
                "ET NSE": r["et"]["nse"],
                "ET PBIAS %": r["et"]["pbias"],
                "Meets thresholds": "✅" if r["discharge_passes"] else "❌",
            } for r in _t["runs"]]),
            use_container_width=True, hide_index=True,
        )
        st.info("🔍 " + _t["diagnosis"])

        # ── 3. Hazard map vs observed floods ─────────────────────────────────
        st.markdown("### 3 · Hazard map vs observed floods")
        c1, c2, c3 = st.columns(3)
        c1.metric("AUC-ROC", f"{_a['auc_roc']:.2f}",
                  help="0.5 = no skill, 1.0 = perfect")
        c2.metric("High+V.High enrichment", f"{_a['high_veryhigh_enrichment']:.2f}×",
                  help="Share of observed flood vs share of Lagos area")
        c3.metric("Observed flood area", f"{_a['flood_area_km2']:.0f} km²")

        st.dataframe(
            pd.DataFrame([{
                "Hazard zone": z,
                "% of observed flood": _a["zones"][z]["pct_of_observed_flood"],
                "% of Lagos": _a["zones"][z]["pct_of_lagos"],
                "Enrichment": _a["zones"][z]["enrichment"],
            } for z in ("Very Low", "Low", "Moderate", "High", "Very High")]),
            use_container_width=True, hide_index=True,
        )
        st.markdown(
            "Enrichment climbs monotonically across the zones — the map **ranks** "
            "flood risk in the right order. Discrimination is modest, not strong."
        )

        # ── 4. The negative result ───────────────────────────────────────────
        st.markdown("### 4 · LGA-level check — an inconclusive result")
        c1, c2, c3 = st.columns(3)
        c1.metric("ρ vs modelled exposure", f"{_b['spearman_rho']:+.2f}")
        c2.metric("ρ vs absolute exposed", f"{_b['spearman_rho_vs_absolute_exposed']:+.2f}")
        c3.metric("ρ vs raw population", f"{_b['spearman_rho_vs_population']:+.2f}")
        st.warning(
            "⚠️ NEMA flood-report counts track **raw population** far better than "
            "modelled exposure. Reporting effort — not flood hazard — dominates this "
            "dataset, so it cannot validate the map. Reported as a null result."
        )
        st.dataframe(
            pd.DataFrame(_b["per_lga"]).rename(columns={
                "lga": "LGA", "nema_reports": "NEMA reports",
                "model_pct_high_vh": "Model % High+V.High",
                "population": "Population",
                "model_people_high_vh": "People exposed",
            }),
            use_container_width=True, hide_index=True, height=320,
        )

        st.error("🚫 **Not claimed:** " + _v["honest_status"]["not_claimed"])
        st.caption(
            "Sources: MODIS 250 m flood extent Jul–Nov 2012 (NASA/DFO via HDX); "
            "NEMA 2022 Lagos flood records (62 reports, via HDX). "
            "Method and caveats: `validation/spatial_validation.py`."
        )
