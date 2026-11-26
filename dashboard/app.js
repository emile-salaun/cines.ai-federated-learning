/* Dashboard of the federated learning workshop.
 *
 * Reads the results written by the Flower server (api/run/<name>) and the precomputed
 * "solo / centralised" references. No dependencies: hand-written SVG and DOM.
 * Addresses are relative, so it also works behind the JupyterHub proxy.
 */
"use strict";

// ============================================================================ utils
const $ = (sel, root = document) => root.querySelector(sel);
const esc = (s) => String(s).replace(/[&<>"']/g, (c) => (
  { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const cssVar = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
const NNBSP = " ";

function pct(v, digits = 0) {
  if (v == null || Number.isNaN(v)) return "—";
  return (v * 100).toFixed(digits) + "%";
}
function mb(bytes) {
  if (bytes == null) return "—";
  const v = bytes / 1e6;
  return (v < 10 ? v.toFixed(2) : v.toFixed(0)) + NNBSP + "MB";
}
function int(n) { return Math.round(n).toLocaleString("en-US"); }
function secs(s) { return s.toFixed(s < 10 ? 1 : 0) + NNBSP + "s"; }

function clientColor(pid, n) {
  return n > 8 ? cssVar("--faint") : cssVar(`--c${pid}`);
}

async function getJSON(url) {
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(`${res.status} ${url}`);
  return res.json();
}

// ============================================================================ state
const state = {
  view: "together",
  runs: [],
  run: null,
  follow: true,
  payload: null,
  payloadKey: null,
  cache: new Map(),          // name -> {key, payload}, for the comparison view
  compare: new Set(),
  net: { round: null, latest: true, raf: null },
  serverDown: false,
};

function readHash() {
  const h = new URLSearchParams(location.hash.slice(1));
  if (h.get("view")) state.view = h.get("view");
  if (h.get("run")) { state.run = h.get("run"); state.follow = false; }
}
function writeHash() {
  const h = new URLSearchParams();
  h.set("view", state.view);
  if (!state.follow && state.run) h.set("run", state.run);
  history.replaceState(null, "", "#" + h.toString());
}

// ============================================================================ data
function derive(p) {
  const run = p.run;
  const rounds = run.rounds || [];
  const ids = new Set();
  rounds.forEach((r) => Object.keys(r.clients || {}).forEach((k) => ids.add(+k)));
  const clients = [...ids].sort((a, b) => a - b);
  const total = +run.config["num-server-rounds"] || (rounds.length ? rounds[rounds.length - 1].round : 0);
  const last = rounds.length ? rounds[rounds.length - 1] : null;
  return {
    name: p.name, run, rounds, clients, n: clients.length, total, last,
    classes: run.classes || [], refs: p.references || null,
    counts: p.label_counts || null, raw: p.raw_bytes || null,
  };
}

function recognized(perClass) {
  return perClass ? perClass.filter((v) => v >= 0.5).length : 0;
}

function describeConfig(cfg) {
  const parts = [cfg.dataset === "cifar10" ? "CIFAR-10" : "Fashion-MNIST"];
  if (cfg.partitioning === "iid") parts.push("IID data");
  if (cfg.partitioning === "dirichlet") parts.push(`Dirichlet α = ${cfg["dirichlet-alpha"]}`);
  if (cfg.partitioning === "pathological") parts.push(`${cfg["classes-per-partition"]} classes per client`);
  if (+cfg["fraction-train"] < 1) parts.push(`${pct(+cfg["fraction-train"])} of clients per round`);
  if (+cfg["dropout-rate"] > 0) parts.push(`${pct(+cfg["dropout-rate"])} dropouts`);
  if (+cfg["proximal-mu"] > 0) parts.push(`FedProx μ = ${cfg["proximal-mu"]}`);
  return parts.join(", ");
}

// ============================================================================ line chart
/* series: [{name, color, width, dash, opacity, points: [[x, y|null], ...], end: bool}] */
function niceMax(v) {
  const p = Math.pow(10, Math.floor(Math.log10(v)));
  return [1, 2, 2.5, 5, 10].map((k) => k * p).find((k) => k >= v);
}

function lineChart(container, { series, xMax, yMax = 1, yFmt = (v) => pct(v), height = 300, ticks }) {
  // Drawn at the container's real width, so text keeps its size on any screen.
  const W = Math.max(300, Math.round(container.getBoundingClientRect().width || 640));
  const H = height, m = { l: 46, r: W < 480 ? 104 : 124, t: 12, b: 30 };
  const pw = W - m.l - m.r, ph = H - m.t - m.b;
  const X = (x) => m.l + (xMax ? x / xMax : 0) * pw;
  const Y = (y) => m.t + ph - (y / yMax) * ph;
  const yTicks = ticks || [0, 0.25, 0.5, 0.75, 1].map((f) => f * yMax);

  let svg = `<svg viewBox="0 0 ${W} ${H}" role="img">`;
  svg += `<g class="axis">`;
  yTicks.forEach((v) => {
    svg += `<line class="gridline" x1="${m.l}" x2="${m.l + pw}" y1="${Y(v)}" y2="${Y(v)}"/>`;
    svg += `<text x="${m.l - 8}" y="${Y(v) + 4}" text-anchor="end">${esc(yFmt(v))}</text>`;
  });
  const step = xMax <= 12 ? 1 : Math.ceil(xMax / 10);
  for (let x = 0; x <= xMax; x += step) {
    svg += `<text x="${X(x)}" y="${H - 8}" text-anchor="middle">${x}</text>`;
  }
  svg += `<text x="${m.l + pw + 10}" y="${H - 8}">round</text></g>`;

  const ends = [];
  series.forEach((s) => {
    let d = "", pen = false;
    s.points.forEach(([x, y]) => {
      if (y == null || Number.isNaN(y)) { pen = false; return; }
      d += `${pen ? "L" : "M"}${X(x).toFixed(1)},${Y(y).toFixed(1)}`;
      pen = true;
    });
    if (!d) return;
    svg += `<path d="${d}" fill="none" stroke="${s.color}" stroke-width="${s.width || 2}"
      stroke-linejoin="round" stroke-linecap="round" opacity="${s.opacity ?? 1}"
      ${s.dash ? `stroke-dasharray="${s.dash}"` : ""}/>`;
    const lastPt = [...s.points].reverse().find(([, y]) => y != null && !Number.isNaN(y));
    if (lastPt && s.dot !== false) {
      svg += `<circle cx="${X(lastPt[0])}" cy="${Y(lastPt[1])}" r="${(s.width || 2) + 1}" fill="${s.color}"/>`;
    }
    if (lastPt && s.end) ends.push({ y: Y(lastPt[1]), x: X(lastPt[0]), s, v: lastPt[1] });
  });
  // end labels, nudged apart so they never overlap
  ends.sort((a, b) => a.y - b.y);
  for (let i = 1; i < ends.length; i++) ends[i].y = Math.max(ends[i].y, ends[i - 1].y + 14);
  const bottom = m.t + ph;   // keep the column inside the plot: push back up if needed
  for (let i = ends.length - 1; i >= 0; i--) {
    const limit = i === ends.length - 1 ? bottom : ends[i + 1].y - 14;
    ends[i].y = Math.min(ends[i].y, limit);
  }
  // labels in one column right of the plot, each with its series' color
  const lx = m.l + pw + 10;
  ends.forEach((e) => {
    if (e.s.color !== "transparent") svg += `<circle cx="${lx + 3}" cy="${e.y}" r="3.5" fill="${e.s.color}"/>`;
    svg += `<text class="lab${e.s.strong ? " strong" : ""}" x="${lx + 11}" y="${e.y + 4}">${esc(e.s.name)} ${esc(yFmt(e.v))}</text>`;
  });
  svg += `<line class="hoverline" x1="0" x2="0" y1="${m.t}" y2="${m.t + ph}" visibility="hidden"/>`;
  svg += `<rect x="${m.l}" y="${m.t}" width="${pw}" height="${ph}" fill="transparent" class="hit"/>`;
  svg += `</svg><div class="tip" hidden></div>`;
  container.classList.add("chart");
  container.innerHTML = svg;

  // hover: one crosshair, one tooltip with every series at that round
  const el = container.querySelector("svg"), tip = container.querySelector(".tip");
  const hl = el.querySelector(".hoverline"), hit = el.querySelector(".hit");
  hit.addEventListener("mousemove", (ev) => {
    const r = el.getBoundingClientRect();
    const sx = (ev.clientX - r.left) * (W / r.width);
    const x = clamp(Math.round(((sx - m.l) / pw) * xMax), 0, xMax);
    hl.setAttribute("x1", X(x)); hl.setAttribute("x2", X(x)); hl.setAttribute("visibility", "visible");
    const rows = series.filter((s) => s.tip !== false).map((s) => {
      const pt = s.points.find(([px]) => px === x);
      return pt && pt[1] != null && !Number.isNaN(pt[1]) ? { s, v: pt[1] } : null;
    }).filter(Boolean).sort((a, b) => b.v - a.v);
    if (!rows.length) { tip.hidden = true; return; }
    tip.innerHTML = `<div class="note">round ${x}</div>` + rows.map(({ s, v }) =>
      `<div class="row"><span><span class="dotc" style="background:${s.color}"></span>${esc(s.name)}</span><span>${esc(yFmt(v))}</span></div>`).join("");
    tip.hidden = false;
    const left = (X(x) / W) * r.width;
    tip.style.left = `${left + (left > r.width * 0.6 ? -tip.offsetWidth - 12 : 12)}px`;
    tip.style.top = "8px";
  });
  hit.addEventListener("mouseleave", () => { tip.hidden = true; hl.setAttribute("visibility", "hidden"); });
}

// ============================================================================ matrices
function cell(v) {
  if (v == null || Number.isNaN(v)) return `<td style="background:var(--page)"></td>`;
  const a = (0.08 + 0.82 * v).toFixed(2);
  const fg = v > 0.55 ? "var(--surface)" : v < 0.05 ? "var(--faint)" : "var(--ink)";
  return `<td style="background:rgba(var(--ink-rgb),${a});color:${fg}" title="${pct(v)}">${Math.round(v * 100)}</td>`;
}

function matrix(classes, rows, { countLabel = "recognised" } = {}) {
  let h = `<table class="matrix"><thead><tr><th></th>${classes.map((c) => `<th>${esc(c)}</th>`).join("")}<th>${esc(countLabel)}</th></tr></thead><tbody>`;
  rows.forEach((r) => {
    if (r.gap) { h += `<tr class="gap"><th></th></tr>`; return; }
    h += `<tr class="${r.cls || ""}"><th>${r.dot ? `<span class="dotc" style="background:${r.dot}"></span>` : ""}${esc(r.label)}</th>`;
    h += (r.values || classes.map(() => null)).map(cell).join("");
    h += `<td class="count">${r.values ? `${recognized(r.values)}/${classes.length}` : "—"}</td></tr>`;
  });
  return h + "</tbody></table>";
}

function holdings(D) {
  if (!D.counts) return "";
  const max = Math.max(...D.counts.flat(), 1);
  return `<div class="holdings">` + D.counts.map((row, i) => {
    const color = clientColor(i, D.counts.length);
    const total = row.reduce((a, b) => a + b, 0);
    const bars = row.map((v, j) => `<span title="${esc(D.classes[j] || j)} : ${int(v)}" style="height:${Math.max(2, (v / max) * 100)}%;background:${color};opacity:${v ? 0.9 : 0.15}"></span>`).join("");
    return `<div class="holding"><div class="name"><span class="dotc" style="background:${color}"></span>client ${i}</div>
      <div class="bars" aria-label="images per class">${bars}</div>
      <div class="meta">${int(total)} images, ${D.raw ? mb(D.raw[i]) : ""} kept on site</div></div>`;
  }).join("") + `</div>`;
}

// ============================================================================ view: alone or together
function renderTogether(D) {
  const v = $("#view");
  const done = D.rounds.filter((r) => r.round > 0);
  if (!done.length) {
    v.innerHTML = `<div class="empty">Le run <b>${esc(D.name)}</b> is starting: first round in 20 to 60 s.</div>`;
    return;
  }
  const r = D.last.round;
  const refs = D.refs;
  const fl = D.last.accuracy, flC = recognized(D.last.per_class);
  let hero, detail;

  if (refs) {
    const ri = Math.min(r, refs.centralized.rounds.length - 1);
    const alone = Object.entries(refs.alone).map(([pid, a]) => ({ pid: +pid, ...a.rounds[ri] }));
    const best = Math.max(...alone.map((a) => a.accuracy));
    const cs = alone.map((a) => recognized(a.per_class));
    const cMin = Math.min(...cs), cMax = Math.max(...cs);
    const cen = refs.centralized.rounds[ri];
    const span = cMin === cMax ? `${cMax}` : `${cMin} to ${cMax}`;
    hero = `<p><span class="alone">Alone, each client recognises <span class="n">${span} classes out of ${D.classes.length}</span>, with <span class="n">${pct(best)}</span> accuracy at best.</span>
      Together, the federated model recognises <span class="n">${flC}</span> and reaches <span class="n">${pct(fl)}</span>, without a single image leaving the clients.</p>`;
    detail = `At round ${r} of ${D.total}, ${describeConfig(D.run.config)}. If all images were gathered in one place, the centralised model would reach ${pct(cen.accuracy)} (${recognized(cen.per_class)} classes): that is the upper bound.`;
  } else {
    hero = `<p>Together, the federated model recognises <span class="n">${flC} classes out of ${D.classes.length}</span> and reaches <span class="n">${pct(fl)}</span>, without a single image leaving the clients.</p>`;
    detail = `No "solo / centralised" reference for this configuration (${describeConfig(D.run.config)}). They exist for the notebook configurations; to add more: <code>uv run python scripts/compute_baselines.py</code>.`;
  }

  v.innerHTML = `
    <section class="hero">${hero}<div class="detail">${detail}</div></section>
    <div class="grid2">
      <section class="panel"><h2>Accuracy over the rounds</h2>
        <p class="sub">Same test set for all. Each solo client trains as much as in the federated run, but never exchanges anything.</p>
        <div id="c-together"></div><div class="legend" id="lg-together"></div></section>
      <section class="panel"><h2>What each model can recognise</h2>
        <p class="sub">Per-class accuracy (%), at round ${r}. A class counts as recognised above 50%.</p>
        <div id="m-together"></div></section>
    </div>
    <section class="panel" style="margin-top:20px"><h2>Each client's data</h2>
      <p class="sub">Images per class. They stay on the client's machine; only the model weights travel.</p>
      ${holdings(D)}</section>`;

  const ink = cssVar("--ink"), faint = cssVar("--faint");
  const series = [];
  if (refs) {
    Object.entries(refs.alone).forEach(([pid, a]) => series.push({
      name: `client ${pid} solo`, color: clientColor(+pid, D.n), width: 1.6, opacity: 0.85,
      points: a.rounds.map((x) => [x.round, x.accuracy]), dot: false,
    }));
    series.push({ name: "centralised", color: faint, width: 2, dash: "6 5", end: true,
      points: refs.centralized.rounds.map((x) => [x.round, x.accuracy]) });
  }
  series.push({ name: "together (FL)", color: ink, width: 3.2, end: true, strong: true,
    points: D.rounds.map((x) => [x.round, x.accuracy]) });
  if (refs) {
    // one end label for the alone curves: their best value
    const lastAlone = Object.values(refs.alone).map((a) => a.rounds[a.rounds.length - 1].accuracy);
    series.push({ name: "solo, best", color: "transparent", width: 0, end: true, dot: false,
      tip: false, points: [[D.total, Math.max(...lastAlone)]] });
  }
  lineChart($("#c-together"), { series, xMax: D.total });
  $("#lg-together").innerHTML =
    `<span><span class="sw" style="color:${ink}"></span>together (FL)</span>` +
    (refs ? `<span><span class="sw dash" style="color:${faint}"></span>centralised</span>` +
      `<span>${D.clients.map((p) => `<span class="sw thin" style="color:${clientColor(p, D.n)};width:10px;margin-right:2px"></span>`).join("")}&nbsp;each client solo</span>` : "");

  const rows = [];
  if (refs) {
    const ri = Math.min(r, refs.centralized.rounds.length - 1);
    Object.entries(refs.alone).forEach(([pid, a]) => rows.push({
      label: `client ${pid} solo`, dot: clientColor(+pid, D.n), values: a.rounds[ri].per_class }));
    rows.push({ gap: true });
  }
  rows.push({ label: "together (FL)", cls: "together", values: D.last.per_class });
  if (refs) {
    const ri = Math.min(r, refs.centralized.rounds.length - 1);
    rows.push({ label: "centralised", values: refs.centralized.rounds[ri].per_class });
  }
  $("#m-together").innerHTML = `<div class="scrollx">${matrix(D.classes, rows)}</div>`;
}

// ============================================================================ view: the run
function clientAt(round, pid) { return (round.clients || {})[String(pid)] || {}; }

function renderRun(D) {
  const v = $("#view");
  const done = D.rounds.filter((r) => r.round > 0);
  if (!done.length) {
    v.innerHTML = `<div class="empty">Le run <b>${esc(D.name)}</b> is starting: first round in 20 to 60 s.</div>`;
    return;
  }
  const ink = cssVar("--ink");
  v.innerHTML = `
    <section class="hero"><p style="font-size:clamp(20px,2.2vw,26px)">${esc(describeConfig(D.run.config))}.
      Global model at <span class="n">${pct(D.last.accuracy)}</span> at round ${D.last.round} of ${D.total}.</p></section>
    <div class="grid2">
      <section class="panel"><h2>Global model and local models</h2>
        <p class="sub">Each client, right after its local training and before averaging, evaluated on the test set. A line breaks when the client did not take part.</p>
        <div id="c-run"></div></section>
      <section class="panel"><h2>Participation per round</h2>
        <p class="sub">Local model accuracy (%). "–": not sampled. "×": disconnected.</p>
        <div id="p-run" style="overflow-x:auto"></div></section>
    </div>
    <div class="grid2" style="margin-top:20px">
      <section class="panel"><h2>Client drift</h2>
        <p class="sub">Distance between the model each client sent back and the global model it had received. The more unusual a client's data, the further it moves away.</p>
        <div id="d-run"></div></section>
      <section class="panel"><h2>What each model recognises</h2>
        <p class="sub">Per-class accuracy (%) of each client's latest local model, and of the global model at round ${D.last.round}.</p>
        <div id="m-run"></div></section>
    </div>`;

  const series = D.clients.map((pid) => ({
    name: `client ${pid}`, color: clientColor(pid, D.n), width: 1.6,
    points: D.rounds.filter((r) => r.round > 0).map((r) => {
      const c = clientAt(r, pid);
      return [r.round, c.status === "ok" ? c.local_acc : null];
    }), dot: true,
  }));
  series.push({ name: "global model", color: ink, width: 3.2, end: true, strong: true,
    points: D.rounds.map((r) => [r.round, r.accuracy]) });
  lineChart($("#c-run"), { series, xMax: D.total });

  // participation grid
  let g = `<table class="pgrid"><thead><tr><th></th>`;
  for (let k = 1; k <= D.total; k++) g += `<th>${k}</th>`;
  g += `</tr></thead><tbody>`;
  D.clients.forEach((pid) => {
    g += `<tr><th><span class="dotc" style="background:${clientColor(pid, D.n)}"></span>client ${pid}</th>`;
    for (let k = 1; k <= D.total; k++) {
      const r = D.rounds.find((x) => x.round === k);
      if (!r) { g += `<td class="future"></td>`; continue; }
      const c = clientAt(r, pid);
      if (c.status === "ok") g += cell(c.local_acc);
      else if (c.status === "failed") g += `<td class="failed" title="disconnected">×</td>`;
      else g += `<td class="idle" title="not sampled">–</td>`;
    }
    g += `</tr>`;
  });
  $("#p-run").innerHTML = g + `</tbody></table>`;

  // drift
  const drift = D.clients.map((pid) => ({
    name: `client ${pid}`, color: clientColor(pid, D.n), width: 2, end: true,
    points: D.rounds.filter((r) => r.round > 0).map((r) => {
      const c = clientAt(r, pid);
      return [r.round, c.status === "ok" ? c.divergence : null];
    }),
  }));
  const top = niceMax(Math.max(0.1, ...drift.flatMap((s) => s.points.map(([, y]) => y || 0))));
  lineChart($("#d-run"), { series: drift, xMax: D.total, yMax: top, height: 260,
    yFmt: (y) => (Math.round(y * 100) / 100).toString().replace(".", ","),
    ticks: [0, top / 4, top / 2, (3 * top) / 4, top] });

  // per-class: last local model of each client + global
  const rows = D.clients.map((pid) => {
    const lastOk = [...D.rounds].reverse().find((r) => clientAt(r, pid).status === "ok");
    return { label: lastOk ? `client ${pid} (round ${lastOk.round})` : `client ${pid}`,
      dot: clientColor(pid, D.n), values: lastOk ? clientAt(lastOk, pid).local_per_class : null };
  });
  rows.push({ gap: true });
  rows.push({ label: "global model", cls: "together", values: D.last.per_class });
  $("#m-run").innerHTML = `<div class="scrollx">${matrix(D.classes, rows)}</div>`;
}

// ============================================================================ view: network
const PHASES = [
  "The server sends the global model",
  "Each client trains it on its data",
  "The clients send back their weights",
  "The server averages them",
  "The new model is evaluated",
];

function renderNetwork(D) {
  cancelAnimationFrame(state.net.raf);
  const v = $("#view");
  const rounds = D.rounds.filter((r) => r.round > 0 && r.comm && r.comm.train_sent);
  if (!rounds.length) {
    v.innerHTML = `<div class="empty">Le run <b>${esc(D.name)}</b> is starting: first round in 20 to 60 s.</div>`;
    return;
  }
  const lastRound = rounds[rounds.length - 1].round;
  if (state.net.latest || state.net.round == null || state.net.round > lastRound) state.net.round = lastRound;
  const R = rounds.find((r) => r.round === state.net.round) || rounds[rounds.length - 1];

  v.innerHTML = `
    <div class="netcontrols">
      <button id="replay">Replay the round</button>
      <label class="note" for="rsl">Round</label>
      <input id="rsl" type="range" min="${rounds[0].round}" max="${lastRound}" value="${R.round}">
      <span class="note" id="rlab">round ${R.round} of ${D.total}${state.net.latest ? ", following the latest round" : ""}</span>
      ${state.net.latest ? "" : `<button id="tolatest">Follow the latest round</button>`}
    </div>
    <div class="net">
      <section class="panel"><div id="star"></div>
        <ol class="phases" id="phases">${PHASES.map((p, i) => `<li><span class="k">${i + 1}</span>${p}</li>`).join("")}</ol>
        <p class="note" id="final" style="visibility:hidden;margin:8px 0 0"></p>
      </section>
      <div class="stack">
        <section class="panel"><h2>Round timeline</h2>
          <p class="sub" id="tl-sub"></p><div id="timeline"></div>
          <div class="legend">
            <span><span class="sw" style="color:var(--line)"></span>waiting for a CPU</span>
            <span><span class="sw" style="color:${clientColor(0, D.n)}"></span>local training</span>
            <span><span class="sw" style="color:var(--ink)"></span>reception and averaging</span>
            <span><span class="sw" style="color:var(--faint)"></span>evaluation</span>
          </div></section>
        <section class="panel"><h2>What travelled</h2><div id="volumes"></div></section>
      </div>
    </div>`;

  $("#replay").onclick = () => playRound(D, R);
  $("#rsl").oninput = (e) => { state.net.latest = false; state.net.round = +e.target.value; renderNetwork(D); };
  const tl = $("#tolatest");
  if (tl) tl.onclick = () => { state.net.latest = true; renderNetwork(D); };
  playRound(D, R);
}

function playRound(D, R) {
  cancelAnimationFrame(state.net.raf);
  const ink = cssVar("--ink"), faint = cssVar("--faint"), surface = cssVar("--surface");
  const line = cssVar("--line"), failed = cssVar("--failed");
  const comm = R.comm, t0 = comm.train_sent, tEnd = comm.end;
  const real = Math.max(tEnd - t0, 1e-3);
  const span = clamp(real, 3.5, 7), k = span / real, travel = 0.5;
  const s = (t) => 0.6 + Math.max(t - t0, 0) * k;

  // ---- star geometry
  const W = 640, H = 430, cx = 320, cy = 205, Rr = 140, nr = 26, sr = 38;
  const pos = {};
  D.clients.forEach((pid, i) => {
    const a = (-90 + (360 * i) / D.n) * Math.PI / 180;
    pos[pid] = { x: cx + Rr * Math.cos(a), y: cy + Rr * Math.sin(a), a };
  });
  const packets = [], rings = [], marks = [];
  const upArrivals = [];
  let svg = `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Messages between the server and the clients in round ${R.round}">`;

  D.clients.forEach((pid) => {
    const { x, y, a } = pos[pid];
    const c = clientAt(R, pid), cm = c.comm || {};
    const sx = cx + sr * Math.cos(a), sy = cy + sr * Math.sin(a);
    const ex = x - nr * Math.cos(a), ey = y - nr * Math.sin(a);
    svg += `<line x1="${sx}" y1="${sy}" x2="${ex}" y2="${ey}" stroke="${line}" stroke-width="2" ${c.status === "idle" ? 'stroke-dasharray="4 5"' : ""}/>`;
    if (cm.train_bytes_down) packets.push({ from: [sx, sy], to: [ex, ey], b: 0, d: travel, r: 7, fill: ink });
    if (c.status === "ok" && cm.train_reply_at) {
      const b = Math.max(s(cm.train_reply_at), travel);
      packets.push({ from: [ex, ey], to: [sx, sy], b, d: travel, r: 7, fill: clientColor(pid, D.n), stroke: surface });
      upArrivals.push(b + travel);
      const start = Math.max(cm.train_reply_at - (c.train_time || 0), t0);
      const rb = Math.max(s(start), travel);
      rings.push({ pid, b: rb, d: Math.max(s(cm.train_reply_at) - rb, 0.15) });
    } else if (c.status === "failed" && cm.train_reply_at) {
      const b = Math.max(s(cm.train_reply_at), travel);
      marks.push({ x: (sx + ex) / 2, y: (sy + ey) / 2, b });
      upArrivals.push(b + 0.3);
    }
  });
  const pulse = Math.max(s(comm.aggregate_start || t0), ...upArrivals, travel);
  const evalBegin = Math.max(s(comm.eval_sent || tEnd), pulse + 0.5);
  const evalArrivals = [];
  D.clients.forEach((pid) => {
    const { x, y, a } = pos[pid];
    const cm = clientAt(R, pid).comm || {};
    if (!cm.eval_bytes_down) return;
    const sx = cx + sr * Math.cos(a), sy = cy + sr * Math.sin(a);
    const ex = x - nr * Math.cos(a), ey = y - nr * Math.sin(a);
    packets.push({ from: [sx, sy], to: [ex, ey], b: evalBegin, d: travel, r: 4.5, fill: faint });
    if (cm.eval_reply_at) {
      const b = Math.max(s(cm.eval_reply_at), evalBegin + travel);
      packets.push({ from: [ex, ey], to: [sx, sy], b, d: travel * 0.8, r: 3, fill: faint });
      evalArrivals.push(b + travel * 0.8);
    }
  });
  const finale = Math.max(evalBegin + travel, ...evalArrivals) + 0.2;
  const firstUp = upArrivals.length ? Math.min(...upArrivals) - travel : travel;
  const phaseTimes = [0, travel, Math.max(firstUp, travel), pulse, evalBegin];

  // server
  svg += `<circle cx="${cx}" cy="${cy}" r="${sr}" fill="${ink}"/>`;
  svg += `<circle id="pulse" cx="${cx}" cy="${cy}" r="${sr}" fill="none" stroke="${ink}" stroke-width="3" opacity="0"/>`;
  svg += `<text x="${cx}" y="${cy - 2}" text-anchor="middle" font-size="13" font-weight="650" fill="${surface}">Server</text>`;
  svg += `<text x="${cx}" y="${cy + 14}" text-anchor="middle" font-size="11" fill="${surface}" opacity="0.8">FedAvg</text>`;
  // clients
  const circ = 2 * Math.PI * (nr + 6);
  D.clients.forEach((pid) => {
    const { x, y, a } = pos[pid];
    const c = clientAt(R, pid);
    const color = c.status === "idle" ? cssVar("--page") : clientColor(pid, D.n);
    svg += `<circle cx="${x}" cy="${y}" r="${nr}" fill="${color}" stroke="${c.status === "idle" ? line : surface}" stroke-width="2"/>`;
    svg += `<text x="${x}" y="${y + 5}" text-anchor="middle" font-size="14" font-weight="700" fill="${c.status === "idle" ? faint : "#fff"}">${pid}</text>`;
    svg += `<circle class="ring" data-pid="${pid}" cx="${x}" cy="${y}" r="${nr + 6}" fill="none" stroke="${clientColor(pid, D.n)}" stroke-width="3.5" stroke-dasharray="${circ}" stroke-dashoffset="${circ}" transform="rotate(-90 ${x} ${y})"/>`;
    // labels: radially outside, except for nodes at the very top or bottom (beside them)
    const vertical = Math.abs(Math.cos(a)) <= 0.3;
    const lx = vertical ? x + nr + 14 : cx + (Rr + nr + 22) * Math.cos(a);
    const ly = vertical ? y - 12 : cy + (Rr + nr + 22) * Math.sin(a) - 6;
    const anchor = vertical || Math.cos(a) > 0.3 ? "start" : "end";
    const st = c.status === "ok" ? `${int(c.num_examples || 0)} images` : c.status === "failed" ? "disconnected" : "not sampled";
    svg += `<text class="lab strong" x="${lx}" y="${ly}" text-anchor="${anchor}">client ${pid}</text>`;
    svg += `<text class="lab" x="${lx}" y="${ly + 15}" text-anchor="${anchor}">${st}</text>`;
    if (D.raw) svg += `<text class="lab" x="${lx}" y="${ly + 30}" text-anchor="${anchor}" fill="${faint}">${mb(D.raw[pid])} of data, kept</text>`;
  });
  marks.forEach((m, i) => {
    svg += `<g class="mark" data-i="${i}" opacity="0"><circle cx="${m.x}" cy="${m.y}" r="11" fill="${failed}"/><text x="${m.x}" y="${m.y + 5}" text-anchor="middle" font-size="16" font-weight="700" fill="#fff">×</text></g>`;
  });
  packets.forEach((p, i) => {
    svg += `<circle class="pk" data-i="${i}" cx="${p.from[0]}" cy="${p.from[1]}" r="${p.r}" fill="${p.fill}" ${p.stroke ? `stroke="${p.stroke}" stroke-width="2"` : ""} opacity="0"/>`;
  });
  svg += `</svg>`;
  $("#star").classList.add("chart");
  $("#star").innerHTML = svg;

  // ---- timeline (real seconds)
  const TW = 600, rowH = 28, left = 82, top = 6, pw = TW - left - 14;
  const rowsTl = ["server", ...D.clients.map((p) => `client ${p}`)];
  const TH = top + rowH * rowsTl.length + 26;
  const X = (t) => left + ((t - t0) / real) * pw;
  let tl = `<svg viewBox="0 0 ${TW} ${TH}">`;
  rowsTl.forEach((label, i) => {
    const y = top + i * rowH;
    tl += `<text class="lab" x="${left - 10}" y="${y + 18}" text-anchor="end">${label}</text>`;
    tl += `<line class="gridline" x1="${left}" x2="${left + pw}" y1="${y + rowH - 1}" y2="${y + rowH - 1}"/>`;
  });
  if (comm.train_received) {
    const x1 = X(comm.train_received), x2 = X(comm.aggregate_end || comm.train_received);
    tl += `<rect x="${x1}" y="${top + 6}" width="${Math.max(x2 - x1, 3)}" height="14" rx="3" fill="${ink}"/>`;
  }
  if (comm.eval_sent) {
    const x1 = X(comm.eval_sent);
    tl += `<rect x="${x1}" y="${top + 6}" width="${Math.max(X(tEnd) - x1, 3)}" height="14" rx="3" fill="${faint}"/>`;
  }
  D.clients.forEach((pid, i) => {
    const y = top + (i + 1) * rowH;
    const c = clientAt(R, pid), cm = c.comm || {};
    if (c.status === "ok" && cm.train_reply_at) {
      const start = Math.max(cm.train_reply_at - (c.train_time || 0), t0);
      tl += `<rect x="${X(t0)}" y="${y + 11}" width="${Math.max(X(start) - X(t0), 0)}" height="5" rx="2" fill="${line}"/>`;
      tl += `<rect x="${X(start)}" y="${y + 6}" width="${Math.max(X(cm.train_reply_at) - X(start), 3)}" height="14" rx="3" fill="${clientColor(pid, D.n)}"><title>${secs(c.train_time || 0)} of training</title></rect>`;
    } else if (c.status === "failed" && cm.train_reply_at) {
      tl += `<rect x="${X(t0)}" y="${y + 11}" width="${Math.max(X(cm.train_reply_at) - X(t0), 0)}" height="5" rx="2" fill="${line}"/>`;
      tl += `<text x="${X(cm.train_reply_at)}" y="${y + 19}" text-anchor="middle" font-size="15" font-weight="700" fill="${failed}">×</text>`;
    } else if (c.status === "idle") {
      tl += `<text class="lab" x="${left + 4}" y="${y + 18}">not sampled</text>`;
    }
    if (cm.eval_reply_at) tl += `<rect x="${X(cm.eval_reply_at) - 1.5}" y="${y + 6}" width="3" height="14" fill="${faint}"/>`;
  });
  const axisY = top + rowH * rowsTl.length + 16;
  const step = real <= 8 ? 1 : real <= 16 ? 2 : 5;
  for (let sec = 0; sec <= real; sec += step) tl += `<text class="lab" x="${X(t0 + sec)}" y="${axisY}" text-anchor="middle">${sec} s</text>`;
  tl += `<line id="cursor" x1="${left}" x2="${left}" y1="${top}" y2="${top + rowH * rowsTl.length}" stroke="${ink}" stroke-width="1.5" stroke-dasharray="3 3"/>`;
  tl += `</svg>`;
  $("#timeline").classList.add("chart");
  $("#timeline").innerHTML = tl;
  $("#tl-sub").textContent = `Real duration ${secs(real)}, replayed in ${secs(span)}.` +
    (R.round === 1 ? " Round 1 includes the client start-up." : "") +
    " In simulation, clients share the CPUs: the thin part of each bar is the wait for a free CPU.";

  // ---- volumes
  const sum = (r, key) => Object.values(r.clients || {}).reduce((a, c) => a + ((c.comm || {})[key] || 0), 0);
  const cnt = (r, key) => Object.values(r.clients || {}).filter((c) => (c.comm || {})[key]).length;
  const soFar = D.rounds.filter((r) => r.round > 0 && r.round <= R.round);
  const keys = ["train_bytes_down", "train_bytes_up", "eval_bytes_down", "eval_bytes_up"];
  const cumul = soFar.reduce((a, r) => a + keys.reduce((b, kk) => b + sum(r, kk), 0), 0);
  const perClient = D.clients.map((pid) => soFar.reduce((a, r) => a + keys.reduce((b, kk) => b + ((clientAt(r, pid).comm || {})[kk] || 0), 0), 0));
  const rawTotal = D.raw ? D.raw.reduce((a, b) => a + b, 0) : null;
  $("#volumes").innerHTML = `
    <dl class="kpis">
      <dt>Sent to the clients</dt><dd>${cnt(R, "train_bytes_down")} × the global model, ${mb(sum(R, "train_bytes_down"))}</dd>
      <dt>Sent back to the server</dt><dd>${cnt(R, "train_bytes_up")} × trained weights, ${mb(sum(R, "train_bytes_up"))}</dd>
      <dt>Evaluation</dt><dd>${mb(sum(R, "eval_bytes_down"))} sent, ${int(sum(R, "eval_bytes_up"))} bytes of metrics received</dd>
      <dt>Since round 1</dt><dd>${mb(cumul)} exchanged in ${soFar.length} rounds</dd>
      <dt>Client data</dt><dd class="strong">${rawTotal != null ? mb(rawTotal) : "—"}, never sent</dd>
    </dl>
    <table class="plain"><thead><tr><th>client</th><th class="num">data kept</th><th class="num">exchanged since round 1</th></tr></thead><tbody>
    ${D.clients.map((pid, i) => `<tr><td><span class="dotc" style="background:${clientColor(pid, D.n)}"></span>client ${pid}</td><td class="num">${D.raw ? mb(D.raw[pid]) : "—"}</td><td class="num">${mb(perClient[i])}</td></tr>`).join("")}
    </tbody></table>
    <p class="note" style="margin:10px 0 0">Clients never talk to each other: every message goes through the server.</p>`;

  // ---- animation
  const pkEls = [...document.querySelectorAll("#star .pk")];
  const ringEls = Object.fromEntries([...document.querySelectorAll("#star .ring")].map((e) => [e.dataset.pid, e]));
  const markEls = [...document.querySelectorAll("#star .mark")];
  const pulseEl = $("#pulse"), cursor = $("#cursor");
  const phaseEls = [...document.querySelectorAll("#phases li")];
  const final = $("#final");
  final.innerHTML = `New global model: <b>${pct(R.accuracy)}</b> accuracy at round ${R.round}.`;
  const ease = (u) => (u < 0.5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2);

  function frame(t) {
    packets.forEach((p, i) => {
      const u = (t - p.b) / p.d;
      const el = pkEls[i];
      if (u < 0 || u > 1) { el.setAttribute("opacity", "0"); return; }
      const e = ease(u);
      el.setAttribute("cx", p.from[0] + (p.to[0] - p.from[0]) * e);
      el.setAttribute("cy", p.from[1] + (p.to[1] - p.from[1]) * e);
      el.setAttribute("opacity", "1");
    });
    rings.forEach((r) => {
      const u = clamp((t - r.b) / r.d, 0, 1);
      ringEls[r.pid].setAttribute("stroke-dashoffset", circ * (1 - u));
    });
    marks.forEach((m, i) => markEls[i].setAttribute("opacity", t >= m.b ? "1" : "0"));
    const pu = (t - pulse) / 0.9;
    if (pu >= 0 && pu <= 1) {
      pulseEl.setAttribute("r", sr * (1 + 0.7 * pu));
      pulseEl.setAttribute("opacity", 0.7 * (1 - pu));
    } else pulseEl.setAttribute("opacity", "0");
    phaseEls.forEach((el, i) => el.classList.toggle("on", t >= phaseTimes[i]));
    cursor.setAttribute("transform", `translate(${clamp((t - 0.6) / span, 0, 1) * pw},0)`);
    final.style.visibility = t >= finale ? "visible" : "hidden";
  }

  if (matchMedia("(prefers-reduced-motion: reduce)").matches) { frame(1e9); return; }
  const start = performance.now();
  const tick = (now) => {
    const t = (now - start) / 1000;
    frame(t);
    if (t < finale + 0.5) state.net.raf = requestAnimationFrame(tick);
  };
  state.net.raf = requestAnimationFrame(tick);
}

// ============================================================================ view: compare
async function getRun(name) {
  const info = state.runs.find((r) => r.name === name);
  const key = info ? `${info.name}:${info.updated}` : name;
  const hit = state.cache.get(name);
  if (hit && hit.key === key) return hit.payload;
  const payload = await getJSON(`api/run/${encodeURIComponent(name)}`);
  state.cache.set(name, { key, payload });
  return payload;
}

async function renderCompare() {
  const v = $("#view");
  if (!state.compare.size) state.runs.slice(0, 3).forEach((r) => state.compare.add(r.name));
  const chosen = state.runs.filter((r) => state.compare.has(r.name)).slice(0, 8);
  v.innerHTML = `
    <section class="panel"><h2>Compare runs</h2>
      <p class="sub">Global model accuracy, round by round. Tick up to 8 runs.</p>
      <div class="picker">${state.runs.map((r) => `<label><input type="checkbox" value="${esc(r.name)}" ${state.compare.has(r.name) ? "checked" : ""}>${esc(r.name)}</label>`).join("")}</div>
      <div id="c-compare"></div><div id="t-compare"></div></section>`;
  v.querySelectorAll(".picker input").forEach((cb) => cb.addEventListener("change", () => {
    if (cb.checked) state.compare.add(cb.value); else state.compare.delete(cb.value);
    renderCompare();
  }));
  if (!chosen.length) { $("#c-compare").innerHTML = `<p class="note">No run selected.</p>`; return; }
  const payloads = await Promise.all(chosen.map((r) => getRun(r.name).catch(() => null)));
  const Ds = payloads.filter(Boolean).map(derive);
  const xMax = Math.max(...Ds.map((d) => d.total));
  lineChart($("#c-compare"), {
    xMax,
    series: Ds.map((d, i) => ({ name: d.name, color: cssVar(`--c${i}`), width: 2.4, end: true,
      points: d.rounds.map((r) => [r.round, r.accuracy]) })),
  });
  const rowsHtml = Ds.map((d, i) => {
    const acc = d.rounds.map((r) => r.accuracy);
    const times = d.rounds.map((r) => r.time);
    const steps = times.slice(2).map((t, j) => t - times[j + 1]).sort((a, b) => a - b);
    const med = steps.length ? steps[Math.floor(steps.length / 2)] : null;
    return `<tr><td><span class="dotc" style="background:${cssVar(`--c${i}`)}"></span>${esc(d.name)}</td>
      <td>${esc(describeConfig(d.run.config))}</td>
      <td class="num">${pct(acc[1])}</td><td class="num">${pct(acc[Math.min(5, acc.length - 1)])}</td>
      <td class="num">${pct(acc[acc.length - 1])}</td><td class="num">${pct(Math.max(...acc))}</td>
      <td class="num">${med != null ? secs(med) : "—"}</td></tr>`;
  }).join("");
  $("#t-compare").innerHTML = `<table class="plain" style="margin-top:16px"><thead><tr><th>run</th><th>configuration</th>
    <th class="num">round 1</th><th class="num">round 5</th><th class="num">last</th><th class="num">best</th><th class="num">round duration</th></tr></thead>
    <tbody>${rowsHtml}</tbody></table>`;
}

// ============================================================================ shell
function renderRunPicker() {
  const sel = $("#run");
  const opts = [`<option value="__latest__">Follow the latest run</option>`].concat(state.runs.map((r) => {
    const status = r.finished ? "finished" : `round ${r.round} of ${r.total}`;
    return `<option value="${esc(r.name)}">${esc(r.name)} (${status})</option>`;
  }));
  const html = opts.join("");
  if (sel.dataset.html !== html) { sel.innerHTML = html; sel.dataset.html = html; }
  sel.value = state.follow ? "__latest__" : state.run || "__latest__";
}

function renderLive(info) {
  const el = $("#live");
  if (state.serverDown) {
    el.className = "live"; el.querySelector(".txt").textContent = "notebook server unreachable";
    return;
  }
  if (!info) { el.className = "live"; el.querySelector(".txt").textContent = "no run"; return; }
  const running = !info.finished;
  el.className = "live" + (running ? " running" : "");
  el.querySelector(".txt").textContent = running
    ? (info.round ? `round ${info.round} of ${info.total}, running` : "starting")
    : `finished, ${info.round} rounds`;
}

function render(dataChanged = true) {
  document.querySelectorAll(".tab").forEach((t) => t.setAttribute("aria-selected", String(t.dataset.view === state.view)));
  writeHash();
  if (state.view === "compare") { renderCompare(); return; }
  if (!state.payload) {
    cancelAnimationFrame(state.net.raf);
    $("#view").innerHTML = state.runs.length
      ? `<div class="empty">Loading…</div>`
      : `<div class="empty">No run yet. Run a <code>viz.run(...)</code> cell in the notebook: it will show up here automatically.</div>`;
    return;
  }
  const D = derive(state.payload);
  if (state.view === "together") renderTogether(D);
  else if (state.view === "run") renderRun(D);
  else if (state.view === "network") {
    // Replay only when a new round arrives (or on view/run change), not at every poll.
    const lastNet = D.rounds.filter((r) => r.round > 0 && r.comm && r.comm.train_sent).slice(-1)[0];
    const key = `${D.name}:${lastNet ? lastNet.round : 0}`;
    const runChanged = !state.net.key || state.net.key.split(":")[0] !== D.name;
    if (runChanged) state.net.latest = true;
    const newRound = key !== state.net.key;
    state.net.key = key;
    if (dataChanged === "view" || runChanged || !$("#star") || (newRound && state.net.latest)) renderNetwork(D);
  }
}

async function poll() {
  try {
    const runs = await getJSON("api/runs");
    state.serverDown = false;
    state.runs = runs;
    if (state.follow && runs.length) state.run = runs[0].name;
    else if (!state.run && runs.length) state.run = runs[0].name;
    renderRunPicker();
    const info = runs.find((r) => r.name === state.run);
    const key = info ? `${info.name}:${info.updated}` : null;
    if (key && key !== state.payloadKey) {
      state.payload = await getJSON(`api/run/${encodeURIComponent(state.run)}`);
      state.payloadKey = key;
      render(true);
    } else if (!info && state.payload) {
      state.payload = null; state.payloadKey = null; render(true);
    } else if (!state.payload) render(true);
    renderLive(info);
  } catch (err) {
    state.serverDown = true;
    renderLive(null);
  }
  setTimeout(poll, 2000);
}

document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => {
  state.view = t.dataset.view;
  render("view");
}));
$("#run").addEventListener("change", (e) => {
  if (e.target.value === "__latest__") { state.follow = true; }
  else { state.follow = false; state.run = e.target.value; }
  state.payloadKey = null;
  state.net.latest = true;
  writeHash();
  getJSON(`api/run/${encodeURIComponent(state.follow && state.runs.length ? state.runs[0].name : state.run)}`)
    .then((p) => { state.payload = p; render("view"); })
    .catch(() => {});
});
window.addEventListener("hashchange", () => { readHash(); render("view"); });
let resizeTimer = null;
window.addEventListener("resize", () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => { if (state.view !== "network") render("resize"); }, 200);
});

readHash();
render("view");
poll();
