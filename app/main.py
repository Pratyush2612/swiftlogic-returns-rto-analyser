from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape
import plotly.express as px
import plotly.graph_objects as go

from app.config import BRAND, ROOT
from app import engine
from app.excel import build_weekly_pack

app = FastAPI(title="SwiftLogic AI — Returns & RTO analyser", version="1.0.0")
app.mount("/static", StaticFiles(directory=str(ROOT / "static")), name="static")

TEMPLATES = Environment(
    loader=FileSystemLoader(str(ROOT / "templates")),
    autoescape=select_autoescape(["html"]),
)

GOLD = "#e89b1e"
TEAL = "#0d9b7a"
ROSE = "#e55a5a"
INK = "#1a1d2e"


def _layout(fig: go.Figure) -> dict:
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=INK, size=12),
        margin=dict(l=40, r=20, t=40, b=40),
        legend=dict(orientation="h", y=-0.18),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="#eef1f8")
    # fig.to_json() converts numpy types; to_plotly_json() is not FastAPI-safe
    return json.loads(fig.to_json())


@app.get("/health")
def health():
    return {"ok": True, "brand": BRAND}


@app.get("/", response_class=HTMLResponse)
def home():
    html = TEMPLATES.get_template("index.html").render(brand=BRAND)
    return HTMLResponse(html)


@app.get("/api/meta")
def meta():
    df = engine.joined()
    return {
        "brand": BRAND,
        "cities": sorted(df.city.unique().tolist()),
        "skus": sorted(df.sku.unique().tolist()),
        "payments": ["COD", "Prepaid"],
        "statuses": sorted(df.status.unique().tolist()),
    }


@app.get("/api/overview")
def overview(
    city: str = Query("all"),
    sku: str = Query("all"),
    payment: str = Query("all"),
):
    df = engine.filter_frame(city=city, sku=sku, payment=payment)
    return {
        "kpis": engine.kpis(df),
        "skus": engine.flag_skus(df).to_dict(orient="records"),
        "cities": engine.flag_cities(df).to_dict(orient="records"),
        "pincodes": engine.flag_pincodes(df).head(25).to_dict(orient="records"),
        "reasons": engine.reasons_breakup(df).to_dict(orient="records"),
        "weekly": engine.weekly_trend(df).to_dict(orient="records"),
        "payment": engine.payment_split(df).to_dict(orient="records"),
    }


@app.get("/api/charts")
def charts(
    city: str = Query("all"),
    sku: str = Query("all"),
    payment: str = Query("all"),
):
    df = engine.filter_frame(city=city, sku=sku, payment=payment)
    weekly = engine.weekly_trend(df)
    reasons = engine.reasons_breakup(df)
    cities = engine.flag_cities(df)
    skus = engine.flag_skus(df)
    pay = engine.payment_split(df)

    fig_week = go.Figure()
    fig_week.add_bar(x=weekly.week, y=weekly.orders, name="Orders", marker_color="#cfd5e6")
    fig_week.add_scatter(
        x=weekly.week, y=weekly.rto_pct, name="RTO %", yaxis="y2",
        line=dict(color=ROSE, width=2.4), mode="lines+markers",
    )
    fig_week.update_layout(
        yaxis=dict(title="Orders"),
        yaxis2=dict(title="RTO %", overlaying="y", side="right"),
        title="Weekly volume vs RTO %",
    )

    fig_reason = px.bar(
        reasons, x="orders", y="reason_label", color="bucket",
        orientation="h",
        color_discrete_map={"RTO": ROSE, "Return": GOLD},
        title="Failure reasons",
    )
    fig_reason.update_layout(yaxis={"categoryorder": "total ascending"})

    fig_city = px.bar(
        cities.sort_values("rto_pct", ascending=False).head(12),
        x="city", y="rto_pct", color="flag",
        color_discrete_map={True: ROSE, False: TEAL},
        title="RTO % by city",
    )

    fig_sku = px.bar(
        skus.sort_values("rto_pct", ascending=False),
        x="rto_pct", y="sku_name", color="flag",
        orientation="h",
        color_discrete_map={True: ROSE, False: TEAL},
        title="RTO % by SKU",
    )
    fig_sku.update_layout(yaxis={"categoryorder": "total ascending"})

    fig_pay = px.bar(
        pay, x="payment", y="rto_pct", color="payment",
        color_discrete_map={"COD": ROSE, "Prepaid": TEAL},
        title="RTO % by payment",
    )

    return {
        "weekly": _layout(fig_week),
        "reasons": _layout(fig_reason),
        "cities": _layout(fig_city),
        "skus": _layout(fig_sku),
        "payment": _layout(fig_pay),
    }


@app.get("/api/report")
def report():
    path = build_weekly_pack()
    return FileResponse(
        path,
        filename=path.name,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
