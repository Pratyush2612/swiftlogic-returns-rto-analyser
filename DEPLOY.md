# Deploy — Returns & RTO analyser

Single Python process: **FastAPI** serves the Plotly dashboard, pandas joins, and the weekly openpyxl pack.

Fictional brand in the demo: **Prakriti Naturals**.

## Local

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python run.py          # http://127.0.0.1:8000
```

- Dashboard: `/`
- Health: `/health`
- JSON: `/api/overview`, `/api/charts`, `/api/meta`
- Excel pack: `/api/report` → `reports/rto_weekly_pack_YYYYMMDD.xlsx`

## What it does

1. Generates ~4,200 D2C orders (SKU, GMV, COD/Prepaid, pincode, status).
2. Joins `orders × pincode master × return-reason catalogue` in pandas.
3. Flags high-RTO SKUs (≥18% RTO, ≥40 orders) and cities (≥16% RTO, ≥50 orders).
4. Renders Plotly charts (weekly trend, reasons, city, SKU, payment).
5. Builds a multi-sheet openpyxl workbook for the weekly ops pack.

## Environment

| Variable | Default | Purpose |
|---|---|---|
| `HOST` | `127.0.0.1` | Bind. Use `0.0.0.0` on a host. |
| `PORT` | `8000` | Render/Railway inject this. |
| `RELOAD` | `true` | Set `false` in production. |
| `BRAND` | `Prakriti Naturals` | Cover title. |
| `SEED` | `42` | Reproducible dummy data. |

## Render / Railway / VPS

Build: `pip install -r requirements.txt`  
Start: `HOST=0.0.0.0 RELOAD=false python run.py`  
Health check: `/health`

## Engagement band

Portfolio card: **₹40,000 – ₹85,000** (D2C / e-commerce Returns & RTO analyser).
