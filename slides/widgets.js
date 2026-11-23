/*
 * widgets.js - interactive pieces of the workshop deck (Marp, HTML build).
 *
 * Loaded by slides/talk.md. No dependencies, works offline.
 * Each widget is found by its CSS class and draws its initial state at load,
 * so the PDF export shows a meaningful still frame.
 * Clicks inside a widget never change slide (stopPropagation).
 */
(() => {
  "use strict";
  const init = () => {

    const SVG = "http://www.w3.org/2000/svg";
    const CLASSES = ["T-shirt", "Trouser", "Pullover", "Dress", "Coat",
                     "Sandal", "Shirt", "Sneaker", "Bag", "Boot"];
    const isBespoke = () => !!document.querySelector(".bespoke-marp-parent");
    const el = (tag, attrs = {}, parent = null) => {
      const n = document.createElementNS(SVG, tag);
      for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
      if (parent) parent.appendChild(n);
      return n;
    };
    const keepClicks = (root) => {
      ["click", "dblclick", "pointerdown", "keydown"].forEach((t) =>
        root.addEventListener(t, (e) => e.stopPropagation()));
    };
    // Run fn once, the first time `node` becomes visible in the presentation.
    const onFirstShow = (node, fn) => {
      let done = false;
      new IntersectionObserver((entries) => {
        if (!done && isBespoke() && entries.some((x) => x.isIntersecting)) { done = true; fn(); }
      }).observe(node);
    };
    // Presentation (bespoke HTML) vs still render (PDF): chooses each widget's initial state.
    const live = isBespoke();

    // Seeded PRNG (mulberry32) and Gamma / Dirichlet sampling (Marsaglia-Tsang).
    const rng = (seed) => () => {
      seed |= 0; seed = (seed + 0x6d2b79f5) | 0;
      let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
    const normal = (r) => {
      let u = 0, v = 0;
      while (u === 0) u = r();
      while (v === 0) v = r();
      return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
    };
    const gamma = (a, r) => {
      if (a < 1) return gamma(a + 1, r) * Math.pow(r(), 1 / a);
      const d = a - 1 / 3, c = 1 / Math.sqrt(9 * d);
      for (;;) {
        let x, v;
        do { x = normal(r); v = 1 + c * x; } while (v <= 0);
        v = v * v * v;
        const u = r();
        if (u < 1 - 0.0331 * x ** 4) return d * v;
        if (Math.log(u) < 0.5 * x * x + d * (1 - v + Math.log(v))) return d * v;
      }
    };
    const dirichlet = (alpha, k, r) => {
      const g = Array.from({ length: k }, () => Math.max(gamma(alpha, r), 1e-12));
      const s = g.reduce((a, b) => a + b, 0);
      return g.map((x) => x / s);
    };

    /* ---------------------------------------------------------------------
     * 1. Countdown: <div class="countdown" data-minutes="15">15:00</div>
     *    Starts when its slide is first shown. Click: pause/resume. Double-click: reset.
     * ------------------------------------------------------------------- */
    document.querySelectorAll(".countdown").forEach((node) => {
      const total = Number(node.dataset.minutes || 15) * 60;
      let left = total, timer = null;
      const show = () => {
        const m = Math.floor(left / 60), s = left % 60;
        node.textContent = `${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
        node.classList.toggle("ending", left > 0 && left <= 60);
        node.classList.toggle("done", left === 0);
      };
      const stop = () => { clearInterval(timer); timer = null; };
      const tick = () => { if (left > 0) { left -= 1; show(); } else stop(); };
      const start = () => { if (!timer && left > 0) timer = setInterval(tick, 1000); };
      keepClicks(node);
      node.addEventListener("click", () => (timer ? stop() : start()));
      node.addEventListener("dblclick", () => { stop(); left = total; show(); });
      show();
      onFirstShow(node, start);
    });

    /* ---------------------------------------------------------------------
     * 2. Round loop stepper: <div class="widget loop-widget"></div>
     *    Server at the top, 5 clients below; "Next step" walks the 5 steps.
     * ------------------------------------------------------------------- */
    const STEPS = [
      ["Send", "The server sends the current global model to the clients of the round."],
      ["Train", "Each client trains locally on its own data, for a few epochs."],
      ["Return", "Clients send back their updated weights. Never their data."],
      ["Aggregate", "The server averages the weights, weighted by each client's data size (FedAvg)."],
      ["Evaluate", "The new global model is evaluated, then the next round starts."],
    ];
    document.querySelectorAll(".loop-widget").forEach((root) => {
      keepClicks(root);
      const svg = el("svg", { viewBox: "0 0 600 300", class: "loop" }, root);
      const server = { x: 300, y: 50 };
      const clients = [80, 190, 300, 410, 520].map((x) => ({ x, y: 240 }));
      const groups = STEPS.map(() => el("g", { class: "step" }, svg));
      // Static layer: server and clients.
      el("rect", { x: 240, y: 22, width: 120, height: 56, rx: 10, fill: "#1f3d37" }, svg);
      const st = el("text", { x: 300, y: 56, "text-anchor": "middle", fill: "#fff", "font-size": 18, "font-weight": 700 }, svg);
      st.textContent = "Server";
      clients.forEach((c, i) => {
        el("rect", { x: c.x - 42, y: c.y - 26, width: 84, height: 52, rx: 10, fill: "#fff", stroke: "#3d8b78", "stroke-width": 3 }, svg);
        const t = el("text", { x: c.x, y: c.y + 6, "text-anchor": "middle", fill: "#1f3d37", "font-size": 16, "font-weight": 600 }, svg);
        t.textContent = `Client ${i + 1}`;
      });
      // Step layers.
      clients.forEach((c) => {
        el("line", { x1: server.x, y1: server.y + 28, x2: c.x, y2: c.y - 30, stroke: "#3d8b78", "stroke-width": 3, "marker-end": "url(#arrow)" }, groups[0]);
        el("circle", { cx: c.x + 34, cy: c.y - 22, r: 11, fill: "#f2c46d" }, groups[1]);
        el("line", { x1: c.x, y1: c.y - 30, x2: server.x, y2: server.y + 28, stroke: "#c9803a", "stroke-width": 3, "stroke-dasharray": "6 5" }, groups[2]);
      });
      const agg = el("text", { x: 380, y: 56, fill: "#1f3d37", "font-size": 26, "font-weight": 700 }, groups[3]);
      agg.textContent = "Σ nₖ·wₖ / n";
      el("circle", { cx: 240, cy: 50, r: 13, fill: "#8fd3be" }, groups[4]);
      const ck = el("text", { x: 240, y: 56, "text-anchor": "middle", "font-size": 16, "font-weight": 700, fill: "#142824" }, groups[4]);
      ck.textContent = "✓";
      const defs = el("defs", {}, svg);
      const m = el("marker", { id: "arrow", viewBox: "0 0 10 10", refX: 9, refY: 5, markerWidth: 6, markerHeight: 6, orient: "auto-start-reverse" }, defs);
      el("path", { d: "M0,0 L10,5 L0,10 z", fill: "#3d8b78" }, m);

      const bar = document.createElement("div");
      bar.style.cssText = "display:flex;gap:10px;align-items:center;margin-top:8px";
      const next = document.createElement("button");
      next.textContent = "Next step ▸";
      const reset = document.createElement("button");
      reset.className = "ghost";
      reset.textContent = "Reset";
      const cap = document.createElement("div");
      cap.className = "caption";
      bar.append(next, reset);
      root.append(bar, cap);

      // Still frame (PDF): all steps visible. Live: walk them one by one.
      let k = STEPS.length - 1;
      const render = (all = false) => {
        groups.forEach((g, i) => g.classList.toggle("on", all || i === k));
        cap.innerHTML = all
          ? "One round = <b>send → train → return → aggregate → evaluate</b>. Repeat for N rounds."
          : `<b>${k + 1}. ${STEPS[k][0]}</b>: ${STEPS[k][1]}`;
      };
      const clear = () => {
        k = -1;
        groups.forEach((g) => g.classList.remove("on"));
        cap.textContent = "Click “Next step” to run one round.";
      };
      next.addEventListener("click", () => { k = (k + 1) % STEPS.length; render(); });
      reset.addEventListener("click", clear);
      if (live) clear(); else render(true);
    });

    /* ---------------------------------------------------------------------
     * 3. FedAvg tug-of-war: <div class="widget fedavg-widget"></div>
     *    Two clients with their own optimum; the global model is the
     *    data-weighted average. Sliders: data share of client A, data difference.
     * ------------------------------------------------------------------- */
    document.querySelectorAll(".fedavg-widget").forEach((root) => {
      keepClicks(root);
      const svg = el("svg", { viewBox: "0 0 600 260" }, root);
      const cx = 300, cy = 130;
      const ellA = el("ellipse", { rx: 120, ry: 70, fill: "#3d8b7822", stroke: "#3d8b78", "stroke-width": 2 }, svg);
      const ellB = el("ellipse", { rx: 120, ry: 70, fill: "#c9803a22", stroke: "#c9803a", "stroke-width": 2 }, svg);
      const pA = el("circle", { r: 9, fill: "#3d8b78" }, svg);
      const pB = el("circle", { r: 9, fill: "#c9803a" }, svg);
      const lA = el("text", { "font-size": 15, "font-weight": 700, fill: "#3d8b78", "text-anchor": "middle" }, svg);
      const lB = el("text", { "font-size": 15, "font-weight": 700, fill: "#c9803a", "text-anchor": "middle" }, svg);
      const link = el("line", { stroke: "#9aa8a4", "stroke-width": 2, "stroke-dasharray": "4 4" }, svg);
      const g = el("circle", { r: 13, fill: "#142824" }, svg);
      const lg = el("text", { "font-size": 15, "font-weight": 700, fill: "#142824", "text-anchor": "middle" }, svg);
      lA.textContent = "Client A optimum";
      lB.textContent = "Client B optimum";
      lg.textContent = "Global model";
      svg.insertBefore(link, pA);

      const controls = document.createElement("div");
      controls.className = "cols";
      controls.style.gap = "24px";
      controls.innerHTML = `
        <div><label>Client A holds <span class="readout" data-r="share">50</span> % of the data</label>
          <input type="range" min="5" max="95" value="50" data-in="share"></div>
        <div><label>How different the data are: <span class="readout" data-r="gap">high</span></label>
          <input type="range" min="0" max="100" value="80" data-in="gap"></div>`;
      const cap = document.createElement("div");
      cap.className = "caption";
      root.append(controls, cap);
      const share = controls.querySelector('[data-in="share"]');
      const gap = controls.querySelector('[data-in="gap"]');

      const render = () => {
        const w = Number(share.value) / 100, d = Number(gap.value) / 100;
        const half = 20 + 200 * d;
        const ax = cx - half, bx = cx + half;
        const ay = cy + 30 * d, by = cy - 30 * d;
        const gx = w * ax + (1 - w) * bx, gy = w * ay + (1 - w) * by;
        [[ellA, ax, ay], [ellB, bx, by]].forEach(([e, x, y]) => { e.setAttribute("cx", x); e.setAttribute("cy", y); });
        pA.setAttribute("cx", ax); pA.setAttribute("cy", ay);
        pB.setAttribute("cx", bx); pB.setAttribute("cy", by);
        lA.setAttribute("x", ax); lA.setAttribute("y", ay + 95);
        lB.setAttribute("x", bx); lB.setAttribute("y", by - 82);
        link.setAttribute("x1", ax); link.setAttribute("y1", ay); link.setAttribute("x2", bx); link.setAttribute("y2", by);
        g.setAttribute("cx", gx); g.setAttribute("cy", gy);
        lg.setAttribute("x", gx); lg.setAttribute("y", gy - 22);
        controls.querySelector('[data-r="share"]').textContent = Math.round(w * 100);
        controls.querySelector('[data-r="gap"]').textContent = d < 0.25 ? "low (IID-like)" : d < 0.6 ? "medium" : "high (non-IID)";
        cap.innerHTML = d < 0.25
          ? "Clients want almost the same model: the average is good for both."
          : "The average lands <b>between</b> the clients, far from each optimum: this is <b>client drift</b>.";
      };
      share.addEventListener("input", render);
      gap.addEventListener("input", render);
      render();
    });

    /* ---------------------------------------------------------------------
     * 4. Dirichlet α heatmap: <div class="widget alpha-widget" data-alpha="0.1" data-seed="42"></div>
     *    Same scheme as flwr-datasets' DirichletPartitioner: for each class,
     *    split its images over the 5 clients with proportions ~ Dir(α).
     *    Illustrative only: it is not the exact partition of the hands-on.
     * ------------------------------------------------------------------- */
    document.querySelectorAll(".alpha-widget").forEach((root) => {
      keepClicks(root);
      const nClients = 5, perClass = 6000;
      const steps = [100, 10, 1, 0.3, 0.1, 0.03];
      const start = Math.max(0, steps.indexOf(Number(root.dataset.alpha || 0.1)));
      const seed = Number(root.dataset.seed || 42);
      const svg = el("svg", { viewBox: "0 0 600 290", class: "heat" }, root);
      const x0 = 90, y0 = 66, cw = 46, ch = 38;
      CLASSES.forEach((name, j) => {
        const x = x0 + j * cw + cw / 2;
        const t = el("text", { x, y: 58, class: "col", transform: `rotate(-40 ${x} 58)` }, svg);
        t.textContent = name;
      });
      const cells = [], totals = [];
      for (let i = 0; i < nClients; i += 1) {
        const t = el("text", { x: 8, y: y0 + i * ch + ch / 2 + 5 }, svg);
        t.textContent = `Client ${i + 1}`;
        cells.push(CLASSES.map((_, j) => el("rect", { x: x0 + j * cw, y: y0 + i * ch, width: cw, height: ch, rx: 4, class: "cell" }, svg)));
        totals.push(el("text", { x: x0 + 10 * cw + 10, y: y0 + i * ch + ch / 2 + 5 }, svg));
      }
      const head = el("text", { x: x0 + 10 * cw + 10, y: 58 }, svg);
      head.textContent = "images";

      const controls = document.createElement("div");
      controls.innerHTML = `<label>α = <span class="readout">–</span></label>
        <input type="range" min="0" max="${steps.length - 1}" step="1" value="${start}">
        <div class="tiny" style="display:flex;justify-content:space-between"><span>α = 100 · everyone has the same mix</span><span>α = 0.03 · each client has a few classes</span></div>`;
      root.appendChild(controls);
      const slider = controls.querySelector("input");
      const readout = controls.querySelector(".readout");

      const render = () => {
        const alpha = steps[Number(slider.value)];
        readout.textContent = alpha;
        const r = rng(seed);
        const counts = Array.from({ length: nClients }, () => Array(10).fill(0));
        for (let j = 0; j < 10; j += 1) {
          dirichlet(alpha, nClients, r).forEach((p, i) => { counts[i][j] = Math.round(p * perClass); });
        }
        counts.forEach((row, i) => {
          row.forEach((n, j) => {
            const a = Math.min(1, n / (perClass / nClients * 2.5));
            cells[i][j].setAttribute("fill", n === 0 ? "#f4f6f5" : `rgba(31,61,55,${0.08 + 0.92 * a})`);
          });
          totals[i].textContent = row.reduce((s, v) => s + v, 0).toLocaleString("en-US");
        });
      };
      slider.addEventListener("input", render);
      render();
    });

    /* ---------------------------------------------------------------------
     * 5. Partial participation: <div class="widget participation-widget"></div>
     *    Click clients in or out of the round; the bar shows which classes
     *    the aggregated model sees this round. Illustrative class mapping.
     * ------------------------------------------------------------------- */
    document.querySelectorAll(".participation-widget").forEach((root) => {
      keepClicks(root);
      // Illustrative non-IID mapping (not the hands-on partition).
      const owns = [[0, 1, 2], [2, 3, 4], [5, 6], [6, 7, 8], [8, 9, 0]];
      const on = [true, true, true, true, true];
      const chips = document.createElement("div");
      chips.className = "chips";
      const bar = document.createElement("div");
      bar.className = "classbar";
      const cap = document.createElement("div");
      cap.className = "caption";
      root.append(chips, bar, cap);
      const chipEls = owns.map((_, i) => {
        const c = document.createElement("span");
        c.className = "chip";
        c.textContent = `Client ${i + 1}`;
        c.addEventListener("click", () => { on[i] = !on[i]; render(); });
        chips.appendChild(c);
        return c;
      });
      const classEls = CLASSES.map((name) => {
        const d = document.createElement("div");
        d.textContent = name;
        bar.appendChild(d);
        return d;
      });
      const render = () => {
        const seen = new Set();
        owns.forEach((cls, i) => { if (on[i]) cls.forEach((c) => seen.add(c)); });
        chipEls.forEach((c, i) => c.classList.toggle("on", on[i]));
        classEls.forEach((d, j) => d.classList.toggle("seen", seen.has(j)));
        const n = on.filter(Boolean).length;
        cap.innerHTML = n === 0
          ? "Nobody in this round: the global model stays unchanged."
          : `<b>${n} of 5</b> clients in this round: the update only reflects <b>${seen.size} of 10</b> classes.`;
      };
      render();
    });

    /* ---------------------------------------------------------------------
     * 6. Poll reveal (debrief): <div class="widget poll"> rows with data-value </div>
     *    Bars stay empty until the presenter clicks "Reveal".
     * ------------------------------------------------------------------- */
    document.querySelectorAll(".poll").forEach((root) => {
      keepClicks(root);
      const rows = [...root.querySelectorAll(".row")];
      const max = Math.max(...rows.map((r) => Number(r.dataset.value)));
      const btn = document.createElement("button");
      btn.textContent = "Reveal";
      root.appendChild(btn);
      const reveal = (yes) => {
        root.classList.toggle("revealed", yes);
        rows.forEach((r) => {
          r.querySelector(".bar").style.width = yes ? `${(Number(r.dataset.value) / max) * 100}%` : "0";
        });
        btn.textContent = yes ? "Hide" : "Reveal";
      };
      btn.addEventListener("click", () => reveal(!root.classList.contains("revealed")));
      // Live presentation: start hidden. PDF / static view: show the answer.
      reveal(!live);
    });
  };
  if (document.readyState === "complete") init();
  else window.addEventListener("load", init);
})();
