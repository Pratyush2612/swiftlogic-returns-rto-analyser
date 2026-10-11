from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

BRAND = os.getenv("BRAND", "Prakriti Naturals")
SEED = int(os.getenv("SEED", "42"))
HIGH_RTO_SKU_PCT = 18.0
HIGH_RTO_CITY_PCT = 16.0
HIGH_RTO_PIN_PCT = 22.0
