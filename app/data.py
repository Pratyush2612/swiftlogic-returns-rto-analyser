"""Synthetic D2C orders, pincode master, and return-reason catalogue."""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.config import SEED

SKUS = [
    ("PN-HAIR-100", "Bhringraj Hair Oil 100ml", "Hair", 449),
    ("PN-HAIR-200", "Bhringraj Hair Oil 200ml", "Hair", 799),
    ("PN-FACE-50", "Haldi Face Wash 50ml", "Skin", 299),
    ("PN-FACE-100", "Haldi Face Wash 100ml", "Skin", 499),
    ("PN-SOAP-01", "Neem + Tulsi Soap", "Bath", 149),
    ("PN-SCRUB-01", "Coffee Body Scrub", "Bath", 399),
    ("PN-OIL-01", "Sesame Cooking Oil 500ml", "Pantry", 289),
    ("PN-GHEE-01", "A2 Cow Ghee 250ml", "Pantry", 649),
    ("PN-TEA-01", "Tulsi Green Tea 25s", "Pantry", 229),
    ("PN-KIT-01", "Festive Ritual Kit", "Gifting", 1299),
]

# city, state, sample pincodes, baseline RTO lift (multiplicative)
PINCODES = [
    ("Pune", "MH", ["411001", "411014", "411038", "411045"], 0.9),
    ("Mumbai", "MH", ["400001", "400053", "400070", "400092"], 1.05),
    ("Thane", "MH", ["400601", "400607"], 1.15),
    ("Bengaluru", "KA", ["560001", "560038", "560066", "560102"], 0.85),
    ("Hyderabad", "TS", ["500001", "500032", "500081"], 1.0),
    ("Chennai", "TN", ["600001", "600028", "600042"], 0.95),
    ("Delhi", "DL", ["110001", "110017", "110048", "110092"], 1.25),
    ("Noida", "UP", ["201301", "201304"], 1.35),
    ("Gurgaon", "HR", ["122001", "122018"], 1.2),
    ("Jaipur", "RJ", ["302001", "302017"], 1.4),
    ("Ahmedabad", "GJ", ["380001", "380015"], 1.1),
    ("Surat", "GJ", ["395001", "395007"], 1.3),
    ("Kolkata", "WB", ["700001", "700019", "700053"], 1.15),
    ("Lucknow", "UP", ["226001", "226010"], 1.55),
    ("Patna", "BR", ["800001", "800020"], 1.7),
    ("Indore", "MP", ["452001", "452010"], 1.2),
    ("Nagpur", "MH", ["440001", "440010"], 1.25),
    ("Bhopal", "MP", ["462001", "462016"], 1.35),
]

REASONS = [
    ("RTO_REFUSED", "Customer refused delivery", "RTO", 0.38),
    ("RTO_ADDR", "Address incomplete / not found", "RTO", 0.18),
    ("RTO_PHONE", "Phone unreachable", "RTO", 0.14),
    ("RTO_COD", "COD cash not available", "RTO", 0.12),
    ("RET_SIZE", "Size / quantity mismatch", "Return", 0.06),
    ("RET_QUALITY", "Quality / leakage complaint", "Return", 0.05),
    ("RET_WRONG", "Wrong SKU shipped", "Return", 0.04),
    ("RET_CHANGE", "Customer changed mind", "Return", 0.03),
]


def pincode_master() -> pd.DataFrame:
    rows = []
    for city, state, pins, lift in PINCODES:
        for pin in pins:
            rows.append(
                {
                    "pincode": pin,
                    "city": city,
                    "state": state,
                    "rto_lift": lift,
                    "cod_share": 0.72 if lift >= 1.3 else 0.55,
                    "serviceable": True,
                }
            )
    return pd.DataFrame(rows)


def reason_catalogue() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"reason_code": c, "reason_label": l, "bucket": b, "weight": w}
            for c, l, b, w in REASONS
        ]
    )


def generate_orders(n: int = 4200, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    pins = pincode_master()
    sku_df = pd.DataFrame(SKUS, columns=["sku", "sku_name", "category", "mrp"])
    reasons = reason_catalogue()

    start = pd.Timestamp("2026-03-01")
    days = np.arange(0, 210)
    # more volume toward recent weeks
    day_w = np.linspace(0.6, 1.4, len(days))
    day_w /= day_w.sum()

    sku_w = np.array([0.14, 0.10, 0.12, 0.09, 0.11, 0.07, 0.08, 0.09, 0.08, 0.12])
    pin_idx = rng.choice(len(pins), size=n, replace=True)
    sku_idx = rng.choice(len(sku_df), size=n, p=sku_w)
    day_off = rng.choice(days, size=n, p=day_w)

    rows = []
    for i in range(n):
        pin_row = pins.iloc[int(pin_idx[i])]
        sku_row = sku_df.iloc[int(sku_idx[i])]
        order_dt = start + pd.Timedelta(days=int(day_off[i]), hours=int(rng.integers(8, 22)))
        qty = int(rng.choice([1, 1, 1, 2, 3], p=[0.62, 0.18, 0.1, 0.07, 0.03]))
        pay = "COD" if rng.random() < float(pin_row.cod_share) else "Prepaid"
        # base RTO probability
        base = 0.11
        if pay == "COD":
            base += 0.09
        if sku_row.category == "Gifting":
            base += 0.04
        if sku_row.mrp >= 600:
            base += 0.03
        p_rto = min(0.55, base * float(pin_row.rto_lift))
        p_ret = 0.035 if pay == "Prepaid" else 0.02
        roll = rng.random()
        if roll < p_rto:
            status = "RTO"
        elif roll < p_rto + p_ret:
            status = "Returned"
        else:
            status = "Delivered"

        reason_code = None
        if status == "RTO":
            rto = reasons[reasons.bucket == "RTO"]
            reason_code = str(rng.choice(rto.reason_code, p=rto.weight / rto.weight.sum()))
        elif status == "Returned":
            ret = reasons[reasons.bucket == "Return"]
            reason_code = str(rng.choice(ret.reason_code, p=ret.weight / ret.weight.sum()))

        rows.append(
            {
                "order_id": f"PN{100000 + i}",
                "order_date": order_dt,
                "sku": sku_row.sku,
                "sku_name": sku_row.sku_name,
                "category": sku_row.category,
                "qty": qty,
                "gmv": round(float(sku_row.mrp) * qty, 2),
                "payment": pay,
                "pincode": pin_row.pincode,
                "status": status,
                "reason_code": reason_code,
                "awb": f"SL{rng.integers(10_000_000, 99_999_999)}",
            }
        )
    return pd.DataFrame(rows)
