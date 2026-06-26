import json
import logging

logger = logging.getLogger(__name__)

PRODUCT_TABLE_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <meta content='connect-src "none"' http-equiv='Content-Security-Policy'>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <title>Pricing opportunities Analysis</title>
    <style>
        :root {
            --bg-color: #ffffff;
            --border: #e2e8f0;
            --t1: #0f172a;
            --t2: #475569;
            --t3: #64748b;
            --primary: #2563eb;
            --red: #ef4444;
            --hover: #f8fafc;
        }
        body {
            font-family: 'Poppins', system-ui, -apple-system, sans-serif;
            background-color: var(--bg-color);
            color: var(--t1);
            margin: 0;
            padding: 8px;
            box-sizing: border-box;
            font-size: 13px;
        }
        .panel-lead {
            font-size: 13px;
            font-weight: 500;
            margin-bottom: 16px;
            color: var(--t1);
        }
        .kpi-row {
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
        }
        .kpi {
            flex: 1;
            background: #ffffff;
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 14px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.04);
        }
        .kpi-label {
            font-size: 10px;
            text-transform: uppercase;
            color: var(--t3);
            font-weight: 700;
            letter-spacing: 0.05em;
        }
        .kpi-value {
            font-size: 20px;
            font-weight: 700;
            color: var(--t1);
            margin: 6px 0 4px;
            line-height: 1.2;
        }
        .kpi-value.red {
            color: var(--red);
        }
        .kpi-sub {
            font-size: 11px;
            color: var(--t3);
        }
        .table-container {
            overflow-x: auto;
        }
        .pa-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12.5px;
        }
        .pa-table th {
            font-size: 9.5px;
            font-weight: 700;
            letter-spacing: 0.07em;
            text-transform: uppercase;
            color: var(--t3);
            text-align: left;
            padding: 10px 12px;
            border-bottom: 1px solid var(--border);
            white-space: nowrap;
        }
        .pa-table th.num,
        .pa-table td.num {
            text-align: right;
        }
        .pa-table td {
            padding: 12px;
            border-bottom: 1px solid var(--border);
            color: var(--t1);
            white-space: nowrap;
        }
        .pa-table tbody tr {
            cursor: pointer;
            transition: background 0.15s;
        }
        .pa-table tbody tr:hover {
            background: var(--hover);
        }
        .pa-table tbody tr:last-child td {
            border-bottom: none;
        }
        .pa-table tbody tr.top td {
            background: rgba(37, 99, 235, 0.04);
        }
        .pa-rank {
            display: inline-flex;
            width: 22px;
            height: 22px;
            border-radius: 50%;
            background: #f1f5f9;
            color: var(--t2);
            font-size: 11px;
            font-weight: 700;
            align-items: center;
            justify-content: center;
        }
        .pa-table tr.top .pa-rank {
            background: var(--primary);
            color: #ffffff;
        }
        .pa-prod {
            font-weight: 600;
        }
        .pa-neg {
            color: var(--red);
            font-weight: 600;
        }
        .pa-pos {
            font-weight: 600;
        }
        .panel-line {
            color: var(--t3);
            font-size: 11.5px;
            margin-top: 12px;
        }
        .btn-download {
            background: transparent;
            border: 1px solid #00a4e4;
            color: #002f6c;
            padding: 5px 10px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-download:hover {
            background-color: #00a4e4;
            color: #ffffff;
        }
    </style>
</head>
<body>
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 16px;">
            <div class="panel-lead" style="margin-bottom: 0;">Here’s what I found — five products where price increases drove household attrition over the past 12 weeks.</div>
            <button class="btn-download" onclick="downloadCSV()">Download CSV</button>
        </div>
    
    <div class="kpi-row" id="kpi-summary">
        <!-- Dynamically Populated KPI Cards -->
    </div>

    <div class="table-container">
        <table class="pa-table">
            <thead>
                <tr>
                    <th></th>
                    <th>Product</th>
                    <th class="num">Avg price Δ · 12w</th>
                    <th class="num">Households lost</th>
                    <th class="num">Volume Δ</th>
                    <th class="num">Lapsed-buyer pool (HH)</th>
                </tr>
            </thead>
            <tbody id="table-body">
                <!-- Dynamically Injected Rows -->
            </tbody>
        </table>
    </div>
    
    <div class="panel-line">Ranked by verified households lost where price was the leading driver — volume-only declines are excluded. Tap a row to take it into phase 2.</div>

    <script>
        const rawData = window.INJECTED_DATA || [];
        const data = rawData.length > 0 ? rawData : [
            { rank: 1, product_name: "Tropicana Pure Premium 52oz", price_change: "+14.2%", households_lost: "−412K", lost_households_pct: -9.8, volume_change: -6.4, pool_size: 412400 },
            { rank: 2, product_name: "Quaker Instant Oatmeal 10ct", price_change: "+11.5%", households_lost: "−298K", lost_households_pct: -7.4, volume_change: -5.2, pool_size: 298100 },
            { rank: 3, product_name: "Gatorade Thirst Quencher 28oz", price_change: "+9.0%", households_lost: "−244K", lost_households_pct: -5.9, volume_change: -4.8, pool_size: 243700 },
            { rank: 4, product_name: "Lay's Classic Party Size", price_change: "+12.1%", households_lost: "−201K", lost_households_pct: -5.1, volume_change: -3.9, pool_size: 200900 },
            { rank: 5, product_name: "Lipton Iced Tea 12pk", price_change: "+8.4%", households_lost: "−156K", lost_households_pct: -4.2, volume_change: -3.1, pool_size: 156300 }
        ];

        function downloadCSV() {
            let csvContent = "data:text/csv;charset=utf-8,";
            csvContent += "Rank,Product,Price Change,Households Lost,Volume Change,Lapsed Pool\n";
            data.forEach((item, index) => {
                const r = index + 1;
                const p = item.product_name || '';
                const pr = item.price_change || '';
                const hh = item.households_lost || item.lost_households_count || '';
                const v = item.volume_change || '';
                const pool = item.pool_size || item.lapsed_pool || '';
                csvContent += `"${r}","${p}","${pr}","${hh}","${v}","${pool}"\n`;
            });
            const encodedUri = encodeURI(csvContent);
            const link = document.createElement("a");
            link.setAttribute("href", encodedUri);
            link.setAttribute("download", "pricing_opportunities.csv");
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }

        const topItem = data[0] || {};
        const kpiSummary = document.getElementById('kpi-summary');
        
        const topName = topItem.product_name || "Tropicana Pure Premium 52oz";
        const topPrice = topItem.price_change || "+14.2%";
        const topLoss = topItem.households_lost || (topItem.lost_households_count ? topItem.lost_households_count : "−412K");
        const topPct = topItem.lost_households_pct ? `${topItem.lost_households_pct}%` : "−9.8%";
        const topPool = topItem.pool_size ? topItem.pool_size.toLocaleString() : (topItem.lapsed_pool ? topItem.lapsed_pool.toLocaleString() : "412,400");

        kpiSummary.innerHTML = `
            <div class="kpi">
                <div class="kpi-label">Top product</div>
                <div class="kpi-value" style="font-size:17px;">${topName}</div>
                <div class="kpi-sub">${topPrice} avg price · 12w</div>
            </div>
            <div class="kpi">
                <div class="kpi-label">Households lost</div>
                <div class="kpi-value red">${topLoss}</div>
                <div class="kpi-sub">${topPct} of buying households</div>
            </div>
            <div class="kpi">
                <div class="kpi-label">Lapsed-buyer pool (HH)</div>
                <div class="kpi-value">${topPool}</div>
                <div class="kpi-sub">verified · audience-ready</div>
            </div>
        `;

        const tbody = document.getElementById('table-body');
        data.forEach((item, index) => {
            const tr = document.createElement('tr');
            tr.className = index === 0 ? 'top' : '';
            
            const pName = item.product_name || "Unknown";
            const pPrice = item.price_change || "+14.2%";
            const pLoss = item.households_lost || (item.lost_households_count ? item.lost_households_count : "−412K");
            const pPct = item.lost_households_pct ? `${item.lost_households_pct}%` : "−9.8%";
            const pVol = item.volume_change ? `${item.volume_change}%` : "−6.4%";
            const pPool = item.pool_size ? item.pool_size.toLocaleString() : (item.lapsed_pool ? item.lapsed_pool.toLocaleString() : "412,400");

            tr.innerHTML = `
                <td><span class="pa-rank">${index + 1}</span></td>
                <td class="pa-prod">${pName}</td>
                <td class="num pa-pos">${pPrice}</td>
                <td class="num pa-neg">${pLoss} <span style="color:var(--t3);font-weight:400">(${pPct})</span></td>
                <td class="num pa-neg">${pVol}</td>
                <td class="num">${pPool}</td>
            `;

            tr.onclick = () => {
                window.parent.postMessage({
                    type: 'USER_ACTION',
                    actionId: 'product_selected',
                    payload: { product: pName }
                }, '*');
            };

            tbody.appendChild(tr);
        });
    </script>
</body>
</html>
"""

SIZING_DASHBOARD_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang='en'>
<head>
  <meta charset='UTF-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1.0'>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --primary: #4A90E2;
      --secondary: #FF9B40;
      --up: #7B3FA0;
      --bg: #EBEBEB;
      --surface: #FFFFFF;
      --border: #E4E4E4;
      --t1: #212121;
      --t2: #334155;
      --t3: #787885;
      --t4: #B9B9B9;
      --green: #00B929;
    }
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Inter', sans-serif;
      background: var(--bg);
      color: var(--t1);
      font-size: 13px;
      line-height: 1.5;
      padding: 16px;
    }
    .wrapper {
      display: flex;
      flex-direction: column;
      gap: 20px;
      max-width: 960px;
      margin: 0 auto;
    }

    /* Steps Separator */
    .steps-sep {
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--t3);
      font-size: 12.5px;
      font-weight: 500;
      margin-left: 4px;
    }

    /* Panel Card */
    .panel {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 24px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .panel-lead {
      font-size: 15px;
      font-weight: 700;
      color: var(--t1);
      margin-bottom: 20px;
    }
    .kpi-row {
      display: flex;
      gap: 16px;
      margin-bottom: 20px;
    }
    .kpi {
      flex: 1;
      background: #F8FAFC;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 18px 16px;
    }
    .kpi-label { font-size: 10px; font-weight: 700; text-transform: uppercase; color: var(--t3); letter-spacing: 0.05em; margin-bottom: 6px; }
    .kpi-value { font-size: 32px; font-weight: 800; letter-spacing: -0.03em; margin: 4px 0; }
    .kpi-value.det { color: var(--t1); }
    .kpi-value.prob { color: #FF6F00; }
    .kpi-value.total { color: #10B981; }
    .kpi-sub { font-size: 11.5px; color: var(--t3); margin-top: 4px; }
    .panel-line { font-size: 13.5px; color: var(--t2); line-height: 1.6; }

    /* Recommended Next Steps */
    .followup-section { margin-top: 24px; display: flex; flex-direction: column; gap: 12px; }
    .followup-label { font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--t3); letter-spacing: 0.06em; }
    .chip-row { display: flex; gap: 10px; flex-wrap: wrap; }
    .chip {
      padding: 9px 20px;
      border-radius: 24px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      border: 1px solid #CBD5E1;
      background: var(--surface);
      color: var(--t2);
      transition: all 0.2s;
    }
    .chip.go-chip {
      background: #FF6F00;
      border-color: #FF6F00;
      color: #FFFFFF;
      box-shadow: 0 2px 6px rgba(255,111,0,0.25);
    }
    .chip.go-chip:hover { opacity: 0.9; }
    .chip:hover:not(.go-chip) { background: #F1F5F9; }
  </style>
<script>window.INJECTED_DATA = {};</script>
</head>
<body>
  <div class="wrapper">
    <!-- Steps Trace -->
    <div class="steps-sep">
      <span>▸</span> Worked through 2 steps
    </div>

    <!-- Main Sizing Panel -->
    <div class="panel">
      <div class="panel-lead">All set — your audience is built, scaled, and sized.</div>
      <div class="kpi-row">
        <div class="kpi"><div class="kpi-label">Built · verified seed</div><div class="kpi-value det" id="kDet">412.4<small style="font-size:75%">K</small></div><div class="kpi-sub" id="kSubDet">lapsed Tropicana Pure Premium HH</div></div>
        <div class="kpi"><div class="kpi-label">Scaled · Complete</div><div class="kpi-value prob">3.1<small style="font-size:75%">M</small></div><div class="kpi-sub">ProScore lookalikes</div></div>
        <div class="kpi"><div class="kpi-label">Sized · addressable reach</div><div class="kpi-value total" id="kReach">2.86<small style="font-size:75%">M</small></div><div class="kpi-sub">ready to activate</div></div>
      </div>
      <div class="panel-line" id="panel-desc">
        From one question to an audience that’s ready to go: <b>412,400</b> verified lapsed Tropicana Pure Premium households, expanded to <b>3.1M</b> with ProScore, with <b>2.86M</b> reachable for activation. Pick a destination and we’re off.
      </div>
    </div>

    <!-- Recommended Next Steps -->
    <div class="followup-section">
      <div class="followup-label">Recommended next steps</div>
      <div class="chip-row">
        <button class="chip go-chip" onclick="activatePartner('LiveRamp,Google')">🚀 Activate</button>
        <button class="chip" onclick="profileAudience()">Profile it</button>
      </div>
    </div>
  </div>

  <script>
    const data = window.INJECTED_DATA || {};
    const pName = data.product_name || "Tropicana Pure Premium";
    const seedCount = data.seed_count || 412400;
    const scaledCount = data.scaled_size || "3.1M";
    const reachCount = data.reach_count || "2.86M";

    if (data.product_name) {
      document.getElementById('kSubDet').textContent = `lapsed ${pName} HH`;
      document.getElementById('panel-desc').innerHTML = `From one question to an audience that’s ready to go: <b>${seedCount.toLocaleString()}</b> verified lapsed ${pName} households, expanded to <b>${scaledCount}</b> with ProScore, with <b>${reachCount}</b> reachable for activation. Pick a destination and we’re off.`;
    }

    function activatePartner(partners) {
      window.parent.postMessage({
        type: 'USER_ACTION',
        actionId: 'btn_activate',
        payload: { partners: partners.split(',') }
      }, '*');
    }
    function profileAudience() {
      window.parent.postMessage({ type: 'USER_ACTION', actionId: 'profile_audience', payload: {} }, '*');
    }
  </script>
</body>
</html>
"""

EXECUTION_CHAIN_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <title>Execution Pipeline</title>
    <style>
        :root {
            --bg-color: #ffffff;
            --border: #e2e8f0;
            --t1: #0f172a;
            --t3: #64748b;
            --primary: #2563eb;
            --green: #10b981;
        }
        body {
            font-family: 'Poppins', system-ui, sans-serif;
            margin: 0; padding: 12px;
        }
        .chain-box {
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 16px;
            background: #f8fafc;
        }
        .chain-lead {
            font-size: 13px; font-weight: 700; color: var(--t1);
            margin-bottom: 16px;
        }
        .chain-row {
            display: flex; align-items: center; gap: 12px;
        }
        .chain-step {
            flex: 1; background: #fff;
            border: 2px solid var(--border);
            border-radius: 8px; padding: 12px;
            text-align: center;
        }
        .chain-step.ok { border-color: var(--green); }
        .chain-step.on { border-color: var(--primary); }
        .chain-name { font-weight: 700; font-size: 12px; color: var(--t1); }
        .chain-sub { font-size: 10.5px; color: var(--t3); margin-top: 4px; }
    </style>
</head>
<body>
    <div class="chain-box">
        <div class="chain-lead">Here’s how I’ll get this done — three steps handing results straight to the next.</div>
        <div class="chain-row">
            <div class="chain-step ok">
                <div class="chain-name">1 · Build</div>
                <div class="chain-sub">verified lapsed-buyer audience</div>
            </div>
            <div style="color:var(--t3);font-weight:700">→</div>
            <div class="chain-step ok">
                <div class="chain-name">2 · Scale</div>
                <div class="chain-sub">ProScore expansion</div>
            </div>
            <div style="color:var(--t3);font-weight:700">→</div>
            <div class="chain-step on" id="s3">
                <div class="chain-name">3 · Size</div>
                <div class="chain-sub">addressable reach</div>
            </div>
        </div>
    </div>
    <script>
        const stepNum = (window.INJECTED_DATA || {}).step || 3;
        if (stepNum >= 4) {
            document.getElementById('s3').className = 'chain-step ok';
        }
    </script>
</body>
</html>
"""

DEMOGRAPHIC_PROFILE_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <title>Demographic Profile</title>
    <style>
        body {
            font-family: 'Poppins', system-ui, sans-serif;
            margin: 0; padding: 12px;
            color: #0f172a; background: #ffffff;
            font-size: 12.5px; line-height: 1.5;
        }
        .panel {
            border: 1px solid #e2e8f0;
            border-radius: 12px; padding: 20px;
            display: flex; flex-direction: column; gap: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.02);
        }
        .dp-title { font-weight: 700; font-size: 15px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: baseline; }
        .dp-title small { font-weight: 400; font-size: 11.5px; color: #64748b; }
        .stat-strip {
            display: flex; gap: 14px;
        }
        .stat-card {
            flex: 1; background: #f8fafc; border: 1px solid #e2e8f0;
            border-radius: 10px; padding: 12px 16px;
        }
        .stat-label { font-size: 10px; text-transform: uppercase; color: #64748b; font-weight: 700; }
        .stat-num { font-size: 22px; font-weight: 800; margin: 4px 0; color: #0f172a; }
        .stat-sub { font-size: 10.5px; color: #ff6f00; font-weight: 600; background: #fff7ed; padding: 2px 8px; border-radius: 10px; display: inline-block; border: 1px solid #fed7aa; }
        
        .dp-section {
            border-top: 1px solid #f1f5f9; padding-top: 20px;
        }
        
        .dp-bar-row {
            display: flex; align-items: center; gap: 16px; margin-bottom: 10px;
        }
        .dp-lbl { width: 120px; font-weight: 600; font-size: 12px; color: #334155; }
        .dp-track { flex: 1; background: #f1f5f9; height: 18px; border-radius: 9px; overflow: hidden; display: flex; }
        .dp-fill { background: #ff6f00; height: 100%; border-radius: 9px; }
        .dp-fill.muted { background: #94a3b8; }
        .dp-pct { width: 45px; text-align: right; font-weight: 700; font-size: 12px; }
        .dp-idx { width: 55px; text-align: center; font-size: 11px; font-weight: 700; padding: 2px 6px; border-radius: 6px; }
        .dp-idx.over { background: #fff7ed; color: #c2410c; border: 1px solid #fed7aa; }
        .dp-idx.under { background: #f8fafc; color: #64748b; border: 1px solid #e2e8f0; }

        .two-col {
            display: flex; gap: 24px; align-items: flex-start;
        }
        .col-left { flex: 3; }
        .col-right { flex: 2; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; }
        
        .dma-row { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; border-bottom: 1px solid #f1f5f9; font-size: 12px; }
        .dma-row:last-child { border-bottom: none; }
        .dma-name { font-weight: 600; color: #334155; }
        
        .gen-rail { margin-top: 20px; }
        .gen-bar { display: flex; height: 28px; border-radius: 8px; overflow: hidden; gap: 2px; }
        .gen-seg { display: flex; flex-direction: column; justify-content: center; align-items: center; color: white; font-weight: 700; font-size: 10px; line-height: 1; }
        .gen-seg span { font-size: 8.5px; opacity: 0.9; }
        
        .followup-section { margin-top: 12px; padding-top: 16px; border-top: 1px solid #e2e8f0; }
        .followup-label { font-size: 11px; text-transform: uppercase; color: #64748b; font-weight: 700; margin-bottom: 12px; }
        .chip-row { display: flex; gap: 10px; }
        .chip {
            background: #f8fafc; border: 1px solid #cbd5e1; padding: 10px 24px; border-radius: 24px;
            font-weight: 600; font-size: 13px; cursor: pointer; color: #334155;
            transition: all 0.2s ease;
        }
        .chip:hover { background: #f1f5f9; border-color: #94a3b8; }
        .chip.go-chip { background: #ff6f00; color: white; border-color: #ff6f00; }
        .chip.go-chip:hover { background: #e66400; }
    </style>
</head>
<body>
    <div class="panel">
        <div class="dp-title">Audience Profile · 3.1M Households</div>
        <div class="stat-strip">
            <div class="stat-card"><div class="stat-label">Median Age</div><div class="stat-num">47 yrs</div><div class="stat-sub">idx 124</div></div>
            <div class="stat-card"><div class="stat-label">Median Income</div><div class="stat-num">$78K</div><div class="stat-sub">+6 vs US</div></div>
            <div class="stat-card"><div class="stat-label">Avg HH Size</div><div class="stat-num">3.1</div><div class="stat-sub">+0.6 vs US</div></div>
            <div class="stat-card"><div class="stat-label">Kids in HH</div><div class="stat-num">52%</div><div class="stat-sub">+38 vs base</div></div>
        </div>

        <div class="dp-section">
            <div class="dp-title">Age and life stage <small>Audience curve vs US baseline</small></div>
            <svg viewBox="0 0 620 180" style="width:100%; height:auto;">
                <line x1="30" y1="150" x2="590" y2="150" stroke="#e2e8f0" stroke-width="1"/>
                <line x1="30" y1="90" x2="590" y2="90" stroke="#e2e8f0" stroke-width="1" stroke-dasharray="3 3"/>
                <line x1="30" y1="30" x2="590" y2="30" stroke="#e2e8f0" stroke-width="1" stroke-dasharray="3 3"/>
                <text x="76" y="168" text-anchor="middle" font-size="11" fill="#64748b">18–24</text>
                <text x="170" y="168" text-anchor="middle" font-size="11" fill="#64748b">25–34</text>
                <text x="264" y="168" text-anchor="middle" font-size="11" fill="#64748b" font-weight="700">35–44</text>
                <text x="358" y="168" text-anchor="middle" font-size="11" fill="#64748b" font-weight="700">45–54</text>
                <text x="452" y="168" text-anchor="middle" font-size="11" fill="#64748b">55–64</text>
                <text x="546" y="168" text-anchor="middle" font-size="11" fill="#64748b">65+</text>
                <path d="M76,120 C170,115 264,110 358,112 452,115 546,118" fill="none" stroke="#94a3b8" stroke-width="2" stroke-dasharray="4 4"/>
                <path d="M76,140 C170,105 264,30 358,45 452,100 546,125" fill="none" stroke="#ff6f00" stroke-width="3.5"/>
                <circle cx="264" cy="42" r="5" fill="#ff6f00" stroke="#ffffff" stroke-width="2"/>
                <circle cx="358" cy="45" r="5" fill="#ff6f00" stroke="#ffffff" stroke-width="2"/>
                <rect x="270" y="12" width="94" height="22" rx="11" fill="#ff6f00"/>
                <text x="317" y="27" text-anchor="middle" font-size="10.5" font-weight="700" fill="#ffffff">+30 vs baseline</text>
            </svg>
        </div>

        <div class="dp-section">
            <div class="dp-title">Household income <small>Distribution and index vs US baseline</small></div>
            <div class="dp-bar-row"><div class="dp-lbl">&lt; $50K</div><div class="dp-track"><div class="dp-fill muted" style="width:18%"></div></div><div class="dp-pct">18%</div><div class="dp-idx under">75</div></div>
            <div class="dp-bar-row"><div class="dp-lbl">$50 – 75K</div><div class="dp-track"><div class="dp-fill" style="width:38%"></div></div><div class="dp-pct">24%</div><div class="dp-idx over">114</div></div>
            <div class="dp-bar-row"><div class="dp-lbl">$75 – 100K</div><div class="dp-track"><div class="dp-fill" style="width:30%"></div></div><div class="dp-pct">22%</div><div class="dp-idx over">102</div></div>
            <div class="dp-bar-row"><div class="dp-lbl">$100 – 150K</div><div class="dp-track"><div class="dp-fill" style="width:28%"></div></div><div class="dp-pct">21%</div><div class="dp-idx over">108</div></div>
            <div class="dp-bar-row"><div class="dp-lbl">$150K+</div><div class="dp-track"><div class="dp-fill muted" style="width:15%"></div></div><div class="dp-pct">15%</div><div class="dp-idx under">95</div></div>
        </div>

        <div class="dp-section two-col">
            <div class="col-left">
                <div class="dp-title">Geography <small>State density concentration</small></div>
                <div style="background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:24px; text-align:center; font-weight:600; color:#ff6f00; font-size:13px;">
                    Southern &amp; Midwestern DMA Concentration: TX, GA, FL, IL, AZ Highly Active
                </div>
            </div>
            <div class="col-right">
                <div style="font-weight:700; font-size:11px; color:#64748b; text-transform:uppercase; margin-bottom:10px;">Top DMAs by Reach</div>
                <div class="dma-row"><span class="dma-name">Dallas-Ft Worth</span><span>1.4M <b class="dp-idx over">+32</b></span></div>
                <div class="dma-row"><span class="dma-name">Houston</span><span>1.2M <b class="dp-idx over">+28</b></span></div>
                <div class="dma-row"><span class="dma-name">Atlanta</span><span>1.1M <b class="dp-idx over">+24</b></span></div>
                <div class="dma-row"><span class="dma-name">Chicago</span><span>1.1M <b class="dp-idx over">+9</b></span></div>
            </div>
        </div>

        <div class="dp-section">
            <div class="dp-title">Household composition &amp; Generation mix</div>
            <div class="dp-bar-row"><div class="dp-lbl">Couple + 2 kids</div><div class="dp-track"><div class="dp-fill" style="width:60%"></div></div><div class="dp-pct">30%</div><div class="dp-idx over">+62</div></div>
            <div class="dp-bar-row"><div class="dp-lbl">Couple + 1 kid</div><div class="dp-track"><div class="dp-fill" style="width:44%"></div></div><div class="dp-pct">22%</div><div class="dp-idx over">+34</div></div>
            <div class="dp-bar-row"><div class="dp-lbl">Couple, no kids</div><div class="dp-track"><div class="dp-fill muted" style="width:48%"></div></div><div class="dp-pct">24%</div><div class="dp-idx under">idx 92</div></div>
            <div class="dp-bar-row"><div class="dp-lbl">Single parent</div><div class="dp-track"><div class="dp-fill" style="width:18%"></div></div><div class="dp-pct">9%</div><div class="dp-idx over">+18</div></div>
            <div class="dp-bar-row"><div class="dp-lbl">Single adult</div><div class="dp-track"><div class="dp-fill muted" style="width:16%"></div></div><div class="dp-pct">8%</div><div class="dp-idx under">idx 71</div></div>

            <div class="gen-rail">
                <div style="font-size:10.5px; font-weight:700; color:#64748b; text-transform:uppercase; margin-bottom:6px;">Generation Mix</div>
                <div class="gen-bar">
                    <div class="gen-seg" style="flex:14; background:#94a3b8;">14%<span>Gen Z</span></div>
                    <div class="gen-seg" style="flex:24; background:#6366f1;">24%<span>Millennial</span></div>
                    <div class="gen-seg" style="flex:38; background:#ff6f00;">38%<span>Gen X (Lead)</span></div>
                    <div class="gen-seg" style="flex:18; background:#10b981;">18%<span>Boomer</span></div>
                    <div class="gen-seg" style="flex:6; background:#cbd5e1; color:#334155;">6%<span>Silent</span></div>
                </div>
            </div>
        </div>

        <div class="followup-section">
            <div class="followup-label">Recommended next steps</div>
            <div class="chip-row">
                <button class="chip go-chip" onclick="activatePartner('LiveRamp,Google')">🚀 Activate</button>
            </div>
        </div>
    </div>
    <script>
        function activatePartner(partners) {
            window.parent.postMessage({
                type: 'USER_ACTION',
                actionId: 'btn_activate',
                payload: { partners: partners.split(',') }
            }, '*');
        }
    </script>
</body>
</html>
"""

COMBINED_ACTIVATION_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang='en'>
<head>
  <meta charset='UTF-8'>
  <meta name='viewport' content='width=device-width, initial-scale=1.0'>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  <style>
    :root {
      --primary: #4A90E2;
      --secondary: #FF9B40;
      --up: #7B3FA0;
      --bg: #EBEBEB;
      --surface: #FFFFFF;
      --border: #E4E4E4;
      --t1: #212121;
      --t2: #334155;
      --t3: #787885;
      --t4: #B9B9B9;
      --green: #00B929;
      --red: #FF2D2E;
      --green-bg: rgba(0, 185, 41, 0.08);
      --purple-bg: rgba(123, 63, 160, 0.08);
      --purple-border: #D8B4E2;
      --purple-text: #7B3FA0;
    }
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Inter', sans-serif;
      background: transparent;
      color: var(--t1);
      font-size: 13px;
      line-height: 1.5;
      padding: 4px;
    }
    .wrapper {
      display: flex;
      flex-direction: column;
      gap: 20px;
      width: 100%;
      max-width: 100%;
    }

    /* 1. Chain Tracker */
    .chain-container {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 16px 20px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .chain-title {
      font-size: 13.5px;
      font-weight: 700;
      color: var(--t1);
      margin-bottom: 12px;
    }
    .chain {
      display: flex;
      align-items: center;
      justify-content: space-between;
    }
    .chain-step {
      display: flex;
      flex-direction: column;
      border: 1px solid var(--border);
      padding: 10px 16px;
      border-radius: 10px;
      flex: 1;
      background: #FAFAFA;
      opacity: 0.5;
    }
    .chain-step.ok {
      opacity: 1;
      background: var(--green-bg);
      border-color: #A3E4B5;
    }
    .chain-step.on {
      opacity: 1;
      background: #FFFFFF;
      border-color: var(--primary);
      box-shadow: 0 2px 8px rgba(74,144,226,0.15);
    }
    .chain-head { display: flex; align-items: center; justify-content: space-between; }
    .chain-name { font-size: 11.5px; font-weight: 700; color: var(--t1); }
    .chain-sub { font-size: 10px; color: var(--t3); margin-top: 2px; }
    .chain-id { font-size: 10.5px; font-family: monospace; color: var(--green); font-weight: 600; margin-top: 4px; }
    .chain-arrow { color: var(--t4); font-weight: bold; font-size: 16px; padding: 0 12px; }

    /* 2. Audience Tile */
    .aud-tile {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.04);
      overflow: hidden;
    }
    .aud-tile-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 20px;
      border-bottom: 1px solid var(--border);
      background: #FAFAFA;
    }
    .aud-tile-title {
      font-size: 15px;
      font-weight: 700;
      color: var(--t1);
    }
    .aud-tile-head-right {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    .aud-tile-hint {
      font-size: 11.5px;
      color: var(--t3);
      font-style: italic;
    }
    .aud-status {
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.06em;
      padding: 5px 12px;
      border-radius: 20px;
      text-transform: uppercase;
      background: #F3E8FF;
      color: #7E22CE;
      border: 1px solid #E9D5FF;
    }
    .pin-btn {
      width: 28px;
      height: 28px;
      border-radius: 6px;
      border: 1px solid var(--border);
      background: #FFFFFF;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      color: var(--t3);
    }
    .pin-btn:hover { background: #F1F5F9; color: var(--t1); }

    .aud-tile-body {
      padding: 16px 20px;
      display: flex;
      flex-direction: column;
    }
    .aud-grp {
      display: grid;
      grid-template-columns: 140px 1fr;
      align-items: center;
      padding: 10px 0;
      border-bottom: 1px solid #F1F5F9;
    }
    .aud-grp:last-of-type { border-bottom: none; }
    .aud-grp-label {
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      color: var(--t3);
      letter-spacing: 0.05em;
    }
    .aud-pills {
      display: flex;
      align-items: center;
      flex-wrap: wrap;
      gap: 8px;
    }
    .pill {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 5px 12px;
      border-radius: 20px;
      font-size: 12px;
      font-weight: 500;
      border: 1px solid;
    }
    .pill.type { background: #FDF4FF; color: #86198F; border-color: #FAE8FF; }
    .pill.scope-product { background: #EFF6FF; color: #1E3A8A; border-color: #DBEAFE; }
    .pill.scope-time { background: #F0FDF4; color: #166534; border-color: #DCFCE7; }
    .pill.attribute { background: #FDF4FF; color: #86198F; border-color: #FAE8FF; }
    .pill.missing { background: #FFFBEB; color: #B45309; border: 1px dashed #FDE68A; cursor: pointer; }
    .pill-add {
      width: 26px;
      height: 26px;
      border-radius: 50%;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border: 1px solid #CBD5E1;
      background: #F8FAFC;
      color: var(--t3);
      cursor: pointer;
      font-weight: bold;
    }
    .pill-add.danger {
      border: 1px dashed #FCA5A5;
      color: #EF4444;
      background: #FEF2F2;
    }

    .aud-result-strip {
      background: #F0FDF4;
      border: 1px solid #DCFCE7;
      border-radius: 8px;
      padding: 10px 16px;
      margin: 16px 0 12px;
      display: flex;
      align-items: center;
      gap: 12px;
      font-weight: 600;
      color: #166534;
      font-size: 12px;
    }
    .dot { width: 4px; height: 4px; border-radius: 50%; background: currentColor; opacity: 0.5; }
    .expand-row { font-size: 12.5px; color: var(--primary); font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; }

    /* 3. Steps Separator */
    .steps-sep {
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--t3);
      font-size: 12.5px;
      font-weight: 500;
      margin: -4px 0 -4px 4px;
    }

    /* 4. Scaled Panel */
    .panel {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 20px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .panel-lead {
      font-size: 15px;
      font-weight: 700;
      color: var(--t1);
      margin-bottom: 16px;
    }
    .kpi-row {
      display: flex;
      gap: 16px;
      margin-bottom: 16px;
    }
    .kpi {
      flex: 1;
      background: #F8FAFC;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 16px;
    }
    .kpi-label { font-size: 10px; font-weight: 700; text-transform: uppercase; color: var(--t3); letter-spacing: 0.05em; }
    .kpi-value { font-size: 28px; font-weight: 800; letter-spacing: -0.03em; margin: 4px 0; }
    .kpi-value.det { color: var(--t1); }
    .kpi-value.prob { color: #FF6F00; }
    .kpi-value.total { color: #10B981; }
    .kpi-sub { font-size: 11.5px; color: var(--t3); }
    .panel-line { font-size: 13.5px; color: var(--t2); line-height: 1.55; }
    
    .banner.success {
      background: #F0FDF4;
      border: 1px solid #DCFCE7;
      border-radius: 8px;
      padding: 10px 14px;
      display: flex;
      align-items: center;
      gap: 10px;
      font-size: 12.5px;
      color: #166534;
      font-weight: 500;
      margin-top: 14px;
    }

    /* 5. Follow-up Sizing Box */
    .followup-section { margin-top: 16px; display: flex; flex-direction: column; gap: 10px; }
    .followup-label { font-size: 11px; font-weight: 700; text-transform: uppercase; color: var(--t3); letter-spacing: 0.05em; }
    .chip-row { display: flex; gap: 10px; flex-wrap: wrap; }
    .chip {
      padding: 9px 20px;
      border-radius: 24px;
      font-size: 13px;
      font-weight: 600;
      cursor: pointer;
      border: 1px solid #CBD5E1;
      background: #FFFFFF;
      color: var(--t2);
      transition: all 0.2s;
    }
    .chip.confirm {
      background: #10B981;
      border-color: #10B981;
      color: #FFFFFF;
      box-shadow: 0 2px 6px rgba(16,185,129,0.25);
    }
    .chip.confirm:hover { opacity: 0.9; }
    .chip:hover:not(.confirm) { background: #F1F5F9; }
  </style>
<script>window.INJECTED_DATA = {};</script>
</head>
<body>
  <div class="wrapper">
    <!-- 1. Chain Tracker -->
    <div class="chain-container">
      <div class="chain-title">Here’s how I’ll get this done — three steps, each one handing its result straight to the next.</div>
      <div class="chain">
        <div class="chain-step ok">
          <div class="chain-head"><span class="chain-name">1 · Build</span></div>
          <div class="chain-sub">verified lapsed-buyer audience · Liquid Data</div>
          <div class="chain-id">audience_id: aud_7Q2KX9</div>
        </div>
        <div class="chain-arrow">→</div>
        <div class="chain-step ok">
          <div class="chain-head"><span class="chain-name">2 · Scale</span></div>
          <div class="chain-sub">ProScore expansion → Complete audience</div>
          <div class="chain-id">scaled_audience_id: aud_7Q2KX9_s</div>
        </div>
        <div class="chain-arrow">→</div>
        <div class="chain-step on">
          <div class="chain-head"><span class="chain-name">3 · Size</span></div>
          <div class="chain-sub">households &amp; addressable reach</div>
          <div class="chain-id" style="color:var(--t3);font-family:sans-serif;font-weight:normal;">pending confirmation...</div>
        </div>
      </div>
    </div>

    <!-- 2. Audience Tile -->
    <div class="aud-tile">
      <div class="aud-tile-head">
        <div class="aud-tile-title" id="pTitle">Tropicana Pure Premium — Lapsed Buyers</div>
        <div class="aud-tile-head-right">
          <span class="aud-tile-hint">tap a pill to edit it</span>
          <span class="aud-status">Scaled · Complete</span>
          <button class="pin-btn" title="Dock definition">◩</button>
        </div>
      </div>
      <div class="aud-tile-body">
        <div class="aud-grp">
          <div class="aud-grp-label">Type</div>
          <div class="aud-pills"><span class="pill type" id="pType" onclick="editPill('pType', 'Type')">Verified · Lapsed Buyers</span></div>
        </div>
        <div class="aud-grp">
          <div class="aud-grp-label">Scope (Product)</div>
          <div class="aud-pills">
            <span class="pill scope-product" id="pScope" onclick="editPill('pScope', 'Scope (Product)')">Tropicana Pure Premium</span>
            <button class="pill-add" onclick="editPill('pScope', 'Scope (Product)')">+</button>
          </div>
        </div>
        <div class="aud-grp">
          <div class="aud-grp-label">Scope (Time)</div>
          <div class="aud-pills">
            <span class="pill scope-time" id="pTime" onclick="editPill('pTime', 'Scope (Time)')">Prior 12 weeks</span>
            <button class="pill-add" onclick="editPill('pTime', 'Scope (Time)')">+</button>
          </div>
        </div>
        <div class="aud-grp">
          <div class="aud-grp-label">Measures</div>
          <div class="aud-pills">
            <button class="pill missing" id="pMeasure" onclick="editPill('pMeasure', 'Measures')">Add a measure</button>
          </div>
        </div>
        <div class="aud-grp">
          <div class="aud-grp-label">Attributes</div>
          <div class="aud-pills">
            <span class="pill attribute" id="pAttr" onclick="editPill('pAttr', 'Attributes')">Price-sensitive</span>
            <button class="pill-add" onclick="editPill('pAttr', 'Attributes')">+</button>
          </div>
        </div>
        <div class="aud-grp">
          <div class="aud-grp-label">Destinations</div>
          <div class="aud-pills">
            <button class="pill-add danger" id="pDest" onclick="editPill('pDest', 'Destinations')">+</button>
          </div>
        </div>
        <div class="aud-result-strip">
          <span id="pReach">est. reach 412,400 HH</span><span class="dot"></span>
          <span>profile available</span><span class="dot"></span>
          <span>gates pending</span>
        </div>
        <div class="expand-row">
          <span>▸</span> View full audience details
        </div>
      </div>
    </div>

    <!-- 3. Steps Separator -->
    <div class="steps-sep">
      <span>▸</span> Worked through 3 steps
    </div>

    <!-- 4. Scaled Panel -->
    <div class="panel">
      <div class="panel-lead">Scaled to a Complete audience.</div>
      <div class="kpi-row">
        <div class="kpi"><div class="kpi-label">Verified seed</div><div class="kpi-value det" id="pDet">412,400</div><div class="kpi-sub">deterministic panel HH</div></div>
        <div class="kpi"><div class="kpi-label">ProScore expansion</div><div class="kpi-value prob">2.7<small>M</small></div><div class="kpi-sub">probabilistic lookalikes</div></div>
        <div class="kpi"><div class="kpi-label">Total reach</div><div class="kpi-value total">3.1<small>M</small></div><div class="kpi-sub">Complete · activation-ready</div></div>
      </div>
      <div class="panel-line">Seed of <b id="pDetSub">412,400</b> verified lapsed <span id="pLineProd">Tropicana Pure Premium</span> households expanded via ProScore to <b>3.1M</b> behaviorally similar US shoppers.</div>
      <div class="banner success">
        <span>✓</span> Complete = merge. Scaling merges the ProScore build with the verified seed; the seed itself is left untouched.
      </div>
    </div>

    <!-- 5. Ask Sizing Confirmation Box -->
    <div class="panel" style="background:#FAFAFA;">
      <div style="font-size:13.5px;color:var(--t1);line-height:1.55">That’s the heavy lifting done — your Complete audience is sitting at <b>3.1M</b> households. One step left: sizing it, so we know exactly how many households we can reach when you activate. Ready when you are.</div>
      <div class="followup-section">
        <div class="followup-label">Continue</div>
        <div class="chip-row">
          <button class="chip confirm" onclick="sizeAudience()">Yes, size it</button>
          <button class="chip">Review the audience first</button>
        </div>
      </div>
    </div>
  </div>

  <script>
    const data = window.INJECTED_DATA || {};
    if (data.product_name) {
      document.getElementById('pTitle').textContent = `${data.product_name} — Lapsed Buyers`;
      document.getElementById('pScope').textContent = data.product_name;
      document.getElementById('pLineProd').textContent = data.product_name;
    }
    if (data.pool_size || data.lapsed_pool) {
      const poolStr = (data.pool_size || data.lapsed_pool).toLocaleString();
      document.getElementById('pDet').textContent = poolStr;
      document.getElementById('pDetSub').textContent = poolStr;
      document.getElementById('pReach').textContent = `est. reach ${poolStr} HH`;
    }

    try {
      const pricing = window.parent.document.querySelectorAll('details#pricing-details');
      if (pricing) pricing.forEach(d => d.removeAttribute('open'));
    } catch(e) {}

    function editPill(id, label) {
      const el = document.getElementById(id);
      const curr = el ? el.textContent : '';
      const updated = prompt(`Edit ${label}:`, curr);
      if (updated && el) {
        el.textContent = updated;
      }
    }

    function sizeAudience() {
      const prod = document.getElementById('pScope') ? document.getElementById('pScope').textContent : 'Tropicana Pure Premium';
      const time = document.getElementById('pTime') ? document.getElementById('pTime').textContent : 'Prior 12 weeks';
      const meas = document.getElementById('pMeasure') ? document.getElementById('pMeasure').textContent : 'Add a measure';
      const attr = document.getElementById('pAttr') ? document.getElementById('pAttr').textContent : 'Price-sensitive';
      const dest = document.getElementById('pDest') ? document.getElementById('pDest').textContent : '+';

      window.parent.postMessage({
        type: 'USER_ACTION',
        actionId: 'size_audience',
        payload: {
          recap: `Audience [${prod}], Time [${time}], Measures [${meas}], Attr [${attr}], Dest [${dest}]`,
          product_name: prod,
          time_scope: time,
          measures: meas,
          attributes: attr,
          destinations: dest
        }
      }, '*');
    }
  </script>
</body>
</html>
"""

class UIBuilder:
    @staticmethod
    def build_combined_activation(surface_id: str, data: dict) -> dict:
        injected_script = f"<script>window.INJECTED_DATA = {json.dumps(data)};</script>"
        html = COMBINED_ACTIVATION_HTML_TEMPLATE.replace("</head>", f"{injected_script}\n</head>")
        return {
            "surfaceUpdate": {
                "surfaceId": surface_id,
                "components": [
                    {
                        "id": "root",
                        "component": {
                            "WebFrameSrcdoc": {
                                "htmlContent": { "literalString": html }
                            }
                        }
                    }
                ]
            },
            "dataModelUpdate": { "surfaceId": surface_id, "contents": [] },
            "beginRendering": { "surfaceId": surface_id, "root": "root" }
        }

    @staticmethod
    def build_product_table(surface_id: str, product_data: list, collapse: bool = False) -> dict:
        """Compiles A2UI payload for pricing opportunities interactive table."""
        injected_script = f"<script>window.INJECTED_DATA = {json.dumps(product_data)}; window.COLLAPSE_TABLE = {json.dumps(collapse)};</script>"
        html_injected = PRODUCT_TABLE_HTML_TEMPLATE.replace("</head>", f"{injected_script}\n</head>")

        return {
            "surfaceUpdate": {
                "surfaceId": surface_id,
                "components": [
                    {
                        "id": "root",
                        "component": {
                            "WebFrameSrcdoc": {
                                "htmlContent": { "literalString": html_injected }
                            }
                        }
                    }
                ]
            },
            "dataModelUpdate": {
                "surfaceId": surface_id,
                "contents": []
            },
            "beginRendering": {
                "surfaceId": surface_id,
                "root": "root"
            }
        }

    @staticmethod
    def build_sizing_dashboard(surface_id: str, sizing_data: dict) -> dict:
        """Compiles A2UI payload for audience sizing kpi dashboard."""
        injected_script = f"<script>window.INJECTED_DATA = {json.dumps(sizing_data)};</script>"
        html_injected = SIZING_DASHBOARD_HTML_TEMPLATE.replace("</head>", f"{injected_script}\n</head>")

        return {
            "surfaceUpdate": {
                "surfaceId": surface_id,
                "components": [
                    {
                        "id": "root",
                        "component": {
                            "WebFrameSrcdoc": {
                                "htmlContent": { "literalString": html_injected }
                            }
                        }
                    }
                ]
            },
            "dataModelUpdate": {
                "surfaceId": surface_id,
                "contents": []
            },
            "beginRendering": {
                "surfaceId": surface_id,
                "root": "root"
            }
        }

    @staticmethod
    def build_demographic_profile(surface_id: str, profile_data: dict) -> dict:
        """Compiles A2UI payload for audience demographic profile dashboard."""
        injected_script = f"<script>window.INJECTED_DATA = {json.dumps(profile_data)};</script>"
        html_injected = DEMOGRAPHIC_PROFILE_HTML_TEMPLATE.replace("</head>", f"{injected_script}\n</head>")

        return {
            "surfaceUpdate": {
                "surfaceId": surface_id,
                "components": [
                    {
                        "id": "root",
                        "component": {
                            "WebFrameSrcdoc": {
                                "htmlContent": { "literalString": html_injected }
                            }
                        }
                    }
                ]
            },
            "dataModelUpdate": {
                "surfaceId": surface_id,
                "contents": []
            },
            "beginRendering": {
                "surfaceId": surface_id,
                "root": "root"
            }
        }

    @staticmethod
    def build_execution_chain(surface_id: str, step: int = 3) -> dict:
        injected_script = f"<script>window.INJECTED_DATA = {json.dumps({'step': step})};</script>"
        html = EXECUTION_CHAIN_HTML_TEMPLATE.replace("</head>", f"{injected_script}\n</head>")
        return {
            "surfaceUpdate": {
                "surfaceId": surface_id,
                "components": [
                    {
                        "id": "root",
                        "component": {
                            "WebFrameSrcdoc": {
                                "htmlContent": { "literalString": html }
                            }
                        }
                    }
                ]
            },
            "dataModelUpdate": { "surfaceId": surface_id, "contents": [] },
            "beginRendering": { "surfaceId": surface_id, "root": "root" }
        }

    @staticmethod
    def build_audience_build(surface_id: str, data: dict) -> dict:
        injected_script = f"<script>window.INJECTED_DATA = {json.dumps(data)};</script>"
        html = AUDIENCE_BUILD_HTML_TEMPLATE.replace("</head>", f"{injected_script}\n</head>")
        return {
            "surfaceUpdate": {
                "surfaceId": surface_id,
                "components": [
                    {
                        "id": "root",
                        "component": {
                            "WebFrameSrcdoc": {
                                "htmlContent": { "literalString": html }
                            }
                        }
                    }
                ]
            },
            "dataModelUpdate": { "surfaceId": surface_id, "contents": [] },
            "beginRendering": { "surfaceId": surface_id, "root": "root" }
        }

    @staticmethod
    def build_audience_scale(surface_id: str, data: dict) -> dict:
        injected_script = f"<script>window.INJECTED_DATA = {json.dumps(data)};</script>"
        html = AUDIENCE_SCALE_HTML_TEMPLATE.replace("</head>", f"{injected_script}\n</head>")
        return {
            "surfaceUpdate": {
                "surfaceId": surface_id,
                "components": [
                    {
                        "id": "root",
                        "component": {
                            "WebFrameSrcdoc": {
                                "htmlContent": { "literalString": html }
                            }
                        }
                    }
                ]
            },
            "dataModelUpdate": { "surfaceId": surface_id, "contents": [] },
            "beginRendering": { "surfaceId": surface_id, "root": "root" }
        }

    @staticmethod
    def build_audience_ask_size(surface_id: str) -> dict:
        return {
            "surfaceUpdate": {
                "surfaceId": surface_id,
                "components": [
                    {
                        "id": "root",
                        "component": {
                            "WebFrameSrcdoc": {
                                "htmlContent": { "literalString": AUDIENCE_ASK_SIZE_HTML_TEMPLATE }
                            }
                        }
                    }
                ]
            },
            "dataModelUpdate": { "surfaceId": surface_id, "contents": [] },
            "beginRendering": { "surfaceId": surface_id, "root": "root" }
        }

def get_product_table_a2ui(products: list) -> str:
    ui = UIBuilder.build_product_table("circana-pricing-table", products)
    sequence = [ui["surfaceUpdate"], ui["dataModelUpdate"], ui["beginRendering"]]
    return f"<a2ui-json>\n{json.dumps(sequence, indent=2)}\n</a2ui-json>"

def get_sizing_dashboard_a2ui(sizing: dict) -> str:
    ui = UIBuilder.build_sizing_dashboard("circana-sizing-dashboard", sizing)
    sequence = [ui["surfaceUpdate"], ui["dataModelUpdate"], ui["beginRendering"]]
    return f"<a2ui-json>\n{json.dumps(sequence, indent=2)}\n</a2ui-json>"

def get_demographic_profile_a2ui(profile: dict) -> str:
    ui = UIBuilder.build_demographic_profile("circana-demographic-profile", profile)
    sequence = [ui["surfaceUpdate"], ui["dataModelUpdate"], ui["beginRendering"]]
    return f"<a2ui-json>\n{json.dumps(sequence, indent=2)}\n</a2ui-json>"

LOYALTY_CAMPAIGN_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <meta content='connect-src "none"' http-equiv='Content-Security-Policy'>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #ffffff;
            --border-color: #e2e8f0;
            --text-primary: #0f172a;
            --text-secondary: #64748b;
            --accent-primary: #3b82f6;
            --accent-secondary: #2563eb;
        }
        body {
            font-family: 'Poppins', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-primary);
            margin: 0;
            padding: 16px;
        }
        .header h1 {
            font-size: 1.25rem;
            margin: 0 0 4px;
        }
        .header p {
            color: var(--text-secondary);
            font-size: 0.85rem;
            margin: 0 0 16px;
        }
        .kpi-container {
            display: flex;
            gap: 12px;
            margin-bottom: 20px;
        }
        .kpi-card {
            flex: 1;
            background-color: #f8fafc;
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 12px;
        }
        .kpi-title {
            color: var(--text-secondary);
            font-size: 0.75rem;
            text-transform: uppercase;
            font-weight: 600;
        }
        .kpi-value {
            font-size: 1.5rem;
            font-weight: 700;
            margin-top: 4px;
        }
        .panel {
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 16px;
        }
        .panel-title {
            font-weight: 600;
            margin-bottom: 12px;
        }
        .form-group {
            margin-bottom: 12px;
        }
        .form-label {
            display: block;
            margin-bottom: 4px;
            color: var(--text-secondary);
            font-size: 0.75rem;
        }
        .form-input {
            width: 100%;
            background-color: var(--bg-color);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            color: var(--text-primary);
            padding: 6px;
            box-sizing: border-box;
        }
        .btn-launch {
            width: 100%;
            background: linear-gradient(135deg, var(--accent-primary), var(--accent-secondary));
            color: #ffffff;
            border: none;
            padding: 8px;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            transition: opacity 0.2s;
            text-align: center;
        }
        .btn-launch:hover {
            opacity: 0.9;
        }
    </style>
</head>
<body>
    <div class='header'>
        <h1>Loyalty Campaign Manager</h1>
        <p id='cohort-context'>Activate offer personalization for target segment</p>
    </div>

    <div class='kpi-container'>
        <div class='kpi-card'>
            <div class='kpi-title'>Target Customers</div>
            <div class='kpi-value' id='val-customers'>0</div>
        </div>
        <div class='kpi-card'>
            <div class='kpi-title'>Current Churn Risk</div>
            <div class='kpi-value' id='val-risk'>High</div>
        </div>
    </div>

    <div class='panel'>
        <div class='panel-title'>Campaign Parameters</div>
        <div class='form-group'>
            <label class='form-label' for='discount-value'>Discount Value (%)</label>
            <input class='form-input' type='number' id='discount-value' value='10'>
        </div>
        <div class='form-group'>
            <label class='form-label' for='points-multiplier'>Points Multiplier</label>
            <input class='form-input' type='number' id='points-multiplier' value='2'>
        </div>
        <button class='btn-launch' id='btn-submit'>Launch Loyalty Campaign</button>
    </div>

    <script>
        const data = window.INJECTED_DATA || {};
        document.getElementById('cohort-context').textContent = `Target cohort: ${data.product_name || 'Selected Cohort'}`;
        document.getElementById('val-customers').textContent = (data.shoppers_isolated || 350000).toLocaleString();

        document.getElementById('btn-submit').onclick = () => {
            const disc = document.getElementById('discount-value').value;
            const mult = document.getElementById('points-multiplier').value;
            window.parent.postMessage({
                type: 'USER_ACTION',
                actionId: 'btn_launch_campaign',
                payload: {
                    discount_pct: parseInt(disc),
                    points_mult: parseFloat(mult),
                    product: data.product_name || 'Selected Cohort'
                }
            }, '*');
        };
    </script>
</body>
</html>
"""

AUDIENCE_BUILD_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <meta content='connect-src "none"' http-equiv='Content-Security-Policy'>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #ffffff;
            --border: #e2e8f0;
            --t1: #0f172a;
            --t2: #475569;
            --t3: #64748b;
            --primary: #2563eb;
            --green: #10b981;
        }
        body { font-family: 'Poppins', sans-serif; margin: 0; padding: 8px; background: #ffffff; color: var(--t1); }
        .aud-tile { border: 1px solid var(--border); border-radius: 12px; background: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.04); overflow: hidden; }
        .aud-head { display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid #f1f5f9; }
        .aud-title { font-size: 15px; font-weight: 700; color: var(--t1); }
        .aud-badge { background: #f0fdf4; color: #166534; border: 1px solid #bbf7d0; font-size: 10px; font-weight: 700; padding: 4px 10px; border-radius: 20px; text-transform: uppercase; letter-spacing: 0.05em; }
        .aud-body { padding: 16px 20px; }
        .aud-row { display: flex; align-items: center; padding: 10px 0; border-bottom: 1px solid #f1f5f9; font-size: 12.5px; }
        .aud-row:last-child { border-bottom: none; }
        .aud-lbl { width: 140px; font-weight: 600; color: var(--t3); font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; }
        .pill { display: inline-flex; align-items: center; background: #f8fafc; border: 1px solid #cbd5e1; padding: 5px 12px; border-radius: 6px; font-size: 12px; font-weight: 500; color: var(--t1); margin-right: 8px; }
        .pill.purple { background: #faf5ff; border-color: #e9d5ff; color: #7e22ce; font-weight: 600; }
        .pill.blue { background: #eff6ff; border-color: #bfdbfe; color: #1d4ed8; font-weight: 600; }
        .pill.green { background: #f0fdf4; border-color: #bbf7d0; color: #15803d; font-weight: 600; }
        .pill-add { border: 1px dashed #f59e0b; background: #fffbeb; color: #d97706; font-weight: 600; cursor: pointer; }
        .pill-add.red { border-color: #ef4444; background: #fef2f2; color: #dc2626; }
        .aud-footer { background: #f8fafc; padding: 12px 20px; font-size: 11.5px; font-weight: 600; color: var(--t2); display: flex; justify-content: space-between; align-items: center; }
        .link { color: var(--primary); cursor: pointer; font-weight: 600; text-decoration: none; }
    </style>
</head>
<body>
    <div class="aud-tile">
        <div class="aud-head">
            <div class="aud-title" id="p-title">Tropicana Pure Premium — Lapsed Buyers</div>
            <div class="aud-badge">SCALED · COMPLETE</div>
        </div>
        <div class="aud-body">
            <div class="aud-row"><div class="aud-lbl">Type</div><div><span class="pill purple">Verified · Lapsed Buyers</span></div></div>
            <div class="aud-row"><div class="aud-lbl">Scope (Product)</div><div><span class="pill blue" id="p-pill">Tropicana Pure Premium</span></div></div>
            <div class="aud-row"><div class="aud-lbl">Scope (Time)</div><div><span class="pill green">Prior 12 weeks</span></div></div>
            <div class="aud-row"><div class="aud-lbl">Measures</div><div><span class="pill pill-add">+ Add a measure</span></div></div>
            <div class="aud-row"><div class="aud-lbl">Attributes</div><div><span class="pill">Price-sensitive</span></div></div>
            <div class="aud-row"><div class="aud-lbl">Destinations</div><div><span class="pill pill-add red">+</span></div></div>
        </div>
        <div class="aud-footer">
            <span style="color:#10b981">est. reach 412,400 HH · profile available · gates pending</span>
            <a class="link" href="#">View full audience details →</a>
        </div>
    </div>
    <script>
        const data = window.INJECTED_DATA || {};
        if (data.product_name) {
            document.getElementById('p-title').textContent = data.product_name + " — Lapsed Buyers";
            document.getElementById('p-pill').textContent = data.product_name;
        }
    </script>
</body>
</html>
"""

AUDIENCE_SCALE_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Poppins', sans-serif; margin: 0; padding: 8px; background: #ffffff; color: #0f172a; }
        .panel { border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; background: #ffffff; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }
        .panel-lead { font-size: 15px; font-weight: 700; margin-bottom: 16px; }
        .kpi-row { display: flex; gap: 16px; margin-bottom: 16px; }
        .kpi { flex: 1; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 10px; padding: 16px; }
        .kpi-label { font-size: 10px; text-transform: uppercase; color: #64748b; font-weight: 700; letter-spacing: 0.05em; }
        .kpi-value { font-size: 28px; font-weight: 700; margin: 8px 0 4px; }
        .kpi-value.det { color: #0f172a; }
        .kpi-value.prob { color: #ff6f00; }
        .kpi-value.total { color: #10b981; }
        .kpi-sub { font-size: 11px; color: #64748b; }
        .panel-line { font-size: 13px; line-height: 1.5; color: #334155; margin-bottom: 16px; }
        .banner { background: #f0fdf4; border: 1px solid #bbf7d0; color: #166534; padding: 10px 14px; border-radius: 8px; font-size: 12px; font-weight: 500; }
    </style>
</head>
<body>
    <div class="panel">
        <div class="panel-lead">Scaled to a Complete audience.</div>
        <div class="kpi-row">
            <div class="kpi"><div class="kpi-label">Verified seed</div><div class="kpi-value det">412,400</div><div class="kpi-sub">deterministic panel HH</div></div>
            <div class="kpi"><div class="kpi-label">ProScore expansion</div><div class="kpi-value prob">2.7<span style="font-size:20px">M</span></div><div class="kpi-sub">probabilistic lookalikes</div></div>
            <div class="kpi"><div class="kpi-label">Total reach</div><div class="kpi-value total">3.1<span style="font-size:20px">M</span></div><div class="kpi-sub">Complete · activation-ready</div></div>
        </div>
        <div class="panel-line" id="desc">Seed of <b>412,400</b> verified lapsed Tropicana Pure Premium households expanded via ProScore to <b>3.1M</b> behaviorally similar US shoppers.</div>
        <div class="banner">✓ Complete = merge. Scaling merges the ProScore build with the verified seed; the seed itself is left untouched.</div>
    </div>
    <script>
        const data = window.INJECTED_DATA || {};
        if (data.product_name) {
            document.getElementById('desc').innerHTML = `Seed of <b>412,400</b> verified lapsed ${data.product_name} households expanded via ProScore to <b>3.1M</b> behaviorally similar US shoppers.`;
        }
    </script>
</body>
</html>
"""

AUDIENCE_ASK_SIZE_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang='en'>
<head>
    <meta charset='UTF-8'>
    <meta name='viewport' content='width=device-width, initial-scale=1.0'>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Poppins', sans-serif; margin: 0; padding: 8px; background: #ffffff; color: #0f172a; }
        .panel { border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; background: #f8fafc; }
        .lead { font-size: 13.5px; line-height: 1.6; margin-bottom: 16px; color: #1e293b; }
        .lbl { font-size: 10px; font-weight: 700; text-transform: uppercase; color: #64748b; margin-bottom: 12px; letter-spacing: 0.05em; }
        .btn-row { display: flex; gap: 12px; }
        .btn { padding: 10px 24px; border-radius: 24px; font-weight: 600; font-size: 13px; cursor: pointer; transition: all 0.2s; border: 2px solid #10b981; background: #ffffff; color: #10b981; }
        .btn:hover { background: #10b981; color: #ffffff; }
        .btn-secondary { padding: 10px 20px; border-radius: 24px; border: 1px solid #cbd5e1; background: #ffffff; color: #475569; font-weight: 600; font-size: 13px; cursor: pointer; }
        .btn-secondary:hover { background: #f1f5f9; }
    </style>
</head>
<body>
    <div class="panel">
        <div class="lead">That’s the heavy lifting done — your Complete audience is sitting at <b>3.1M</b> households. One step left: sizing it, so we know exactly how many households we can reach when you activate. Ready when you are.</div>
        <div class="lbl">Continue</div>
        <div class="btn-row">
            <button class="btn" onclick="sizeAudience()">Yes, size it</button>
            <button class="btn-secondary" onclick="reviewAudience()">Review the audience first</button>
        </div>
    </div>
    <script>
        function sizeAudience() {
            window.parent.postMessage({
                type: 'USER_ACTION',
                actionId: 'size_audience',
                payload: {}
            }, '*');
        }
        function reviewAudience() {}
    </script>
</body>
</html>
"""
# Extend UIBuilder
class UIBuilderExtended(UIBuilder):
    @staticmethod
    def build_loyalty_dashboard(surface_id: str, loyalty_data: dict) -> dict:
        """Compiles A2UI payload for loyalty personalization campaign manager."""
        injected_script = f"<script>window.INJECTED_DATA = {json.dumps(loyalty_data)};</script>"
        html_injected = LOYALTY_CAMPAIGN_HTML_TEMPLATE.replace("</head>", f"{injected_script}\n</head>")

        return {
            "surfaceUpdate": {
                "surfaceId": surface_id,
                "components": [
                    {
                        "id": "root",
                        "component": {
                            "WebFrameSrcdoc": {
                                "htmlContent": { "literalString": html_injected }
                            }
                        }
                    }
                ]
            },
            "dataModelUpdate": {
                "surfaceId": surface_id,
                "contents": []
            },
            "beginRendering": {
                "surfaceId": surface_id,
                "root": "root"
            }
        }

def get_loyalty_dashboard_a2ui(loyalty_data: dict) -> str:
    ui = UIBuilderExtended.build_loyalty_dashboard("circana-loyalty-dashboard", loyalty_data)
    sequence = [ui["surfaceUpdate"], ui["dataModelUpdate"], ui["beginRendering"]]
    return f"<a2ui-json>\n{json.dumps(sequence, indent=2)}\n</a2ui-json>"

