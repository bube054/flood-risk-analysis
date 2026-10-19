"""
app.py — Lagos Flood Hazard & Exposure Explorer
=================================================
Interactive explorer over the AHP flood hazard model, population exposure,
NIMET climate analysis and the SWAT+ Ogun model for Lagos State, Nigeria.

Light and dark themes are defined in .streamlit/config.toml; viewers switch
between them from the top-right menu. Custom HTML below takes its
colours from CSS light-dark() tokens, so it follows the switch without a rerun.

Run:  streamlit run app.py
"""
import base64
import calendar
import io
import itertools
import json
import os

import altair as alt
import folium
import folium.raster_layers
from branca.element import MacroElement
from folium.template import Template
import numpy as np
import pandas as pd
import rasterio
from rasterio.features import geometry_mask
from rasterio.transform import Affine
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
    page_icon=":material/flood:",
    layout="wide",
    initial_sidebar_state="auto",   # open on desktop, collapsed on phones
)

# ═══════════════════════════════════════════════════════════════════════════════
# STYLES
# ═══════════════════════════════════════════════════════════════════════════════
# Streamlit sets `color-scheme` on .stApp from the active theme, so light-dark()
# resolves to the right side for everything inside it.
st.markdown("""
<style>
.stApp {
    --fx-bg: light-dark(#f6f5f1, #141618);
    --fx-ink: light-dark(#1c1f23, #e3e1db);
    --fx-muted: light-dark(#5a6067, #a0a5ab);
    --fx-rule: light-dark(#d5d1c7, #34383c);
    --fx-panel: light-dark(#ebe8e1, #1f2225);
    --fx-accent: light-dark(#1d5689, #86b6e0);
    --fx-caution: light-dark(#9a6200, #e0b35a);
    --fx-negative: light-dark(#a3322a, #e88a80);
    --fx-positive: light-dark(#3f7a3b, #8fc489);
    --fx-serif: "Source Serif 4", Georgia, "Times New Roman", serif;
}

/* The header floats over the scrolling page, so it needs the page colour or
   content shows through behind the sidebar toggle and the menu. */
header[data-testid="stHeader"] { background: var(--fx-bg); }
.block-container, [data-testid="stMainBlockContainer"] {
    padding-top: 2.4rem;
    padding-bottom: 3rem;
    max-width: 1320px;
}

/* ── Type ── */
.fx-overline, .fx-label {
    font-size: 0.72rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    font-weight: 600;
    color: var(--fx-muted);
}
.fx-label { margin-bottom: 0.5rem; }
.stApp .fx-title {
    font-family: var(--fx-serif);
    font-size: 2.35rem;
    font-weight: 600;
    line-height: 1.15;
    letter-spacing: -0.01em;
    color: var(--fx-ink);
    margin: 0.35rem 0 0.35rem;
}
.fx-sub { color: var(--fx-muted); font-size: 1rem; margin: 0; max-width: 62rem; }
.fx-masthead { padding-bottom: 1.1rem; border-bottom: 1px solid var(--fx-rule); }
.fx-disclaimer {
    margin-top: 0.95rem;
    padding: 0.1rem 0 0.1rem 0.75rem;
    border-left: 3px solid var(--fx-caution);
    color: var(--fx-muted);
    font-size: 0.87rem;
}
.fx-disclaimer strong { color: var(--fx-ink); font-weight: 600; }

.fx-section { margin: 1.1rem 0 1.1rem; }
.stApp .fx-h2 {
    font-family: var(--fx-serif);
    font-size: 1.65rem;
    font-weight: 600;
    line-height: 1.25;
    color: var(--fx-ink);
    margin: 0 0 0.3rem;
}
.fx-lede { color: var(--fx-muted); font-size: 0.95rem; line-height: 1.55; margin: 0; max-width: 56rem; }
.stApp .fx-h3 {
    font-family: var(--fx-serif);
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--fx-ink);
    margin: 1.6rem 0 0.4rem;
    padding-top: 1.2rem;
    border-top: 1px solid var(--fx-rule);
}
.fx-readout { color: var(--fx-muted); font-size: 0.9rem; margin: -0.2rem 0 0.6rem; }
.fx-readout strong { color: var(--fx-ink); font-weight: 600; font-variant-numeric: tabular-nums; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { gap: 1.75rem; }
.stTabs [data-baseweb="tab"] { padding: 0.75rem 0 0.65rem; }
.stTabs [data-baseweb="tab"] p { font-size: 0.95rem; font-weight: 500; color: var(--fx-muted); }
.stTabs [aria-selected="true"] p { color: var(--fx-ink); }

/* Phones and small tablets: pin the tab bar under the header so sections stay
   one tap away on long pages, and tighten it so more labels fit. The sticky
   element is the tab list's wrapper (the list alone sits in a box its own
   height, so it has nowhere to stick). 3.75rem is Streamlit's header height. */
@media (max-width: 768px) {
    .stTabs div:has(> [data-baseweb="tab-list"]) {
        position: sticky;
        top: 3.75rem;
        z-index: 1000;
        background: var(--fx-bg);
        box-shadow: 0 1px 0 var(--fx-rule),
                    0 10px 12px -10px light-dark(rgba(0, 0, 0, 0.18), rgba(0, 0, 0, 0.7));
    }
    .stTabs [data-baseweb="tab-list"] { gap: 1.15rem; }
    .stTabs [data-baseweb="tab"] p { font-size: 0.9rem; }
}

/* ── Metrics: a hairline above, no card ── */
div[data-testid="stMetric"] { border-top: 1px solid var(--fx-rule); padding-top: 0.65rem; }
/* Not uppercased: labels carry symbols like ρ that turn into look-alikes (Ρ = "P"). */
[data-testid="stMetricLabel"] p {
    font-size: 0.82rem;
    font-weight: 500;
    color: var(--fx-muted);
}
[data-testid="stMetricValue"] {
    font-size: 1.6rem;
    font-weight: 500;
    font-variant-numeric: tabular-nums;
}

/* ── Primary buttons: keep label contrast on the light dark-mode accent ── */
.stButton button[kind="primary"] { color: light-dark(#ffffff, #101418); }

/* ── Callouts: st.container(key="fx-callout-<tone>-n") ── */
[class*="st-key-fx-callout-"] {
    border-left: 3px solid var(--fx-accent);
    background: var(--fx-panel);
    border-radius: 0 4px 4px 0;
    padding: 0.7rem 1rem;
    gap: 0.3rem;
}
[class*="st-key-fx-callout-caution"] { border-left-color: var(--fx-caution); }
[class*="st-key-fx-callout-negative"] { border-left-color: var(--fx-negative); }
[class*="st-key-fx-callout-positive"] { border-left-color: var(--fx-positive); }
[class*="st-key-fx-callout-"] p { margin: 0; font-size: 0.92rem; line-height: 1.55; }

/* ── Chart value labels: Vega hard-codes fill="black" on text marks (axis text is
      themed). The charts are SVG, so CSS can repaint them in the theme ink. ── */
[data-testid="stVegaLiteChart"] g.mark-text.role-mark text { fill: var(--fx-ink); }

/* ── Map frame and figure plates ── */
.st-key-fx-map iframe { border: 1px solid var(--fx-rule); border-radius: 4px; }
[data-testid="stImage"] img { border: 1px solid var(--fx-rule); border-radius: 4px; }

/* ── Overview: headline figures. Cells carry their own top/left rules and the
      wrapper clips the outer ones, so the strip wraps cleanly at any width. ── */
.fx-figwrap {
    overflow: hidden;
    border-top: 1px solid var(--fx-rule);
    border-bottom: 1px solid var(--fx-rule);
    margin: 0.2rem 0 1.8rem;
}
.fx-figures {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    margin: -1px 0 0 calc(-1.2rem - 1px);
}
.fx-fig { padding: 1.05rem 1.2rem; border-top: 1px solid var(--fx-rule); border-left: 1px solid var(--fx-rule); }
.fx-fig-n {
    font-family: var(--fx-serif);
    font-size: 2rem;
    font-weight: 600;
    line-height: 1.1;
    white-space: nowrap;
    color: var(--fx-ink);
    font-variant-numeric: lining-nums tabular-nums;
}
.fx-fig-l { color: var(--fx-muted); font-size: 0.85rem; line-height: 1.4; margin-top: 0.35rem; }
.fx-prose { color: var(--fx-ink); font-size: 0.93rem; line-height: 1.65; }
.fx-prose p { margin: 0 0 0.8rem; }

/* ── Definition lists, legends, weight bars ── */
.fx-dl {
    display: grid;
    grid-template-columns: max-content 1fr;
    gap: 0.35rem 0.9rem;
    margin: 0 0 1.3rem;
    font-size: 0.85rem;
    line-height: 1.45;
}
.fx-dl dt { color: var(--fx-muted); }
.fx-dl dd { margin: 0; color: var(--fx-ink); }
.fx-side-title {
    font-family: var(--fx-serif);
    font-size: 1.08rem;
    font-weight: 600;
    line-height: 1.35;
    color: var(--fx-ink);
    margin-bottom: 1rem;
}
.fx-list { margin: 0 0 1.3rem; padding-left: 1.05rem; font-size: 0.85rem; line-height: 1.6; color: var(--fx-ink); }
.stApp table.fx-weights { width: 100%; border-collapse: collapse; font-size: 0.82rem; border: none; }
.stApp table.fx-weights td { padding: 0.2rem 0; border: none; background: none; }
.stApp .fx-weights td.n { color: var(--fx-ink); white-space: nowrap; padding-right: 0.7rem; }
.fx-weights td.b { width: 100%; }
.fx-weights .bar { height: 6px; background: var(--fx-accent); border-radius: 1px; }
.stApp .fx-weights td.v { text-align: right; padding-left: 0.6rem; color: var(--fx-muted); font-variant-numeric: tabular-nums; }
.stApp .fx-weights tr.total td { border-top: 1px solid var(--fx-rule); padding-top: 0.4rem; font-weight: 600; color: var(--fx-ink); }

.fx-legend-row {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.45rem 0;
    border-bottom: 1px solid var(--fx-rule);
    font-size: 0.88rem;
    color: var(--fx-ink);
}
.fx-legend-row:first-of-type { border-top: 1px solid var(--fx-rule); }
.fx-sw { width: 14px; height: 14px; border-radius: 2px; flex: none; }
.fx-legend-range { margin-left: auto; color: var(--fx-muted); font-size: 0.8rem; font-variant-numeric: tabular-nums; }
.fx-chips { display: flex; flex-wrap: wrap; gap: 0.4rem 1.1rem; font-size: 0.82rem; color: var(--fx-muted); margin: 0.5rem 0 1.2rem; }
.fx-chips span { display: inline-flex; align-items: center; gap: 0.4rem; }
.fx-chips i { width: 11px; height: 11px; border-radius: 2px; display: inline-block; }

/* ── Point-query result ── */
.fx-result {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem 0;
    margin: 0.8rem 0 1rem;
    border-top: 1px solid var(--fx-rule);
    border-bottom: 1px solid var(--fx-rule);
}
.fx-result-chip {
    width: 52px;
    height: 52px;
    flex: none;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: var(--fx-serif);
    font-size: 1.4rem;
    font-weight: 600;
}
.fx-result-title { font-family: var(--fx-serif); font-size: 1.4rem; font-weight: 600; color: var(--fx-ink); line-height: 1.2; }
.fx-result-meta { color: var(--fx-muted); font-size: 0.88rem; margin-top: 0.15rem; }

/* ── Climate figures ── */
.fx-fig-title { font-weight: 600; font-size: 0.95rem; color: var(--fx-ink); margin: 0.6rem 0 0.15rem; }
.fx-fig-desc { color: var(--fx-muted); font-size: 0.85rem; margin-bottom: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS & HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

# Zone colour scheme (index 0 = nodata/background)
ZONE_HEX = {0: "#00000000", 1: "#1a9850", 2: "#a6d96a", 3: "#fee08b",
            4: "#f46d43", 5: "#a50026"}
ZONE_RGBA = {
    0: (0, 0, 0, 0),
    1: (26, 152, 80, 160),
    2: (166, 217, 106, 160),
    3: (254, 224, 139, 175),
    4: (244, 109, 67, 185),
    5: (165, 0, 38, 200),
}
# Text colour that reads on each zone swatch
ZONE_INK = {1: "#ffffff", 2: "#1c1f23", 3: "#1c1f23", 4: "#1c1f23", 5: "#ffffff"}

# Mid-tones that read on both the light and the dark background
NEUTRAL_BAR = "#9aa1a8"
NEUTRAL_RULE = "#7d848b"
SERIES_REF = "#7d848b"     # observed / reference series
SERIES_MODEL = "#3a87c8"   # simulated / model series
SERIES_PEAK = "#c96a3d"

ESRI_ATTR = "Tiles &copy; Esri &mdash; Esri, HERE, Garmin, &copy; OpenStreetMap contributors"
ESRI_CANVAS = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/{}/MapServer/tile/{{z}}/{{y}}/{{x}}"
MAP_OUTLINE = {"light": "#33383e", "dark": "#d4d6d9"}

# Leaflet chrome inside the map iframe; .fx-dark is toggled by MapFollowsTheme.
MAP_CSS = """<style>
.leaflet-container { font-family: "IBM Plex Sans", "Segoe UI", sans-serif; }
/* Leaflet sizes the layer list while the tab is still hidden and adds a needless scrollbar */
.leaflet-control-layers-list { height: auto !important; }
.leaflet-control-layers-scrollbar { overflow-y: visible !important; padding-right: 6px !important; }
/* Phone-width map (the iframe's own width): keep the layer list from covering the map */
@media (max-width: 560px) {
    .leaflet-control-layers-expanded { padding: 4px 8px 4px 6px; font-size: 11px; line-height: 1.35; }
    .leaflet-control-layers-selector { margin-top: 1px; }
}
.leaflet-tooltip.fx-tip {
    background: #ffffff; color: #1c1f23; border: 1px solid #d5d1c7; border-radius: 3px;
    box-shadow: none; padding: 5px 9px; font-size: 13px;
}
.leaflet-tooltip.fx-tip:before { display: none; }
.fx-dark .leaflet-tooltip.fx-tip { background: #1f2225; color: #e3e1db; border-color: #34383c; }
.fx-dark .leaflet-control-layers, .fx-dark .leaflet-bar a {
    background: #1f2225; color: #e3e1db; border-color: #34383c;
}
.fx-dark .leaflet-control-layers-separator { border-top-color: #34383c; }
.fx-dark .leaflet-control-attribution { background: rgba(20, 22, 24, 0.8); color: #a0a5ab; }
.fx-dark .leaflet-control-attribution a { color: #86b6e0; }
.fx-dark .leaflet-control-scale-line { background: rgba(20, 22, 24, 0.7); color: #e3e1db; border-color: #a0a5ab; }
</style>"""


class MapFollowsTheme(MacroElement):
    """Keep the map in step with the app theme without a Streamlit rerun.

    The map runs in a same-origin component iframe, so it can read the
    color-scheme Streamlit sets on .stApp in the parent page. When that flips,
    swap the basemap and the LGA outline colour. A basemap the viewer picks by
    hand stays until the theme changes again.
    """
    _template = Template("""
        {% macro script(this, kwargs) %}
        (function () {
            var map = {{ this._parent.get_name() }};
            var light = {{ this.light.get_name() }}, dark = {{ this.dark.get_name() }};
            var outlines = {{ this.outlines.get_name() }};
            var current = null;
            function apply() {
                var app;
                try { app = window.parent.document.querySelector(".stApp"); } catch (e) { return; }
                if (!app) { return; }
                var isDark = window.parent.getComputedStyle(app).colorScheme === "dark";
                if (isDark === current) { return; }
                current = isDark;
                var on = isDark ? dark : light, off = isDark ? light : dark;
                if (map.hasLayer(off)) { map.removeLayer(off); }
                if (!map.hasLayer(on)) { map.addLayer(on); }
                on.bringToBack();
                outlines.setStyle({color: isDark ? {{ this.outline_dark }} : {{ this.outline_light }}});
                map.getContainer().classList.toggle("fx-dark", isDark);
            }
            apply();
            setInterval(apply, 800);
        })();
        {% endmacro %}
    """)

    def __init__(self, light, dark, outlines):
        super().__init__()
        self._name = "MapFollowsTheme"
        self.light, self.dark, self.outlines = light, dark, outlines
        self.outline_light = json.dumps(MAP_OUTLINE["light"])
        self.outline_dark = json.dumps(MAP_OUTLINE["dark"])

FACTOR_LABELS = {
    "elevation": "Elevation", "twi": "TWI", "dist_rivers": "Dist. to rivers",
    "flow_accum": "Flow accum.", "runoff": "Runoff", "slope": "Slope",
    "rainfall": "Rainfall", "lulc": "LULC",
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

SCENARIO_MODES = ["Percentage change", "NIMET return-period wet year"]
MONTHS = [calendar.month_abbr[m] for m in range(1, 13)]


def _fmt(val, unit="", decimals=1):
    """Format a numeric value safely (returns 'N/A' for None)."""
    if val is None:
        return "N/A"
    if isinstance(val, float):
        return f"{val:,.{decimals}f}{unit}"
    return str(val)


def _people(n):
    """Compact population figure: 6.91 M, 692 K, 312."""
    if n >= 1e6:
        return f"{n / 1e6:.2f} M"
    if n >= 1e3:
        return f"{n / 1e3:.0f} K"
    return f"{n:.0f}"


def _dark():
    return st.context.theme.type == "dark"


def section(title, lede=None):
    lede_html = f'<p class="fx-lede">{lede}</p>' if lede else ""
    st.markdown(
        f'<div class="fx-section"><div class="fx-h2" role="heading" aria-level="2">'
        f'{title}</div>{lede_html}</div>', unsafe_allow_html=True)


def subhead(title):
    st.markdown(f'<div class="fx-h3" role="heading" aria-level="3">{title}</div>',
                unsafe_allow_html=True)


def label(text):
    st.markdown(f'<div class="fx-label">{text}</div>', unsafe_allow_html=True)


_callout_ids = itertools.count()


def callout(md, tone="info"):
    """A note with a coloured left rule. tone: info, caution, negative, positive."""
    with st.container(key=f"fx-callout-{tone}-{next(_callout_ids)}"):
        st.markdown(md)


def zone_chips():
    chips = "".join(f'<span><i style="background:{ZONE_HEX[z]}"></i>{n}</span>'
                    for z, n in M.ZONE_NAMES.items())
    st.markdown(f'<div class="fx-chips">{chips}</div>', unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# CACHED DATA LOADERS
# ═══════════════════════════════════════════════════════════════════════════════

@st.cache_data(ttl=3600)
def get_hazard_overlay():
    """Read hazard zones TIF, clip to the 20 LGAs, colorize, and return base64 PNG + WGS84 bounds."""
    with rasterio.open(M._core("flood_hazard_zones.tif")) as ds:
        bounds = transform_bounds(ds.crs, "EPSG:4326", *ds.bounds)
        factor = 2
        out_shape = (ds.height // factor, ds.width // factor)
        zones = ds.read(1, out_shape=out_shape)
        # The raster has values across its whole bounding box (sea, Ogun State, Benin).
        # Exposure statistics count only cells inside the LGA polygons, so show the same footprint.
        transform = ds.transform * Affine.scale(ds.width / out_shape[1], ds.height / out_shape[0])
        lgas = M.lga_boundaries().to_crs(ds.crs)
        zones[geometry_mask(lgas.geometry, out_shape=out_shape, transform=transform)] = 0

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
def _outside_lgas(height, width, transform_gdal, crs_wkt):
    """Boolean mask, True outside the 20 LGA polygons, on a scenario raster's grid."""
    lgas = M.lga_boundaries().to_crs(crs_wkt)
    return geometry_mask(lgas.geometry, out_shape=(height, width),
                         transform=Affine.from_gdal(*transform_gdal))


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
# CHARTS (Altair, so axes and labels follow the active Streamlit theme)
# ═══════════════════════════════════════════════════════════════════════════════

def chart_lga_ranking(df, statewide_pct):
    """Horizontal bars of % population in High/Very High per LGA, most exposed first."""
    d = df[["lga_name", "pct_high_very_high"]].copy()
    d["above"] = d["pct_high_very_high"] >= statewide_pct
    xmax = float(d["pct_high_very_high"].max()) * 1.12
    base = alt.Chart(d).encode(
        y=alt.Y("lga_name:N", title=None,
                sort=list(d.sort_values("pct_high_very_high", ascending=False)["lga_name"]),
                axis=alt.Axis(labelLimit=200, ticks=False, domain=False, minExtent=118)),
        x=alt.X("pct_high_very_high:Q", title="Population in High / Very High zones (%)",
                scale=alt.Scale(domain=[0, xmax])),
    )
    bars = base.mark_bar(size=15, cornerRadiusEnd=2).encode(
        color=alt.when(alt.datum.above).then(alt.value(ZONE_HEX[4]))
                 .otherwise(alt.value(NEUTRAL_BAR)),
        tooltip=[alt.Tooltip("lga_name:N", title="LGA"),
                 alt.Tooltip("pct_high_very_high:Q", title="% High / Very High", format=".1f")],
    )
    values = base.mark_text(align="left", dx=4, fontSize=11).encode(
        text=alt.Text("pct_high_very_high:Q", format=".1f"))
    statewide = alt.Chart(pd.DataFrame({"v": [statewide_pct]})).mark_rule(
        strokeDash=[4, 3], color=NEUTRAL_RULE).encode(x="v:Q")
    return (bars + values + statewide).properties(height=24 * len(d))


def chart_zone_shares(baseline):
    """Share of the modelled population in each hazard zone."""
    total = baseline["total"]
    d = pd.DataFrame([{"zone": n, "order": z, "share": 100 * baseline.get(n, 0) / total,
                       "label": f"{_people(baseline.get(n, 0))}  ({100 * baseline.get(n, 0) / total:.1f}%)"}
                      for z, n in M.ZONE_NAMES.items()])
    base = alt.Chart(d).encode(
        y=alt.Y("zone:N", sort=list(M.ZONE_NAMES.values()), title=None,
                axis=alt.Axis(ticks=False, domain=False, minExtent=72)),
        x=alt.X("share:Q", title="Share of modelled population (%)",
                scale=alt.Scale(domain=[0, float(d["share"].max()) * 1.6])),
    )
    bars = base.mark_bar(size=18, cornerRadiusEnd=2).encode(
        color=alt.Color("zone:N", legend=None,
                        scale=alt.Scale(domain=list(M.ZONE_NAMES.values()),
                                        range=[ZONE_HEX[z] for z in M.ZONE_NAMES])),
        tooltip=[alt.Tooltip("zone:N", title="Zone"), alt.Tooltip("label:N", title="People")],
    )
    values = base.mark_text(align="left", dx=4, fontSize=11).encode(text="label:N")
    return (bars + values).properties(height=40 * len(d))


def chart_scenario_change(exp):
    """Per-zone % change in population vs the baseline, either side of zero."""
    d = pd.DataFrame([{"zone": n, "order": z, "pct": exp[n]["pct_change"],
                       "label": f"{exp[n]['pct_change']:+.2f}%"}
                      for z, n in M.ZONE_NAMES.items()])
    lim = max(abs(d["pct"]).max(), 0.05) * 1.6
    base = alt.Chart(d).encode(
        y=alt.Y("zone:N", sort=list(M.ZONE_NAMES.values()), title=None,
                axis=alt.Axis(ticks=False, domain=False, minExtent=72)),
        x=alt.X("pct:Q", title="Change in population vs baseline (%)",
                scale=alt.Scale(domain=[-lim, lim])),
    )
    bars = base.mark_bar(size=18).encode(
        color=alt.Color("zone:N", legend=None,
                        scale=alt.Scale(domain=list(M.ZONE_NAMES.values()),
                                        range=[ZONE_HEX[z] for z in M.ZONE_NAMES])),
        tooltip=[alt.Tooltip("zone:N", title="Zone"), alt.Tooltip("label:N", title="Change")],
    )
    pos = base.transform_filter(alt.datum.pct >= 0).mark_text(
        align="left", dx=4, fontSize=11).encode(text="label:N")
    neg = base.transform_filter(alt.datum.pct < 0).mark_text(
        align="right", dx=-4, fontSize=11).encode(text="label:N")
    zero = alt.Chart(pd.DataFrame({"v": [0]})).mark_rule(color=NEUTRAL_RULE).encode(x="v:Q")
    return (bars + pos + neg + zero).properties(height=40 * len(d))


def chart_monthly(series, y_title):
    """Lines over Jan–Dec in calendar order. series: {reference name: 12 values,
    model name: 12 values}; the first is drawn grey, the second blue."""
    d = pd.DataFrame([{"month": MONTHS[i], "series": name, "value": v}
                      for name, vals in series.items() for i, v in enumerate(vals)])
    return alt.Chart(d).mark_line(point=True, strokeWidth=2).encode(
        x=alt.X("month:N", sort=MONTHS, title=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y("value:Q", title=y_title),
        color=alt.Color("series:N", sort=list(series), title=None,
                        scale=alt.Scale(domain=list(series), range=[SERIES_REF, SERIES_MODEL]),
                        legend=alt.Legend(orient="top")),
        tooltip=[alt.Tooltip("month:N", title="Month"), alt.Tooltip("series:N", title="Series"),
                 alt.Tooltip("value:Q", title=y_title, format=",.1f")],
    ).properties(height=300)


def chart_swat_scenarios(sc):
    """Mean and peak-month outlet flow per rainfall scenario, side by side."""
    order = [s["label"] for s in sc]
    d = pd.DataFrame(sc)[["label", "mean", "peak"]].melt(
        id_vars="label", var_name="measure", value_name="flow")
    d["measure"] = d["measure"].map({"mean": "Mean flow", "peak": "Peak month"})
    return alt.Chart(d).mark_bar().encode(
        x=alt.X("label:N", sort=order, title=None, axis=alt.Axis(labelAngle=0)),
        xOffset=alt.XOffset("measure:N"),
        y=alt.Y("flow:Q", title="Outlet discharge (m³/s)"),
        color=alt.Color("measure:N", title=None, legend=alt.Legend(orient="top"),
                        scale=alt.Scale(domain=["Mean flow", "Peak month"],
                                        range=[SERIES_MODEL, SERIES_PEAK])),
        tooltip=[alt.Tooltip("label:N", title="Scenario"), alt.Tooltip("measure:N", title=" "),
                 alt.Tooltip("flow:Q", title="m³/s", format=",.0f")],
    ).properties(height=280)


def scenario_zones_image(zones, ref):
    """Scenario zones clipped to the LGAs, cropped to them, on a transparent ground."""
    outside = _outside_lgas(ref["height"], ref["width"],
                            ref["transform"].to_gdal(), ref["crs"].to_wkt())
    z = zones.copy()
    z[outside] = 0
    rows = np.where(~outside.all(axis=1))[0]
    cols = np.where(~outside.all(axis=0))[0]
    z = z[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1][::2, ::2]
    rgba = np.zeros((*z.shape, 4), dtype=np.uint8)
    for k in M.ZONE_NAMES:
        r, g, b = (int(ZONE_HEX[k][i:i + 2], 16) for i in (1, 3, 5))
        rgba[z == k] = (r, g, b, 255)
    return Image.fromarray(rgba)


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
# MASTHEAD & DISCLAIMER
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="fx-masthead">
    <div class="fx-overline">University of Lagos &nbsp;·&nbsp; Department of Civil &amp; Environmental Engineering</div>
    <div class="fx-title" role="heading" aria-level="1">Lagos Flood Hazard Explorer</div>
    <p class="fx-sub">Interactive decision-support tool for flood hazard, population exposure
       and rainfall scenarios across the 20 Local Government Areas of Lagos State.</p>
    <div class="fx-disclaimer">
        This is a <strong>hazard &amp; exposure decision-support tool</strong>, <em>not</em> a
        dated flood forecast. It shows where flooding is likely and models what-if rainfall scenarios.
    </div>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    _wmax = max(M.WEIGHTS.values())
    _rows = "".join(
        f'<tr><td class="n">{FACTOR_LABELS.get(k, k)}</td>'
        f'<td class="b"><div class="bar" style="width:{100 * w / _wmax:.0f}%"></div></td>'
        f'<td class="v">{w:.2f}</td></tr>'
        for k, w in M.WEIGHTS.items())
    st.markdown(f"""
    <div class="fx-label">Final year project</div>
    <div class="fx-side-title">Flood Risk Analysis and Visualization Web Portal for
        Lagos State, Nigeria</div>
    <dl class="fx-dl">
        <dt>Student</dt><dd>Attah Gbubemi David (190402060)</dd>
        <dt>Supervisor</dt><dd>Dr O. C. Echeta</dd>
        <dt>Institution</dt><dd>Department of Civil &amp; Environmental Engineering,
            University of Lagos</dd>
    </dl>
    <div class="fx-label">Models</div>
    <ul class="fx-list">
        <li>AHP multi-criteria index (8 factors)</li>
        <li>Gumbel EV-I return periods</li>
        <li>SCS-CN runoff recomputation</li>
        <li>SWAT+ Ogun streamflow (calibrated)</li>
    </ul>
    <div class="fx-label">AHP factor weights</div>
    <table class="fx-weights">
        {_rows}
        <tr class="total"><td class="n">Total</td><td></td>
            <td class="v">{sum(M.WEIGHTS.values()):.2f}</td></tr>
    </table>
    """, unsafe_allow_html=True)
    st.caption("Light or dark theme: open the ⋮ menu at the top right.")


# ═══════════════════════════════════════════════════════════════════════════════
# TABS
# ═══════════════════════════════════════════════════════════════════════════════

(tab_overview, tab_map, tab_query, tab_exposure, tab_scenario, tab_climate,
 tab_hydro, tab_valid) = st.tabs([
    "Overview",
    "Hazard map",
    "Point query",
    "Exposure",
    "Scenario",
    "Climate",
    "Hydrology (SWAT+)",
    "Validation",
])

# ─────────────────────── TAB 1 — PROJECT OVERVIEW ────────────────────────────
with tab_overview:
    section("Flood Risk Analysis and Visualization Web Portal",
            "Lagos State, Nigeria · Final year project")

    # Derived from real_baseline_exposure() rather than hardcoded, so these
    # figures cannot drift from the Exposure tab or from the thesis. The
    # denominator is the WorldPop total inside the LGA boundaries (12.42 M), NOT
    # a metro-wide population estimate — mixing the two previously produced
    # 22.8% here against 38.7% in the Exposure tab and in the report.
    _b = get_baseline()
    _hv_m = _b["High+VeryHigh"] / 1e6
    _hv_pct = 100 * _b["High+VeryHigh"] / _b["total"]
    _tot_m = _b["total"] / 1e6
    _topo = 100 * (M.WEIGHTS["elevation"] + M.WEIGHTS["twi"])
    _rain = 100 * (M.WEIGHTS["runoff"] + M.WEIGHTS["rainfall"])

    st.markdown(f"""
    <div class="fx-figwrap"><div class="fx-figures">
        <div class="fx-fig"><div class="fx-fig-n">{_hv_m:.2f} M</div>
            <div class="fx-fig-l">people live in High or Very High hazard zones</div></div>
        <div class="fx-fig"><div class="fx-fig-n">{_hv_pct:.1f}%</div>
            <div class="fx-fig-l">of the {_tot_m:.2f} M residents in the WorldPop analysis grid</div></div>
        <div class="fx-fig"><div class="fx-fig-n">{_topo:.0f}%</div>
            <div class="fx-fig-l">of the hazard index weight is topography (elevation + TWI)</div></div>
        <div class="fx-fig"><div class="fx-fig-n">+0.44 °C</div>
            <div class="fx-fig-l">warming per decade at Ikeja, 1996–2025 (significant trend)</div></div>
    </div></div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3, gap="large")

    with c1:
        st.markdown("""
        <div class="fx-label">Problem statement</div>
        <div class="fx-prose"><p>
            Lagos State, with over <strong>20 million residents</strong> in a low-lying
            coastal setting, faces recurring and devastating flooding. Rapid urbanization,
            inadequate drainage infrastructure, and increasingly variable rainfall
            amplify the risk. This project develops a <em>spatial decision-support
            framework</em> to quantify and visualize flood hazard and population exposure
            across all 20 Local Government Areas.
        </p></div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("""
        <div class="fx-label">Methodology</div>
        <div class="fx-prose">
            <p><strong>AHP Weighted Overlay</strong> of 8 conditioning factors — elevation,
            TWI, proximity to rivers, flow accumulation, SCS-CN runoff depth, slope,
            extreme rainfall, and land-use — to produce a continuous <em>Flood Hazard
            Index (0–1)</em> classified into 5 zones.</p>
            <p><strong>Gumbel EV-I</strong> model fitted to 30 years of NIMET rainfall
            to estimate design annual rainfall for 2–100 year return periods.</p>
            <p><strong>WorldPop 2020</strong> grid for population exposure analysis.</p>
        </div>
        """, unsafe_allow_html=True)

    with c3:
        st.markdown(f"""
        <div class="fx-label">Key findings</div>
        <div class="fx-prose">
            <p><strong>~{_hv_m:.2f} million people</strong> reside in High or Very High hazard
            zones — <strong>{_hv_pct:.1f}%</strong> of the {_tot_m:.2f} million residents
            captured in the WorldPop analysis grid.</p>
            <p>Flood hazard is <strong>topography-dominated</strong>: elevation + TWI account
            for {_topo:.0f}% of the index weight. Rainfall factors contribute {_rain:.0f}%, meaning
            rainfall scenario effects are intentionally modest — the map is structurally realistic.</p>
            <p>Annual mean temperature shows a <strong>statistically significant increasing
            trend</strong> (+0.44°C/decade), while annual rainfall shows no significant
            long-term trend.</p>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("Data sources & limitations", expanded=False):
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
    section("Baseline flood hazard zones",
            "AHP-weighted overlay of 8 conditioning factors. Hover or tap an LGA for its name; "
            "use the layer control (top right of the map) to switch basemap or toggle overlays.")

    map_col, legend_col = st.columns([4, 1], gap="large")

    with map_col:
        b64_img, bounds = get_hazard_overlay()
        lga_json = get_lga_json()
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2
        dark = _dark()

        m = folium.Map(
            location=[center_lat, center_lon],
            zoom_start=10,
            tiles=None,
            control_scale=True,
        )
        # CARTO's free basemaps now return an "API KEY REQUIRED" tile; Esri's canvases need no key.
        # Both are offered; the one matching the app theme opens first, and
        # MapFollowsTheme swaps them in the browser when the viewer switches theme.
        light_tiles, dark_tiles = (
            folium.TileLayer(ESRI_CANVAS.format(canvas), attr=ESRI_ATTR, name=name,
                             max_zoom=16, show=show).add_to(m)
            for name, canvas, show in (("Light basemap (Esri)", "World_Light_Gray_Base", not dark),
                                       ("Dark basemap (Esri)", "World_Dark_Gray_Base", dark)))

        folium.raster_layers.ImageOverlay(
            image=f"data:image/png;base64,{b64_img}",
            bounds=[[bounds[1], bounds[0]], [bounds[3], bounds[2]]],
            opacity=0.75,
            name="Flood hazard zones",
        ).add_to(m)

        line = MAP_OUTLINE["dark" if dark else "light"]
        outlines = folium.GeoJson(
            lga_json,
            name="LGA boundaries",
            style_function=lambda x: {
                "fillColor": "transparent",
                "color": line,
                "weight": 1.2,
                "opacity": 0.85,
            },
            tooltip=folium.GeoJsonTooltip(fields=["NAME_2"], aliases=["LGA:"],
                                          class_name="fx-tip"),
        ).add_to(m)

        folium.LayerControl(collapsed=False).add_to(m)
        m.get_root().header.add_child(folium.Element(MAP_CSS), name="fx-map-css")
        MapFollowsTheme(light_tiles, dark_tiles, outlines).add_to(m)

        with st.container(key="fx-map"):
            st_folium(m, width=None, height=600, returned_objects=[])

    with legend_col:
        rows = "".join(
            f'<div class="fx-legend-row"><span class="fx-sw" style="background:{ZONE_HEX[z]}"></span>'
            f'{M.ZONE_NAMES[z]}<span class="fx-legend-range">'
            f'{M.ZONE_BREAKS[z - 1]:.2f}–{min(M.ZONE_BREAKS[z], 1.0):.2f}</span></div>'
            for z in range(1, 6))
        st.markdown(f"""
        <div class="fx-label">Hazard zone</div>
        <div style="margin-bottom:1.6rem;">{rows}</div>
        <div class="fx-label">Map details</div>
        <dl class="fx-dl">
            <dt>CRS</dt><dd>EPSG:32631 (UTM 31N)</dd>
            <dt>Classes</dt><dd>Equal interval</dd>
            <dt>Basemap</dt><dd>Esri Gray Canvas</dd>
            <dt>LGAs</dt><dd>GADM</dd>
        </dl>
        """, unsafe_allow_html=True)


# ─────────────────────── TAB 3 — POINT QUERY ─────────────────────────────────
with tab_query:
    section("Location hazard inspector",
            "Enter coordinates (WGS84) or pick a preset to query all model layers at that point.")

    label("Quick presets")
    selected_preset = None
    with st.container(horizontal=True, gap="small"):
        for i, (name, (plat, plon)) in enumerate(PRESET_LOCATIONS.items()):
            if st.button(name, key=f"preset_{i}"):
                selected_preset = (plat, plon, name)
                # Show the preset in the inputs below (they are keyed, so their
                # value= default only applies on first render).
                st.session_state["query_lat"] = plat
                st.session_state["query_lon"] = plon

    q_c1, q_c2, q_c3 = st.columns([1, 1, 1], vertical_alignment="bottom")
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
        run_query = st.button("Query location", type="primary", width="stretch",
                              key="run_query")

    if run_query or selected_preset:
        query_lat = selected_preset[0] if selected_preset else lat
        query_lon = selected_preset[1] if selected_preset else lon

        with st.spinner("Sampling model layers..."):
            r = M.point_query(query_lat, query_lon)

        if r.get("hazard_zone") is not None:
            zone_idx = r["hazard_zone"]
            zone_name = r.get("hazard_zone_name", "Unknown")
            zone_color = ZONE_HEX.get(zone_idx, NEUTRAL_BAR)
            zone_ink = ZONE_INK.get(zone_idx, "#ffffff")

            loc_label = selected_preset[2] if selected_preset else f"{query_lat:.4f}°N, {query_lon:.4f}°E"
            lga_part = f" &nbsp;·&nbsp; LGA: {r.get('lga')}" if r.get("lga") else ""
            st.markdown(f"""
            <div class="fx-result">
                <div class="fx-result-chip" style="background:{zone_color}; color:{zone_ink};">{zone_idx}</div>
                <div>
                    <div class="fx-result-title">{zone_name} hazard zone</div>
                    <div class="fx-result-meta">{loc_label}{lga_part}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Hazard index", _fmt(r.get("flood_hazard_index"), decimals=3))
            m2.metric("Elevation", _fmt(r.get("elevation_m"), " m"))
            m3.metric("Slope", _fmt(r.get("slope_deg"), "°"))
            m4.metric("TWI", _fmt(r.get("twi"), decimals=2))
            m5, m6, m7, _ = st.columns(4)
            m5.metric("Dist. to river", _fmt(r.get("distance_to_rivers_m"), " m", decimals=0))
            m6.metric("Runoff depth", _fmt(r.get("runoff_depth_mm"), " mm", decimals=1))
            m7.metric("Local Government Area", r.get("lga") or "N/A")

            with st.expander("Raw JSON response"):
                st.json(r)

        else:
            callout("This location falls outside the Lagos model extent or returned no data. "
                    "Try coordinates within Lagos State (Lat ≈ 6.4–6.7°N, Lon ≈ 2.7–4.4°E).",
                    tone="caution")


# ─────────────────────── TAB 4 — EXPOSURE DASHBOARD ──────────────────────────
with tab_exposure:
    section("Population exposure",
            "Baseline population exposure to flood hazard across all 20 Local Government Areas. "
            "Data source: WorldPop 2020 gridded population.")

    baseline = get_baseline()
    df_lga = get_exposure_lga().sort_values("pct_high_very_high", ascending=False)
    statewide_pct = 100 * baseline.get("High+VeryHigh", 0) / max(baseline.get("total", 1), 1)

    met1, met2, met3, met4 = st.columns(4)
    met1.metric("Total population (model)", f"{baseline.get('total', 0):,.0f}")
    met2.metric("High + Very High zones", f"{baseline.get('High+VeryHigh', 0):,.0f}")
    met3.metric("% in High / Very High", f"{statewide_pct:.1f}%")
    met4.metric("Most exposed LGA",
                df_lga.iloc[0]["lga_name"] if not df_lga.empty else "N/A",
                f"{df_lga.iloc[0]['pct_high_very_high']:.1f}% exposed" if not df_lga.empty else None,
                delta_color="off", delta_arrow="off")

    chart_col, zone_col = st.columns([3, 2], gap="large")

    with chart_col:
        subhead("LGA exposure ranking")
        st.altair_chart(chart_lga_ranking(df_lga, statewide_pct), width="stretch")
        st.caption(f"Dashed line: statewide share ({statewide_pct:.1f}%). "
                   "Orange bars are LGAs above it.")

    with zone_col:
        subhead("Population by hazard zone")
        st.altair_chart(chart_zone_shares(baseline), width="stretch")

    with st.expander("Full LGA exposure table", expanded=False):
        st.dataframe(df_lga, width="stretch", hide_index=True)

    csv_bytes = df_lga.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download exposure data (CSV)", csv_bytes,
        file_name="lagos_exposure_by_lga.csv", mime="text/csv",
        icon=":material/download:",
    )


# ─────────────────────── TAB 5 — SCENARIO SIMULATOR ──────────────────────────
with tab_scenario:
    section("Rainfall what-if scenario",
            "Adjust rainfall intensity and recompute the flood hazard map and population exposure "
            "in real time. Requires the <code>models/factors/</code> folder (~284 MB).")

    factors_available = os.path.isdir(M.FACT) and os.path.exists(
        os.path.join(M.FACT, "dem.tif"))

    if not factors_available:
        callout("The `models/factors/` directory is missing or incomplete. "
                "The scenario simulator requires the full factor rasters (~284 MB). "
                "Copy the `factors/` folder into `models/` and restart.", tone="negative")
    else:
        mode = st.radio("Scenario input", SCENARIO_MODES, horizontal=True, key="scenario_mode")

        ctl, _ = st.columns([3, 2])
        with ctl:
            if mode == SCENARIO_MODES[0]:
                pct = st.slider("Rainfall change (%)", min_value=-50, max_value=100,
                                value=30, step=5, key="rain_pct")
                scale = 1 + pct / 100
                st.markdown(f"""
                <div class="fx-readout">
                    Rainfall multiplier <strong>×{scale:.2f}</strong>
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
                <div class="fx-readout">
                    {T}-year design rainfall ≈ <strong>{design:,.0f} mm</strong>
                    → ×{scale:.2f} of the 1,822 mm annual mean
                </div>
                """, unsafe_allow_html=True)

            run = st.button("Run scenario", type="primary", key="run_scenario",
                            icon=":material/play_arrow:")

        if run:
            baseline_exp = get_baseline()

            with st.spinner("Recomputing hazard index + exposure (first run may take a moment)..."):
                exp, zones = M.scenario_exposure(scale)
                _, _, ref = M.recompute_hazard(scale)

            hv = exp["High+VeryHigh"]

            subhead(f"Result — rainfall ×{scale:.2f}")
            r1, r2, r3 = st.columns(3)
            # More people in High/Very High is the bad direction, so an increase shows red.
            r1.metric("High + Very High (projected)",
                      f"{hv['people']:,.0f}",
                      f"{hv['delta']:+,.0f} people", delta_color="inverse")
            r2.metric("Change (%)", f"{hv['pct_change']:+.2f}%")
            r3.metric("Rainfall scale", f"×{scale:.2f}")

            # Lagos is a ~5:1 strip, so the map gets the full width to be legible.
            label("Recomputed hazard zones")
            st.image(scenario_zones_image(zones, ref), width="stretch")
            zone_chips()

            chart_c, table_c = st.columns(2, gap="large")

            with chart_c:
                label("Change by zone")
                st.altair_chart(chart_scenario_change(exp), width="stretch")

            with table_c:
                label("People per zone")
                st.dataframe(
                    pd.DataFrame([{
                        "Zone": n,
                        "Baseline": round(baseline_exp.get(n, 0)),
                        "Scenario": round(exp[n]["people"]),
                        "Change": round(exp[n]["delta"]),
                    } for n in M.ZONE_NAMES.values()]),
                    width="stretch", hide_index=True,
                    column_config={c: st.column_config.NumberColumn(format="localized")
                                   for c in ("Baseline", "Scenario", "Change")},
                )

            callout("Absolute numbers are anchored to the validated baseline; the scenario applies "
                    "the model's relative zone shift. Rainfall drives 0.20 of the 1.0 index weight, "
                    "so effects are modest — Lagos hazard is topography-dominated.")

            dl1, dl2, _ = st.columns([1, 1, 1])

            with dl1:
                st.download_button(
                    "Scenario exposure (CSV)",
                    _exposure_csv(exp),
                    file_name=f"scenario_exposure_x{scale:.2f}.csv",
                    mime="text/csv", icon=":material/download:", width="stretch",
                )

            with dl2:
                tiff_bytes = _zones_geotiff(zones, ref)
                st.download_button(
                    "Scenario zones (GeoTIFF)",
                    tiff_bytes,
                    file_name=f"scenario_zones_x{scale:.2f}.tif",
                    mime="image/tiff", icon=":material/download:", width="stretch",
                )


# ─────────────────────── TAB 6 — CLIMATE CENTER ──────────────────────────────
with tab_climate:
    section("Climate analysis & trends",
            "30-year analysis of NiMet Ikeja station data (1996–2025): rainfall trends, "
            "temperature, humidity, and Gumbel return-period estimates.")

    calc1, calc2 = st.columns(2, gap="large")

    with calc1:
        label("Return period → design rainfall")
        T_input = st.number_input("Return period (years)", min_value=2,
                                  max_value=1000, value=100, step=1,
                                  key="calc_T")
        dr = M.design_rainfall(T_input)
        st.metric("Design rainfall", f"{dr:,.0f} mm")

    with calc2:
        label("Observed rainfall → return period")
        rain_input = st.number_input("Annual rainfall (mm)", min_value=500,
                                     max_value=6000, value=3932, step=50,
                                     key="calc_rain")
        rp = M.return_period(rain_input)
        rp_label = f"{rp:,.0f} years" if rp < 10000 else "> 10,000 years"
        st.metric("Return period", rp_label)

    subhead("NIMET climate charts")

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
        cols = st.columns(2, gap="large")
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(chart_files):
                fname, title, desc = chart_files[idx]
                fpath = M._core(fname)
                with col:
                    if os.path.exists(fpath):
                        st.markdown(f"""
                        <div class="fx-fig-title">Figure {idx + 1}. {title}</div>
                        <div class="fx-fig-desc">{desc}</div>
                        """, unsafe_allow_html=True)
                        st.image(fpath, width="stretch")
                    else:
                        st.caption(f"Chart not found: {fname}")

    st.write("")
    with st.expander("Monthly climatology table", expanded=False):
        clim = get_climatology()
        st.dataframe(clim, width="stretch", hide_index=True)

    csv_clim = get_climatology().to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download climatology data (CSV)", csv_clim,
        file_name="nimet_climatology_1996_2025.csv", mime="text/csv",
        icon=":material/download:",
    )

# ─────────────────────── TAB 7 — SWAT+ HYDROLOGY ─────────────────────────────
with tab_hydro:
    section("Ogun River hydrology — SWAT+ model",
            "A <strong>calibrated, process-based SWAT+ model</strong> of the <strong>Ogun River "
            "catchment</strong> (~19,915 km²), the largest fluvial input to the Lagos Lagoon. Where "
            "the statewide hazard map is a multi-criteria <em>susceptibility</em> index, this "
            "simulates the actual <strong>rainfall → runoff → streamflow</strong> process, day by "
            "day, across 23 subbasins.")
    if not M.swat_available():
        st.caption("SWAT+ results not bundled. Build the model per `swat/METHODOLOGY_LOG.md`.")
    else:
        cal = M.swat_calibration()
        subhead("Calibration performance")
        c1, c2, c3 = st.columns(3)
        # Three decimals, not two: NSE clears its threshold by 0.007 and R² by
        # 0.006. Rounding to 0.51 / 0.61 hides how narrow that is, and the report
        # states the margins explicitly.
        c1.metric("NSE", f"{cal['nse']:.3f}", "target ≥ 0.50", delta_color="off", delta_arrow="off")
        c2.metric("R²", f"{cal['r2']:.3f}", "target ≥ 0.60", delta_color="off", delta_arrow="off")
        c3.metric("PBIAS", f"{cal['pbias']:+.1f}%", "target ±25%", delta_color="off", delta_arrow="off")
        st.caption(
            f"Monthly discharge vs GEOGLOWS at the Ogun outlet ({cal['period']}). "
            f"Independent validation 2018–2023: NSE {cal['validation_2018_2023']['nse']:.2f}, "
            f"R² {cal['validation_2018_2023']['r2']:.2f} — validation ≥ calibration, so the "
            "model generalises rather than overfitting."
        )

        subhead("Monthly discharge — observed vs simulated")
        _hy = M.swat_hydrograph()
        st.altair_chart(chart_monthly({
            "Observed (GEOGLOWS)": [h["obs"] for h in _hy],
            "Simulated (SWAT+)": [h["sim"] for h in _hy],
        }, "Discharge (m³/s)"), width="stretch")
        st.caption("Mean monthly outlet discharge (m³/s). The Sept–Oct peak matches the Lagos flood season.")

        subhead("Rainfall scenarios (process-based)")
        _sc = M.swat_scenarios()
        _dfs = pd.DataFrame(_sc)
        st.dataframe(
            _dfs.rename(columns={"label": "Scenario", "mean": "Mean flow (m³/s)",
                                 "peak": "Peak month (m³/s)", "d_mean": "Δ mean %",
                                 "d_peak": "Δ peak %"})[
                ["Scenario", "Mean flow (m³/s)", "Peak month (m³/s)", "Δ mean %", "Δ peak %"]],
            width="stretch", hide_index=True,
        )
        st.altair_chart(chart_swat_scenarios(_sc), width="stretch")
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
        callout(_s["note_2022"], tone="caution")
        st.caption(
            "Calibrated against GEOGLOWS modelled discharge (a recognised data-scarce approach). "
            "Oyan Dam regulation is not modelled — a documented limitation. "
            "Full build & calibration trail: `swat/METHODOLOGY_LOG.md`."
        )


# ─────────────────────── TAB 8 — INDEPENDENT VALIDATION ──────────────────────
with tab_valid:
    section("Independent validation",
            "Checks the model was <strong>not</strong> tuned to. The SWAT+ parameters were fitted to "
            "discharge alone and the AHP map was built from expert weights, so everything "
            "below is an out-of-sample test. Results are mixed — they are reported as found.")

    if not M.validation_available():
        st.caption("Validation results not bundled. Run `validation/build_validation_bundle.py`.")
    else:
        _v = M.validation_summary()
        _et = M.et_validation()
        _sp = M.spatial_validation()
        _a = _sp["test_a_pixel_level"]
        _b = _sp["test_b_lga_level"]

        # ── 1. ET check ──────────────────────────────────────────────────────
        subhead("1 · Evapotranspiration — a second variable, never calibrated to")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Monthly NSE", f"{_et['monthly']['nse']:.2f}")
        c2.metric("Monthly R²", f"{_et['monthly']['r2']:.2f}")
        c3.metric("PBIAS", f"{_et['monthly']['pbias']:+.1f}%",
                  help="Within the ±25% Moriasi band")
        c4.metric("Annual ET", f"{_et['annual_mm']['swat']:.0f} mm",
                  delta=f"{_et['annual_mm']['swat'] - _et['annual_mm']['reference']:+.0f} vs ref",
                  delta_color="off")

        _c = _et["climatology"]
        st.altair_chart(chart_monthly({
            "Reference ET": _c["ref_mm"],
            "SWAT+ simulated ET": _c["sim_mm"],
        }, "ET (mm/month)"), width="stretch")
        st.markdown(
            f"**Verdict — {_v['honest_status']['et_independent_check']}**"
        )
        _alt = M.et_validation_corroborating()
        if _alt:
            callout(
                "**Two independent references agree.** MODIS MOD16 "
                f"({_et['annual_mm']['reference']:.0f} mm/yr) and TerraClimate "
                f"({_alt['annual_mm']['reference']:.0f} mm/yr) were tested separately "
                "and show the same damped seasonal cycle. The finding is robust, not "
                "an artefact of one product.", tone="positive")
        st.caption(
            f"Primary reference: {_et['reference_product']} — a true satellite ET "
            "retrieval, the product specified for this validation. Regenerate with "
            "`swat/validation/fetch_mod16_et_gee.js`, then "
            "`et_validation.py --reference <csv>`."
        )

        # ── 2. Calibration trade-off ─────────────────────────────────────────
        subhead("2 · Why the parameters were not re-tuned to ET")
        _t = M.calibration_tradeoff()
        st.dataframe(
            pd.DataFrame([{
                "petco": r["petco"],
                "Discharge NSE": r["discharge"]["nse"],
                "Discharge R²": r["discharge"]["r2"],
                "Discharge PBIAS %": r["discharge"]["pbias"],
                "ET NSE": r["et"]["nse"],
                "ET PBIAS %": r["et"]["pbias"],
                "Meets thresholds": "Yes" if r["discharge_passes"] else "No",
            } for r in _t["runs"]]),
            width="stretch", hide_index=True,
        )
        callout(_t["diagnosis"])

        # ── 3. Hazard map vs observed floods ─────────────────────────────────
        subhead("3 · Hazard map vs observed floods")
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
            width="stretch", hide_index=True,
        )
        st.markdown(
            "Enrichment climbs monotonically across the zones — the map **ranks** "
            "flood risk in the right order. Discrimination is modest, not strong."
        )

        # ── 4. The negative result ───────────────────────────────────────────
        subhead("4 · LGA-level check — an inconclusive result")
        c1, c2, c3 = st.columns(3)
        c1.metric("ρ vs modelled exposure", f"{_b['spearman_rho']:+.2f}")
        c2.metric("ρ vs absolute exposed", f"{_b['spearman_rho_vs_absolute_exposed']:+.2f}")
        c3.metric("ρ vs raw population", f"{_b['spearman_rho_vs_population']:+.2f}")
        callout(
            "NEMA flood-report counts track **raw population** far better than "
            "modelled exposure. Reporting effort — not flood hazard — dominates this "
            "dataset, so it cannot validate the map. Reported as a null result.", tone="caution")
        st.dataframe(
            pd.DataFrame(_b["per_lga"]).rename(columns={
                "lga": "LGA", "nema_reports": "NEMA reports",
                "model_pct_high_vh": "Model % High+V.High",
                "population": "Population",
                "model_people_high_vh": "People exposed",
            }),
            width="stretch", hide_index=True, height=320,
        )

        callout("**Not claimed:** " + _v["honest_status"]["not_claimed"], tone="negative")
        st.caption(
            "Sources: MODIS 250 m flood extent Jul–Nov 2012 (NASA/DFO via HDX); "
            "NEMA 2022 Lagos flood records (62 reports, via HDX). "
            "Method and caveats: `validation/spatial_validation.py`."
        )


# ═══════════════════════════════════════════════════════════════════════════════
# TAB SWITCH SCROLL
# ═══════════════════════════════════════════════════════════════════════════════
# With the tab bar pinned (phones), switching tabs while scrolled down would open
# the new tab part-way through its content. Bring its top back under the bar.
st.html("""
<script>
(() => {
    if (window.__fxTabScroll) { return; }
    window.__fxTabScroll = true;
    document.addEventListener("click", (event) => {
        const tab = event.target.closest('.stTabs [data-baseweb="tab"]');
        if (!tab) { return; }
        requestAnimationFrame(() => {
            const tabs = tab.closest(".stTabs");
            const main = document.querySelector('[data-testid="stMain"]');
            const header = document.querySelector('header[data-testid="stHeader"]');
            if (!tabs || !main) { return; }
            const headerHeight = header ? header.getBoundingClientRect().height : 0;
            const offset = tabs.getBoundingClientRect().top - headerHeight;
            if (offset < 0) { main.scrollBy({top: offset}); }
        });
    });
})();
</script>
""", unsafe_allow_javascript=True)
