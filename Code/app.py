import base64
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

CSV = Path(__file__).resolve().parent.parent / "Database" / "snd.csv"
REPO_PATH = "Database/snd.csv"

BG, TEXT, DIM, GRID = "#ffffff", "#1f2430", "#6b7280", "#e4e7ec"
ACCENT, NAVY, NAVY_2, GOLD = "#596275", "#1b2b5a", "#24386e", "#c9a25a"
BAR = "#4f74a8"

st.set_page_config(page_title="Epiphany SnD", layout="wide", initial_sidebar_state="expanded")
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600&family=Manrope:wght@300;400;500;600;700&display=swap');
html, body, .stApp, .stMarkdown, button, input, label, [data-baseweb] {{ font-family: 'Manrope', sans-serif !important; }}
.stApp {{ background-color: {BG}; background-image: radial-gradient(#e6e9ee 1px, transparent 1px); background-size: 18px 18px; }}
[data-testid="stSidebar"] {{ background: #eceef2; border-right: 1px solid #d9dce3; }}
[data-testid="stSidebar"] label p {{ font-size: .7rem; letter-spacing: .14em; text-transform: uppercase; color: {DIM}; }}
.block-container {{ padding-top: 3.6rem; max-width: 1600px; }}
.app {{ font-family: 'Cormorant Garamond', serif; font-size: 1.05rem; color: {NAVY}; letter-spacing: .04em; border-bottom: 1px solid #d9dce3; padding-bottom: .6rem; margin-bottom: 1rem; }}
.brand {{ font-family: 'Cormorant Garamond', serif; font-size: 2.1rem; color: {ACCENT}; line-height: 1; }}
.brand-s {{ font-size: .68rem; letter-spacing: .3em; text-transform: uppercase; color: {DIM}; margin: .35rem 0 1.2rem; }}
.title {{ font-family: 'Cormorant Garamond', serif; font-size: 2.6rem; color: {TEXT}; line-height: 1.05; }}
.title b {{ color: {NAVY}; font-weight: 600; }}
.chips {{ margin: .7rem 0 1.6rem; }}
.chip {{ display: inline-block; border: 1px solid {GRID}; border-radius: 999px; padding: .15rem .7rem; margin: 0 .4rem .3rem 0;
        font-size: .72rem; color: {DIM}; letter-spacing: .06em; background: #fff; }}
.chip.on {{ background: {NAVY}; border-color: {NAVY}; color: #fff; }}
.chip.bad {{ background: #c62828; border-color: #c62828; color: #fff; }}
.chip.good {{ background: #2e7d32; border-color: #2e7d32; color: #fff; }}
.h {{ font-family: 'Cormorant Garamond', serif; font-size: 1.45rem; color: {TEXT}; margin: .6rem 0 .1rem; }}
.h::after {{ content: ""; display: block; width: 28px; height: 1px; background: {ACCENT}; margin-top: .3rem; margin-bottom: .4rem; }}
[data-testid="stPlotlyChart"] {{ background: #fff; border: 1px solid {GRID}; border-radius: 16px; overflow: hidden !important;
    transition: box-shadow .35s, transform .35s; }}
[data-testid="stPlotlyChart"]:hover {{ transform: translateY(-3px); box-shadow: 0 18px 40px -18px rgba(31,36,48,.28); }}
.tw {{ overflow-x: auto; margin-bottom: 1.2rem; border: 1px solid #d9dce3; border-radius: 14px; background: #fff; }}
.cap {{ padding: .8rem 1.1rem; font-size: .95rem; font-weight: 700; letter-spacing: .18em; color: {NAVY}; background: #f3f5f9; }}
.cap span {{ font-weight: 400; letter-spacing: .04em; color: {DIM}; font-size: .8rem; margin-left: .8rem; }}
table.snd {{ border-collapse: collapse; font-variant-numeric: tabular-nums; font-size: .86rem; width: 100%; }}
table.snd th {{ background: {NAVY_2}; color: #e8ecf6; font-weight: 600; font-size: .7rem; letter-spacing: .08em;
               padding: .5rem .5rem; text-align: center; white-space: nowrap; }}
table.snd td {{ padding: .34rem .5rem; text-align: center; color: {TEXT}; border-bottom: 1px solid #eceef2; white-space: nowrap; }}
table.snd td:first-child, table.snd th:first-child {{ text-align: left; padding-left: 1.1rem; }}
table.snd td:first-child {{ color: {NAVY}; font-weight: 600; }}
table.snd tbody tr:hover td {{ background: #f5f7fb; }}
table.snd tr.tot td {{ font-weight: 700; }}
table.snd tr.top td {{ border-top: 1.5px solid #8a93a6; }}
table.snd tr.dim td {{ color: #8a93a6; }}
table.snd tr.dim td:first-child {{ color: #8a93a6; font-weight: 500; }}
table.snd tr.bal td {{ background: #eef2fb; font-weight: 700; border-top: 1.5px solid #c5cde0; border-bottom: 1.5px solid #c5cde0; }}
table.snd td.neg {{ color: #c62828; }}
table.snd td.tr, table.snd th.tr {{ border-left: 1px solid #e3e6ec; }}
</style>""", unsafe_allow_html=True)


# ---------- data ----------
@st.cache_data
def load(mtime: float) -> pd.DataFrame:
    return pd.read_csv(CSV).set_index("item")


def raw() -> pd.DataFrame:
    return load(CSV.stat().st_mtime)


def balance(df: pd.DataFrame) -> pd.DataFrame:
    """Raw CSV -> full SnD sheet. All derived rows are computed here, never typed in."""
    yrs = [c for c in df.columns if c != "type"]
    d = df[yrs].apply(pd.to_numeric, errors="coerce")
    origins = d[df["type"] == "origin"]
    cons = d[df["type"] == "consumption"].iloc[0]
    open_stock = d[df["type"] == "stock"].iloc[0].iloc[0]
    prod = origins.sum(min_count=1)
    bal = prod - cons
    end = bal.cumsum() - bal.iloc[0] + open_stock     # first year = given stock, then roll forward
    out = origins.copy()
    out.loc["Production"] = prod
    out.loc["Consumption"] = cons
    out.loc["Consumption %"] = cons.pct_change()
    out.loc["Balance"] = bal
    out.loc["End season stock"] = end
    out.loc["S/U"] = end / cons
    return out


# ---------- github save ----------
def save(df: pd.DataFrame, msg: str) -> str:
    text = df.reset_index().to_csv(index=False, lineterminator="\n")
    CSV.write_text(text, encoding="utf-8")
    load.clear()
    tok, repo = st.secrets.get("GITHUB_TOKEN", ""), st.secrets.get("GITHUB_REPO", "")
    if not tok or not repo:
        return "Saved locally (no GITHUB_TOKEN in secrets, so not pushed)."
    url = f"https://api.github.com/repos/{repo}/contents/{REPO_PATH}"
    hdr = {"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"}
    branch = st.secrets.get("GITHUB_BRANCH", "main")
    sha = requests.get(url, headers=hdr, params={"ref": branch}, timeout=15).json().get("sha")
    r = requests.put(url, headers=hdr, timeout=15, json={
        "message": msg, "branch": branch, "sha": sha,
        "content": base64.b64encode(text.encode()).decode()})
    if r.status_code in (200, 201):
        return "Saved and pushed to GitHub."
    return f"Saved locally, GitHub push failed: {r.status_code} {r.text[:200]}"


# ---------- render helpers ----------
def h(text: str) -> None:
    st.markdown(f"<div class='h'>{text}</div>", unsafe_allow_html=True)


def spark(vals: pd.Series, kind: str) -> str:
    v = vals.dropna()
    if len(v) < 2:
        return ""
    w, ht, n = 110, 22, len(vals)
    bw = w / n
    if kind == "bal":
        m = max(v.abs().max(), 1e-9)
        bars = "".join(f"<rect x='{i * bw + 1:.1f}' y='{ht / 2 - max(x, 0) / m * ht / 2:.1f}' width='{bw - 2:.1f}' "
                       f"height='{max(abs(x) / m * ht / 2, .8):.1f}' fill='{'#2e7d32' if x >= 0 else '#c62828'}'/>"
                       for i, x in enumerate(vals) if pd.notna(x))
    else:
        lo, hi = min(v.min(), 0), v.max()
        bars = "".join(f"<rect x='{i * bw + 1:.1f}' y='{ht - (x - lo) / (hi - lo) * ht:.1f}' width='{bw - 2:.1f}' "
                       f"height='{(x - lo) / (hi - lo) * ht:.1f}' fill='{BAR}'/>"
                       for i, x in enumerate(vals) if pd.notna(x) and hi > lo)
    return f"<svg width='{w}' height='{ht}'>{bars}</svg>"


ROW_STYLE = {"Production": ("tot top", "num"), "Consumption": ("tot", "num"), "Consumption %": ("dim", "pct"),
             "Balance": ("bal", "bal"), "End season stock": ("", "num"), "S/U": ("dim", "pct")}


def cell(v, kind: str) -> tuple[str, str]:
    if pd.isna(v):
        return "", ""
    if kind == "pct":
        return f"{v:.1%}", ""
    if kind == "bal":
        return (f"({abs(v):.1f})", "neg") if v < 0 else (f"{v:.1f}", "")
    return f"{v:.1f}", ""


def snd_table(t: pd.DataFrame, title: str, sub: str) -> str:
    head = "<tr><th></th>" + "".join(f"<th>{c}</th>" for c in t.columns) + "<th class='tr'>TREND</th></tr>"
    body = []
    for name, row in t.iterrows():
        cls, kind = ROW_STYLE.get(name, ("", "num"))
        tds = "".join(f"<td class='{c}'>{s}</td>" for s, c in (cell(v, kind) for v in row))
        body.append(f"<tr class='{cls}'><td>{name}</td>{tds}<td class='tr'>{spark(row, kind)}</td></tr>")
    return (f"<div class='tw'><div class='cap'>{title}<span>{sub}</span></div>"
            f"<table class='snd'>{head}{''.join(body)}</table></div>")


def styled(fig: go.Figure, height=380) -> go.Figure:
    fig.update_layout(height=height, margin=dict(l=14, r=14, t=16, b=10), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Manrope, sans-serif", color=DIM, size=11),
                      legend=dict(orientation="h", y=-0.14, font=dict(color=TEXT)), hovermode="x unified",
                      hoverlabel=dict(bgcolor="#fff", bordercolor=GRID, font=dict(color=TEXT)))
    fig.update_xaxes(showgrid=False, linecolor=GRID)
    fig.update_yaxes(gridcolor=GRID, zeroline=False)
    return fig


# ---------- page ----------
df_raw = raw()
full = balance(df_raw)
years = list(full.columns)

with st.sidebar:
    st.markdown("<div class='app'>Epiphany</div><div class='brand'>SnD</div><div class='brand-s'>Arabica · Jul-Jun · m bags</div>",
                unsafe_allow_html=True)
    page = st.radio("View", ["Balance", "Update data"], label_visibility="collapsed")
    y0, y1 = st.select_slider("Seasons", options=years, value=(years[0], years[-1]))
    origins = list(df_raw.index[df_raw["type"] == "origin"])
    pick = st.multiselect("Origins in chart", origins, default=origins)

cols = years[years.index(y0): years.index(y1) + 1]
t = full[cols]
last = cols[-1]

if page == "Balance":
    b, su = t.loc["Balance", last], t.loc["S/U", last]
    st.markdown(f"<div class='title'>Arabica <b>balance sheet</b></div><div class='chips'>"
                f"<span class='chip on'>{y0} to {y1}</span>"
                f"<span class='chip {'good' if b >= 0 else 'bad'}'>{last} balance {b:+.1f}</span>"
                f"<span class='chip'>{last} S/U {su:.1%}</span></div>", unsafe_allow_html=True)

    st.markdown(snd_table(t, "ARABICA", "Jul-Jun"), unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    with c1:
        h("Production vs consumption")
        fig = go.Figure()
        fig.add_bar(x=cols, y=t.loc["Production"], name="Production", marker_color=NAVY_2)
        fig.add_bar(x=cols, y=t.loc["Consumption"], name="Consumption", marker_color=GOLD)
        fig.add_scatter(x=cols, y=t.loc["S/U"] * 100, name="S/U %", yaxis="y2",
                        line=dict(color="#c62828", width=2), mode="lines+markers")
        fig.update_layout(barmode="group", yaxis2=dict(overlaying="y", side="right", showgrid=False, ticksuffix="%"))
        st.plotly_chart(styled(fig), width="stretch", config={"displayModeBar": False})
    with c2:
        h("Origin mix")
        fig = go.Figure()
        pal = ["#3d4a5c", "#4f74a8", "#6fa8a0", "#c9a25a", "#a85f86", "#7a62ad", "#9aa5b8"]
        for i, o in enumerate(pick):
            fig.add_bar(x=cols, y=t.loc[o], name=o, marker_color=pal[i % len(pal)])
        fig.update_layout(barmode="stack")
        st.plotly_chart(styled(fig), width="stretch", config={"displayModeBar": False})

else:
    st.markdown("<div class='title'>Update <b>data</b></div><div class='chips'>"
                "<span class='chip'>Edit cells, add a season column via CSV, then Save</span></div>", unsafe_allow_html=True)
    h("Inputs")
    st.caption("Only inputs live here. Production, balance, stocks and S/U are calculated. "
               "type = origin / consumption / stock. Add an origin by adding a row with type 'origin'.")
    edited = st.data_editor(df_raw, num_rows="dynamic", width="stretch", key="ed")
    c1, c2 = st.columns([3, 1])
    msg = c1.text_input("Change note", "Update SnD inputs")
    if c2.button("Save", type="primary", width="stretch"):
        st.toast(save(edited, msg))
        st.rerun()

    h("Add a season")
    n1, n2 = st.columns([3, 1])
    new = n1.text_input("New season label", placeholder="28/29*", label_visibility="collapsed")
    if n2.button("Add column", width="stretch") and new and new not in df_raw.columns:
        df2 = df_raw.copy()
        df2[new] = df2[years[-1]].where(df2["type"] != "stock")   # copy last season as starting point
        st.toast(save(df2, f"Add season {new}"))
        st.rerun()
