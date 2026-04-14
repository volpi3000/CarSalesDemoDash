import os
import json
from datetime import datetime, timezone
from flask import Flask, request, jsonify, Response

app = Flask(__name__)

last_entry = {"received_at": None, "data": None}   # data is a list of sale dicts

# ── HTML ──────────────────────────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Car Sales Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    :root {
      --bg:      #0d1117;
      --surface: #161b22;
      --card:    #1c2130;
      --border:  #2a3044;
      --accent:  #4f8ef7;
      --green:   #34d399;
      --yellow:  #fbbf24;
      --red:     #f87171;
      --purple:  #a78bfa;
      --teal:    #2dd4bf;
      --text:    #e2e8f0;
      --muted:   #64748b;
      --label:   #94a3b8;
    }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
      min-height: 100vh;
      padding-bottom: 52px;
    }

    /* ── header ── */
    header {
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      padding: 14px 28px;
      display: flex; align-items: center; justify-content: space-between;
      position: sticky; top: 0; z-index: 100;
    }
    .logo { display: flex; align-items: center; gap: 11px; }
    .logo-icon {
      width: 34px; height: 34px;
      background: linear-gradient(135deg, var(--accent), var(--purple));
      border-radius: 8px;
      display: flex; align-items: center; justify-content: center;
      font-size: 17px;
    }
    .logo h1  { font-size: 1.05rem; font-weight: 700; }
    .logo sub { font-size: .7rem; color: var(--muted); display: block; margin-top: 1px; }
    .header-right { display: flex; align-items: center; gap: 12px; }
    .live-badge {
      display: flex; align-items: center; gap: 6px;
      font-size: .72rem; color: var(--green);
      background: rgba(52,211,153,.07);
      border: 1px solid rgba(52,211,153,.2);
      border-radius: 99px; padding: 4px 10px;
    }
    .pulse { width: 6px; height: 6px; border-radius: 50%; background: var(--green); animation: pulse 2s infinite; }
    @keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.3;transform:scale(.65)} }
    .btn {
      border-radius: 6px; padding: 6px 14px; font-size: .78rem;
      cursor: pointer; transition: .15s;
    }
    .btn-ghost {
      background: transparent; border: 1px solid var(--border); color: var(--label);
    }
    .btn-ghost:hover { border-color: var(--red); color: var(--red); background: rgba(248,113,113,.06); }

    /* ── layout ── */
    main { max-width: 1280px; margin: 0 auto; padding: 28px 24px; }

    /* ── empty ── */
    .empty {
      display: flex; flex-direction: column; align-items: center;
      justify-content: center; gap: 14px;
      min-height: 380px;
      color: var(--muted);
      background: var(--surface);
      border: 1px dashed var(--border);
      border-radius: 16px;
    }
    .empty-icon { font-size: 3rem; }
    .empty h2  { font-size: 1rem; font-weight: 500; color: var(--label); }
    .empty code { background: var(--card); padding: 5px 12px; border-radius: 6px; font-size: .8rem; color: var(--accent); }

    /* ── section title ── */
    .section-head {
      display: flex; align-items: baseline; justify-content: space-between;
      margin: 28px 0 14px;
    }
    .section-title { font-size: .72rem; font-weight: 700; color: var(--muted); letter-spacing: .1em; text-transform: uppercase; }
    .received-at   { font-size: .72rem; color: var(--muted); }

    /* ── KPI cards ── */
    .kpi-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(190px, 1fr)); gap: 14px; }
    .kpi {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px 18px;
      position: relative; overflow: hidden;
    }
    .kpi::before {
      content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px;
      background: var(--kpi-color, var(--accent));
      border-radius: 12px 12px 0 0;
    }
    .kpi-label { font-size: .68rem; color: var(--muted); text-transform: uppercase; letter-spacing: .08em; margin-bottom: 8px; }
    .kpi-value { font-size: 1.6rem; font-weight: 700; line-height: 1; }
    .kpi-sub   { font-size: .72rem; color: var(--muted); margin-top: 5px; }

    /* ── chart grid ── */
    .chart-grid-2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; }
    .chart-grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
    @media (max-width: 900px) {
      .chart-grid-2, .chart-grid-3 { grid-template-columns: 1fr; }
    }
    @media (max-width: 1100px) {
      .chart-grid-3 { grid-template-columns: repeat(2, 1fr); }
    }

    .chart-card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 18px 18px 14px;
    }
    .chart-card.wide { grid-column: 1 / -1; }
    .chart-title { font-size: .75rem; font-weight: 600; color: var(--label); text-transform: uppercase; letter-spacing: .07em; margin-bottom: 14px; }
    .chart-wrap  { position: relative; }

    /* ── table ── */
    .table-card {
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: hidden;
      margin-top: 0;
    }
    .table-header {
      padding: 12px 18px;
      border-bottom: 1px solid var(--border);
      display: flex; align-items: center; justify-content: space-between;
    }
    .table-title { font-size: .75rem; font-weight: 600; color: var(--label); text-transform: uppercase; letter-spacing: .07em; }
    .table-count { font-size: .72rem; color: var(--muted); }
    .table-wrap  { overflow-x: auto; max-height: 360px; overflow-y: auto; }
    table { width: 100%; border-collapse: collapse; font-size: .8rem; }
    th {
      position: sticky; top: 0;
      background: var(--surface);
      padding: 9px 14px;
      text-align: left;
      font-size: .68rem; font-weight: 600; color: var(--muted);
      text-transform: uppercase; letter-spacing: .06em;
      border-bottom: 1px solid var(--border);
      white-space: nowrap;
    }
    td { padding: 8px 14px; border-bottom: 1px solid rgba(42,48,68,.6); white-space: nowrap; }
    tr:last-child td { border-bottom: none; }
    tr:hover td { background: rgba(255,255,255,.02); }

    .badge {
      display: inline-block; padding: 2px 9px;
      border-radius: 99px; font-size: .7rem; font-weight: 600;
    }
    .badge-blue   { background: rgba(79,142,247,.12); color: #7ab3ff; border: 1px solid rgba(79,142,247,.28); }
    .badge-green  { background: rgba(52,211,153,.10); color: #5ee8b8; border: 1px solid rgba(52,211,153,.28); }
    .badge-purple { background: rgba(167,139,250,.12); color: #c4b5fd; border: 1px solid rgba(167,139,250,.28); }
    .badge-yellow { background: rgba(251,191,36,.10);  color: #fcd34d; border: 1px solid rgba(251,191,36,.28); }

    /* ── status bar ── */
    #status-bar {
      position: fixed; bottom: 0; left: 0; right: 0;
      background: var(--surface); border-top: 1px solid var(--border);
      padding: 6px 28px; display: flex; align-items: center; gap: 18px;
      font-size: .7rem; color: var(--muted);
    }
    #countdown { color: var(--label); font-weight: 600; }
  </style>
</head>
<body>

<header>
  <div class="logo">
    <div class="logo-icon">🚗</div>
    <div>
      <h1>Car Sales Dashboard</h1>
      <sub>Live data receiver</sub>
    </div>
  </div>
  <div class="header-right">
    <div class="live-badge"><span class="pulse"></span>LIVE</div>
    <button class="btn btn-ghost" onclick="clearData()">Clear Data</button>
  </div>
</header>

<main id="app"></main>

<div id="status-bar">
  <span>POST JSON array to <strong>/data</strong></span>
  <span>·</span>
  <span>Refresh in <span id="countdown">5</span>s</span>
  <span id="status-records"></span>
</div>

<script>
// ── Chart.js defaults ──────────────────────────────────────────────────────
Chart.defaults.color = '#64748b';
Chart.defaults.borderColor = '#2a3044';
Chart.defaults.font.family = "'Segoe UI', system-ui, sans-serif";
Chart.defaults.font.size = 11;

const PALETTE = ['#4f8ef7','#34d399','#fbbf24','#f87171','#a78bfa','#2dd4bf','#fb923c','#e879f9','#86efac','#93c5fd'];

// ── helpers ────────────────────────────────────────────────────────────────
const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

function fmtEur(v) {
  return new Intl.NumberFormat('de-DE',{style:'currency',currency:'EUR',maximumFractionDigits:0}).format(v);
}
function fmtNum(v, dec=1) {
  return Number(v).toFixed(dec);
}

function groupSum(rows, key, valKey) {
  const m = {};
  for (const r of rows) {
    const k = r[key] ?? '—';
    m[k] = (m[k] || 0) + parseFloat(r[valKey] || 0);
  }
  return m;
}
function groupCount(rows, key) {
  const m = {};
  for (const r of rows) { const k = r[key]??'—'; m[k]=(m[k]||0)+1; }
  return m;
}
function sortedEntries(obj, descending=true) {
  return Object.entries(obj).sort((a,b) => descending ? b[1]-a[1] : a[1]-b[1]);
}

// ── chart registry (destroy before re-create) ─────────────────────────────
const charts = {};
function mkChart(id, cfg) {
  if (charts[id]) charts[id].destroy();
  charts[id] = new Chart($(id), cfg);
}

// ── badge helpers ──────────────────────────────────────────────────────────
function channelBadge(ch) {
  const m={Online:'badge-blue',Fleet:'badge-purple',Dealer:'badge-green'};
  return `<span class="badge ${m[ch]||'badge-blue'}">${esc(ch??'—')}</span>`;
}
function segBadge(s) {
  return `<span class="badge ${s==='B2B'?'badge-purple':'badge-green'}">${esc(s??'—')}</span>`;
}

// ── render ─────────────────────────────────────────────────────────────────
function renderEmpty() {
  $('app').innerHTML = `
    <div class="empty">
      <div class="empty-icon">📭</div>
      <h2>Waiting for data…</h2>
      <p>POST a JSON array of car sales records to</p>
      <code>POST /data</code>
    </div>`;
}

function renderDashboard(rows, receivedAt) {
  // ── aggregate ──
  const totalRev   = rows.reduce((s,r) => s + parseFloat(r.Revenue||0), 0);
  const avgDisc    = rows.reduce((s,r) => s + parseFloat(r.Discount||0), 0) / rows.length;
  const avgCR      = rows.reduce((s,r) => s + parseFloat(r.Conversion_Rate||0), 0) / rows.length;

  const revByModel     = groupSum(rows,'Model','Revenue');
  const revByRegion    = groupSum(rows,'Region','Revenue');
  const revBySales     = groupSum(rows,'Salesperson','Revenue');
  const countByChannel = groupCount(rows,'Sales_Channel');
  const countBySeg     = groupCount(rows,'Customer_Segment');
  const countByCountry = groupCount(rows,'Country');

  // monthly revenue
  const monthly = {};
  for (const r of rows) {
    const d = r.Date ? String(r.Date).slice(0,7) : '?';
    monthly[d] = (monthly[d]||0) + parseFloat(r.Revenue||0);
  }
  const monthLabels = Object.keys(monthly).sort();
  const monthValues = monthLabels.map(k => monthly[k]);

  // ── inject HTML skeleton ──
  $('app').innerHTML = `
    <div class="section-head" style="margin-top:0">
      <span class="section-title">Overview</span>
      <span class="received-at">Received ${receivedAt} &nbsp;·&nbsp; ${rows.length} records</span>
    </div>

    <div class="kpi-grid">
      <div class="kpi" style="--kpi-color:#4f8ef7">
        <div class="kpi-label">Total Revenue</div>
        <div class="kpi-value" id="kpi-rev">—</div>
        <div class="kpi-sub">${rows.length} sales</div>
      </div>
      <div class="kpi" style="--kpi-color:#34d399">
        <div class="kpi-label">Avg Discount</div>
        <div class="kpi-value">${fmtNum(avgDisc)}%</div>
        <div class="kpi-sub">across all deals</div>
      </div>
      <div class="kpi" style="--kpi-color:#fbbf24">
        <div class="kpi-label">Avg Conversion Rate</div>
        <div class="kpi-value">${fmtNum(avgCR)}%</div>
        <div class="kpi-sub">per sale</div>
      </div>
      <div class="kpi" style="--kpi-color:#a78bfa">
        <div class="kpi-label">Top Channel</div>
        <div class="kpi-value" style="font-size:1rem;margin-top:4px" id="kpi-channel">—</div>
        <div class="kpi-sub" id="kpi-channel-sub"></div>
      </div>
    </div>

    <div class="section-head"><span class="section-title">Revenue Trends</span></div>
    <div class="chart-card">
      <div class="chart-title">Monthly Revenue</div>
      <div class="chart-wrap" style="height:200px"><canvas id="chart-monthly"></canvas></div>
    </div>

    <div class="section-head"><span class="section-title">Breakdown</span></div>
    <div class="chart-grid-3">
      <div class="chart-card">
        <div class="chart-title">Revenue by Model</div>
        <div class="chart-wrap" style="height:260px"><canvas id="chart-model"></canvas></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">Sales Channel</div>
        <div class="chart-wrap" style="height:260px"><canvas id="chart-channel"></canvas></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">B2B vs B2C</div>
        <div class="chart-wrap" style="height:260px"><canvas id="chart-seg"></canvas></div>
      </div>
    </div>

    <div class="section-head"><span class="section-title">Performance</span></div>
    <div class="chart-grid-2">
      <div class="chart-card">
        <div class="chart-title">Revenue by Salesperson</div>
        <div class="chart-wrap" style="height:260px"><canvas id="chart-sales"></canvas></div>
      </div>
      <div class="chart-card">
        <div class="chart-title">Revenue by Region</div>
        <div class="chart-wrap" style="height:260px"><canvas id="chart-region"></canvas></div>
      </div>
    </div>

    <div class="section-head"><span class="section-title">Sales by Country</span></div>
    <div class="chart-card">
      <div class="chart-title">Number of Sales per Country</div>
      <div class="chart-wrap" style="height:200px"><canvas id="chart-country"></canvas></div>
    </div>

    <div class="section-head"><span class="section-title">All Records</span></div>
    <div class="table-card">
      <div class="table-header">
        <span class="table-title">Sales Log</span>
        <span class="table-count">${rows.length} entries</span>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Date</th><th>Model</th><th>Country</th><th>Region</th>
              <th>Revenue</th><th>Discount</th><th>Channel</th>
              <th>Segment</th><th>Salesperson</th><th>Conv. Rate</th><th>VIN</th>
            </tr>
          </thead>
          <tbody id="table-body"></tbody>
        </table>
      </div>
    </div>`;

  // ── KPI values ──
  $('kpi-rev').textContent = fmtEur(totalRev);
  const topChannel = sortedEntries(countByChannel)[0];
  $('kpi-channel').textContent = topChannel[0];
  $('kpi-channel-sub').textContent = `${topChannel[1]} deals`;

  // ── status bar ──
  $('status-records') && ($('status-records').textContent = `· ${rows.length} records loaded`);

  // ── table rows ──
  $('table-body').innerHTML = rows.map(r => `
    <tr>
      <td>${esc(r.Date??'—')}</td>
      <td>${esc(r.Model??'—')}</td>
      <td>${esc(r.Country??'—')}</td>
      <td>${esc(r.Region??'—')}</td>
      <td style="color:#7ab3ff;font-weight:500">${fmtEur(parseFloat(r.Revenue||0))}</td>
      <td>${fmtNum(r.Discount)}%</td>
      <td>${channelBadge(r.Sales_Channel)}</td>
      <td>${segBadge(r.Customer_Segment)}</td>
      <td>${esc(r.Salesperson??'—')}</td>
      <td>${fmtNum(r.Conversion_Rate)}%</td>
      <td style="color:var(--muted);font-family:monospace;font-size:.72rem">${esc(r.VIN??'—')}</td>
    </tr>`).join('');

  // ── Chart: monthly revenue (line) ──
  mkChart('chart-monthly', {
    type: 'line',
    data: {
      labels: monthLabels,
      datasets: [{
        label: 'Revenue',
        data: monthValues,
        borderColor: '#4f8ef7',
        backgroundColor: 'rgba(79,142,247,.12)',
        borderWidth: 2,
        fill: true,
        tension: .35,
        pointRadius: 4,
        pointBackgroundColor: '#4f8ef7',
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { ticks: { callback: v => '€' + (v/1000).toFixed(0)+'k' }, grid: { color:'#2a3044' } },
        x: { grid: { display: false } }
      }
    }
  });

  // ── Chart: revenue by model (horizontal bar) ──
  const modelEntries = sortedEntries(revByModel);
  mkChart('chart-model', {
    type: 'bar',
    data: {
      labels: modelEntries.map(e=>e[0]),
      datasets: [{ data: modelEntries.map(e=>e[1]), backgroundColor: PALETTE, borderRadius: 4, borderSkipped: false }]
    },
    options: {
      indexAxis: 'y', responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { callback: v => '€'+(v/1000).toFixed(0)+'k' }, grid: { color:'#2a3044' } },
        y: { grid: { display: false } }
      }
    }
  });

  // ── Chart: sales channel (doughnut) ──
  const chEntries = sortedEntries(countByChannel);
  mkChart('chart-channel', {
    type: 'doughnut',
    data: {
      labels: chEntries.map(e=>e[0]),
      datasets: [{ data: chEntries.map(e=>e[1]), backgroundColor: ['#4f8ef7','#a78bfa','#34d399'], borderWidth: 0, hoverOffset: 6 }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      cutout: '62%',
      plugins: {
        legend: { position: 'bottom', labels: { padding: 14, boxWidth: 10 } }
      }
    }
  });

  // ── Chart: B2B vs B2C (doughnut) ──
  const segEntries = sortedEntries(countBySeg);
  mkChart('chart-seg', {
    type: 'doughnut',
    data: {
      labels: segEntries.map(e=>e[0]),
      datasets: [{ data: segEntries.map(e=>e[1]), backgroundColor: ['#a78bfa','#34d399'], borderWidth: 0, hoverOffset: 6 }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      cutout: '62%',
      plugins: {
        legend: { position: 'bottom', labels: { padding: 14, boxWidth: 10 } }
      }
    }
  });

  // ── Chart: revenue by salesperson (horizontal bar) ──
  const salesEntries = sortedEntries(revBySales);
  mkChart('chart-sales', {
    type: 'bar',
    data: {
      labels: salesEntries.map(e=>e[0]),
      datasets: [{ data: salesEntries.map(e=>e[1]), backgroundColor: '#2dd4bf', borderRadius: 4, borderSkipped: false }]
    },
    options: {
      indexAxis: 'y', responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { callback: v => '€'+(v/1000).toFixed(0)+'k' }, grid: { color:'#2a3044' } },
        y: { grid: { display: false } }
      }
    }
  });

  // ── Chart: revenue by region (bar) ──
  const regionEntries = sortedEntries(revByRegion);
  mkChart('chart-region', {
    type: 'bar',
    data: {
      labels: regionEntries.map(e=>e[0]),
      datasets: [{ data: regionEntries.map(e=>e[1]), backgroundColor: ['#4f8ef7','#fbbf24','#34d399','#f87171'], borderRadius: 5, borderSkipped: false }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { ticks: { callback: v => '€'+(v/1000).toFixed(0)+'k' }, grid: { color:'#2a3044' } },
        x: { grid: { display: false } }
      }
    }
  });

  // ── Chart: sales count by country (bar) ──
  const countryEntries = sortedEntries(countByCountry);
  mkChart('chart-country', {
    type: 'bar',
    data: {
      labels: countryEntries.map(e=>e[0]),
      datasets: [{ data: countryEntries.map(e=>e[1]), backgroundColor: PALETTE[0], borderRadius: 4, borderSkipped: false }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        y: { ticks: { stepSize: 1 }, grid: { color:'#2a3044' } },
        x: { grid: { display: false }, ticks: { maxRotation: 35 } }
      }
    }
  });
}

// ── data fetch ─────────────────────────────────────────────────────────────
let lastReceivedAt = null;

async function fetchData() {
  try {
    const res = await fetch('/api/latest');
    const json = await res.json();

    // Only re-render when data actually changed
    if (json.received_at === lastReceivedAt) return;
    lastReceivedAt = json.received_at;

    if (json.data && Array.isArray(json.data) && json.data.length > 0) {
      renderDashboard(json.data, json.received_at);
    } else if (json.data && !Array.isArray(json.data)) {
      renderDashboard([json.data], json.received_at);
    } else {
      renderEmpty();
    }
  } catch(e) { /* network blip */ }
}

async function clearData() {
  await fetch('/api/clear', { method: 'POST' });
  lastReceivedAt = null;
  renderEmpty();
}

// ── countdown ──────────────────────────────────────────────────────────────
let countdown = 5;
setInterval(() => {
  countdown--;
  $('countdown').textContent = countdown;
  if (countdown <= 0) { countdown = 5; fetchData(); }
}, 1000);

fetchData();
</script>

<div id="status-bar">
  <span>POST JSON array to <strong>/data</strong></span>
  <span>·</span>
  <span>Refresh in <span id="countdown">5</span>s</span>
  <span id="status-records"></span>
</div>
</body>
</html>"""


# ── Routes ─────────────────────────────────────────────────────────────────

@app.get("/")
def index():
    return Response(HTML, mimetype='text/html')


@app.post("/data")
def receive_data():
    ct = request.content_type or ""
    if "application/json" in ct:
        try:
            payload = request.get_json(force=True)
        except Exception:
            payload = request.get_data(as_text=True)
    else:
        try:
            payload = request.get_json(force=True)
        except Exception:
            payload = request.get_data(as_text=True)

    last_entry["received_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    last_entry["data"] = payload
    count = len(payload) if isinstance(payload, list) else 1
    return jsonify({"status": "ok", "records": count}), 201


@app.get("/api/latest")
def api_latest():
    return jsonify(last_entry)


@app.post("/api/clear")
def api_clear():
    last_entry["received_at"] = None
    last_entry["data"] = None
    return jsonify({"status": "cleared"}), 200


@app.get("/health")
def health():
    return "ok", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
