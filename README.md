# Car Sales Dashboard

A minimal Flask web server that receives car sales data via a POST endpoint and displays it as a live dashboard with charts.

## Features

- **POST `/data`** — accepts a JSON array of car sales records and stores them in memory
- **GET `/`** — dashboard UI with charts, KPIs, and a data table; auto-polls for new data every 5 seconds (only re-renders on change)
- **GET `/health`** — returns `ok` with HTTP 200
- **Clear Data** button — wipes the current dataset and waits for the next POST

## Tech Stack

- Python / Flask
- Chart.js (via CDN)
- Gunicorn (production server)
- No database — data resets on restart

## Local Development

```bash
pip install -r requirements.txt
python app.py
```

Server runs on `http://localhost:5000`.

## Production (Render.com)

1. Push this repo to GitHub
2. Create a new **Web Service** on [render.com](https://render.com)
3. Set the **Start Command** to:
   ```
   gunicorn app:app
   ```
4. Render injects the `$PORT` environment variable automatically

## Endpoint Reference

### `POST /data`

Accepts a JSON array of car sales objects:

```json
[
  {
    "Date": "2024-01-15",
    "Region": "West",
    "Country": "Germany",
    "Model": "Audi Q5",
    "VIN": "B3KNEUV3FC5XH7ESJ",
    "Revenue": 117790.45,
    "Discount": 11.4,
    "Sales_Channel": "Online",
    "Salesperson": "Anna Schmidt",
    "Conversion_Rate": 43.3,
    "Customer_Segment": "B2B"
  }
]
```

| Field | Type | Values |
|---|---|---|
| `Date` | string `YYYY-MM-DD` | |
| `Region` | string | `West`, `Nord`, `East`, `South` |
| `Country` | string | |
| `Model` | string | e.g. `VW Golf`, `Audi Q5`, `BMW X5` |
| `VIN` | string | |
| `Revenue` | number | euros |
| `Discount` | number | percentage |
| `Sales_Channel` | string | `Online`, `Fleet`, `Dealer` |
| `Salesperson` | string | |
| `Conversion_Rate` | number | percentage |
| `Customer_Segment` | string | `B2B`, `B2C` |

**Response:**
```json
{ "status": "ok", "records": 100 }
```

### `GET /health`

```
200 OK
ok
```
