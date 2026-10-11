const $ = (id) => document.getElementById(id);

const inr = (n) =>
  new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 0 }).format(n || 0);

function params() {
  const q = new URLSearchParams({
    city: $("city").value,
    sku: $("sku").value,
    payment: $("payment").value,
  });
  return q.toString();
}

function kpiCard(label, value, hot) {
  return `<div class="kpi ${hot ? "hot" : ""}"><span>${label}</span><strong>${value}</strong></div>`;
}

function tableHTML(rows, cols) {
  if (!rows.length) return "<p style='padding:12px;color:#5a647a'>No rows</p>";
  const head = cols.map((c) => `<th>${c.label}</th>`).join("");
  const body = rows
    .map((r) => {
      const tds = cols
        .map((c) => {
          let v = r[c.key];
          if (c.kind === "inr") v = inr(v);
          if (c.kind === "pct") v = `${v}%`;
          if (c.key === "flag") v = r.flag ? '<span class="flag">HIGH RTO</span>' : "—";
          return `<td>${v}</td>`;
        })
        .join("");
      return `<tr>${tds}</tr>`;
    })
    .join("");
  return `<table><thead><tr>${head}</tr></thead><tbody>${body}</tbody></table>`;
}

async function loadMeta() {
  const res = await fetch("/api/meta");
  const meta = await res.json();
  meta.cities.forEach((c) => {
    const o = document.createElement("option");
    o.value = c;
    o.textContent = c;
    $("city").appendChild(o);
  });
  meta.skus.forEach((c) => {
    const o = document.createElement("option");
    o.value = c;
    o.textContent = c;
    $("sku").appendChild(o);
  });
}

function draw(id, spec) {
  if (!spec) return;
  Plotly.react(id, spec.data, spec.layout, { displayModeBar: false, responsive: true });
}

async function refresh() {
  const q = params();
  const [overview, charts] = await Promise.all([
    fetch(`/api/overview?${q}`).then((r) => r.json()),
    fetch(`/api/charts?${q}`).then((r) => r.json()),
  ]);
  const k = overview.kpis;
  $("kpis").innerHTML = [
    kpiCard("Orders", k.orders.toLocaleString("en-IN")),
    kpiCard("GMV", inr(k.gmv)),
    kpiCard("RTO %", `${k.rto_pct}%`, k.rto_pct >= 16),
    kpiCard("Returns %", `${k.return_pct}%`),
    kpiCard("Failed GMV", inr(k.failed_gmv), true),
    kpiCard("COD share", `${k.cod_share}%`),
  ].join("");

  $("table-skus").innerHTML = tableHTML(overview.skus, [
    { key: "sku", label: "SKU" },
    { key: "sku_name", label: "Name" },
    { key: "orders", label: "Orders" },
    { key: "rto_pct", label: "RTO %", kind: "pct" },
    { key: "failed_gmv", label: "Failed GMV", kind: "inr" },
    { key: "flag", label: "Flag" },
  ]);
  $("table-cities").innerHTML = tableHTML(overview.cities, [
    { key: "city", label: "City" },
    { key: "state", label: "St" },
    { key: "orders", label: "Orders" },
    { key: "rto_pct", label: "RTO %", kind: "pct" },
    { key: "cod_pct", label: "COD %", kind: "pct" },
    { key: "flag", label: "Flag" },
  ]);

  draw("chart-weekly", charts.weekly);
  draw("chart-reasons", charts.reasons);
  draw("chart-cities", charts.cities);
  draw("chart-skus", charts.skus);
  draw("chart-payment", charts.payment);
}

$("pack-btn").addEventListener("click", () => {
  window.location.href = "/api/report";
});

["city", "sku", "payment"].forEach((id) => $(id).addEventListener("change", refresh));

loadMeta().then(refresh);
