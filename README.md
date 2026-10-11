# SwiftLogic AI — Returns & RTO analyser

D2C / e-commerce demo: join orders, pincodes, and return reasons in pandas, flag high-RTO SKUs and cities, and ship a Plotly dashboard plus a weekly openpyxl pack.

**Fictional brand:** Prakriti Naturals  
**Engagement band:** ₹40,000 – ₹85,000

## What it does

1. Generates ~4,200 synthetic D2C orders (SKU, GMV, COD/Prepaid, pincode, status).
2. Joins `orders × pincode master × return-reason catalogue` in pandas.
3. Flags high-RTO SKUs (≥18% RTO, ≥40 orders), cities (≥16% RTO, ≥50 orders), and pincodes (≥22% RTO, ≥20 orders).
4. Serves a Plotly dashboard (weekly trend, reasons, city, SKU, payment) via FastAPI.
5. Builds a multi-sheet openpyxl weekly pack on demand.

## Stack

- FastAPI + uvicorn
- pandas / numpy
- Plotly
- openpyxl
- Jinja2 (dashboard template)

Single Python process — no Node required.

## Quick start

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate.bat
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
python run.py
```

Open http://127.0.0.1:8000

- Dashboard: `/`
- Health: `/health`
- JSON: `/api/overview`, `/api/charts`, `/api/meta`
- Excel pack: `/api/report` → `reports/rto_weekly_pack_YYYYMMDD.xlsx`

## Environment

| Variable | Default | Purpose |
|---|---|---|
| `HOST` | `127.0.0.1` | Bind address. Use `0.0.0.0` on a host. |
| `PORT` | `8000` | Injected by Render / Railway. |
| `RELOAD` | `true` | Set `false` in production. |
| `BRAND` | `Prakriti Naturals` | Cover title and page heading. |
| `SEED` | `42` | Reproducible dummy data. |

## Project layout

```
app/
  data.py      synthetic orders, pincode master, reason catalogue
  engine.py    joins + high-RTO flags + KPIs
  excel.py     weekly openpyxl pack
  main.py      FastAPI routes and Plotly JSON
  config.py
static/        dashboard CSS / JS
templates/     index.html
run.py
DEPLOY.md
```

## Deploy

See [DEPLOY.md](DEPLOY.md) for Render / Railway / VPS notes.

Build: `pip install -r requirements.txt`  
Start: `HOST=0.0.0.0 RELOAD=false python run.py`  
Health check: `/health`
