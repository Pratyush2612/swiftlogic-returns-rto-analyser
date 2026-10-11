"""Join orders × pincodes × reasons and flag high-RTO SKUs / cities."""

from __future__ import annotations

from functools import lru_cache

import pandas as pd

from app.config import HIGH_RTO_CITY_PCT, HIGH_RTO_PIN_PCT, HIGH_RTO_SKU_PCT
from app.data import generate_orders, pincode_master, reason_catalogue


def _rate(part: int, total: int) -> float:
    return round(100.0 * part / total, 2) if total else 0.0


@lru_cache(maxsize=1)
def warehouse() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    orders = generate_orders()
    pins = pincode_master()
    reasons = reason_catalogue()
    return orders, pins, reasons


def joined() -> pd.DataFrame:
    orders, pins, reasons = warehouse()
    df = orders.merge(pins, on="pincode", how="left")
    df = df.merge(reasons, on="reason_code", how="left")
    df["week"] = df["order_date"].dt.to_period("W-SUN").dt.start_time
    df["is_rto"] = df["status"].eq("RTO")
    df["is_return"] = df["status"].eq("Returned")
    df["is_failed"] = df["is_rto"] | df["is_return"]
    return df


def kpis(df: pd.DataFrame | None = None) -> dict:
    df = df if df is not None else joined()
    n = len(df)
    rto = int(df.is_rto.sum())
    ret = int(df.is_return.sum())
    gmv = float(df.gmv.sum())
    lost = float(df.loc[df.is_failed, "gmv"].sum())
    return {
        "orders": n,
        "gmv": round(gmv, 0),
        "rto_orders": rto,
        "return_orders": ret,
        "rto_pct": _rate(rto, n),
        "return_pct": _rate(ret, n),
        "failed_gmv": round(lost, 0),
        "cod_share": _rate(int(df.payment.eq("COD").sum()), n),
        "cities": int(df.city.nunique()),
        "skus": int(df.sku.nunique()),
    }


def flag_skus(df: pd.DataFrame | None = None) -> pd.DataFrame:
    df = df if df is not None else joined()
    tmp = df.assign(failed_amt=df.gmv.where(df.is_failed, 0.0))
    g = tmp.groupby(["sku", "sku_name", "category"], as_index=False).agg(
        orders=("order_id", "count"),
        gmv=("gmv", "sum"),
        rto=("is_rto", "sum"),
        returns=("is_return", "sum"),
        failed_gmv=("failed_amt", "sum"),
    )
    g["rto_pct"] = (100 * g.rto / g.orders).round(2)
    g["return_pct"] = (100 * g.returns / g.orders).round(2)
    g["flag"] = g.rto_pct.ge(HIGH_RTO_SKU_PCT) & g.orders.ge(40)
    return g.sort_values(["flag", "rto_pct"], ascending=[False, False])


def flag_cities(df: pd.DataFrame | None = None) -> pd.DataFrame:
    df = df if df is not None else joined()
    g = df.groupby(["city", "state"], as_index=False).agg(
        orders=("order_id", "count"),
        gmv=("gmv", "sum"),
        rto=("is_rto", "sum"),
        returns=("is_return", "sum"),
        cod=("payment", lambda s: int(s.eq("COD").sum())),
    )
    g["rto_pct"] = (100 * g.rto / g.orders).round(2)
    g["cod_pct"] = (100 * g.cod / g.orders).round(1)
    g["flag"] = g.rto_pct.ge(HIGH_RTO_CITY_PCT) & g.orders.ge(50)
    return g.sort_values(["flag", "rto_pct"], ascending=[False, False])


def flag_pincodes(df: pd.DataFrame | None = None) -> pd.DataFrame:
    df = df if df is not None else joined()
    g = df.groupby(["pincode", "city", "state"], as_index=False).agg(
        orders=("order_id", "count"),
        rto=("is_rto", "sum"),
        gmv=("gmv", "sum"),
    )
    g["rto_pct"] = (100 * g.rto / g.orders).round(2)
    g["flag"] = g.rto_pct.ge(HIGH_RTO_PIN_PCT) & g.orders.ge(20)
    return g.sort_values(["flag", "rto_pct"], ascending=[False, False])


def reasons_breakup(df: pd.DataFrame | None = None) -> pd.DataFrame:
    df = df if df is not None else joined()
    failed = df[df.is_failed & df.reason_code.notna()]
    g = failed.groupby(["reason_code", "reason_label", "bucket"], as_index=False).agg(
        orders=("order_id", "count"),
        gmv=("gmv", "sum"),
    )
    g["share_pct"] = (100 * g.orders / g.orders.sum()).round(1)
    return g.sort_values("orders", ascending=False)


def weekly_trend(df: pd.DataFrame | None = None) -> pd.DataFrame:
    df = df if df is not None else joined()
    g = df.groupby("week", as_index=False).agg(
        orders=("order_id", "count"),
        rto=("is_rto", "sum"),
        returns=("is_return", "sum"),
        gmv=("gmv", "sum"),
    )
    g["rto_pct"] = (100 * g.rto / g.orders).round(2)
    g["week"] = g["week"].dt.strftime("%Y-%m-%d")
    return g.sort_values("week")


def payment_split(df: pd.DataFrame | None = None) -> pd.DataFrame:
    df = df if df is not None else joined()
    g = df.groupby("payment", as_index=False).agg(
        orders=("order_id", "count"),
        rto=("is_rto", "sum"),
        gmv=("gmv", "sum"),
    )
    g["rto_pct"] = (100 * g.rto / g.orders).round(2)
    return g


def filter_frame(
    city: str | None = None,
    sku: str | None = None,
    payment: str | None = None,
    status: str | None = None,
) -> pd.DataFrame:
    df = joined()
    if city and city != "all":
        df = df[df.city == city]
    if sku and sku != "all":
        df = df[df.sku == sku]
    if payment and payment != "all":
        df = df[df.payment == payment]
    if status and status != "all":
        df = df[df.status == status]
    return df
