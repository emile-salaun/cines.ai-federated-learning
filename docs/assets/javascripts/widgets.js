/* =============================================================================
   widgets.js - Decorative and explanatory widgets of the site. No dependencies,
   works offline. Each widget is a placeholder element found by its
   data-ws-widget attribute and drawn here as inline SVG.

   1. fl-round   <div data-ws-widget="fl-round"></div>    (index.md, hero)
                 Animated federated round: broadcast, local training,
                 updates back, aggregation. Round counter 1..10.
   2. demo-map   <figure data-ws-widget="demo-map" data-sites="adastra,jeanzay"
                         data-tbc="jeanzay">
                 (demo.md) Map of France with the two demo sites and model
                 updates travelling between them. Sites: see SITES below.
                 data-tbc (optional) lists sites shown as "to be confirmed":
                 dashed marker and label. Remove it once the site is official.

   Both respect "reduce motion" (a still frame is drawn) and pause when off
   screen or when the tab is hidden.
   ============================================================================= */
(() => {
  "use strict";

  const SVG = "http://www.w3.org/2000/svg";
  const el = (tag, attrs = {}, parent = null) => {
    const n = document.createElementNS(SVG, tag);
    for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
    if (parent) parent.appendChild(n);
    return n;
  };
  const reduceMotion = () =>
    window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const ease = (t) => (t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2);
  const lerp = (a, b, t) => a + (b - a) * t;

  // Animation loop that only runs while `node` is on screen and the tab is visible.
  // frame(elapsedMs) draws one frame; elapsed time freezes while paused.
  function animate(node, frame) {
    let onScreen = false, raf = null, last = null, elapsed = 0;
    const loop = (now) => {
      if (last !== null) elapsed += Math.min(now - last, 100);
      last = now;
      frame(elapsed);
      raf = requestAnimationFrame(loop);
    };
    const update = () => {
      const run = onScreen && !document.hidden && node.isConnected;
      if (run && raf === null) { last = null; raf = requestAnimationFrame(loop); }
      if (!run && raf !== null) { cancelAnimationFrame(raf); raf = null; }
    };
    new IntersectionObserver((entries) => {
      onScreen = entries.some((e) => e.isIntersecting);
      update();
    }).observe(node);
    document.addEventListener("visibilitychange", update);
  }

  // --- 1. Hero: one federated round --------------------------------------------
  const ROUNDS = 10;
  const PHASE_MS = 1400;
  const PHASES = [
    "The server sends the global model",
    "Each client trains on its own data",
    "Only model updates go back. The data stays.",
    "The server averages them (FedAvg)",
  ];

  function flRound(box) {
    const W = 360, H = 345, CX = 180, CY = 172, R = 112, N = 5;
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, class: "ws-round", role: "img",
      "aria-label": "Animation of a federated learning round: the server sends the model "
        + "to 5 clients, they train on their local data and send back only model updates, "
        + "which the server averages." });
    const links = el("g", { class: "ws-round__links" }, svg);
    const packets = el("g", { class: "ws-round__packets" }, svg);

    // Clients: a ring and three data bars (different mixes = non-IID).
    const clients = Array.from({ length: N }, (_, i) => {
      const a = (-90 + (360 / N) * i) * Math.PI / 180;
      const x = CX + R * Math.cos(a), y = CY + R * Math.sin(a);
      el("line", { x1: CX, y1: CY, x2: x, y2: y }, links);
      const g = el("g", { class: "ws-round__client", transform: `translate(${x} ${y})` }, svg);
      el("circle", { r: 26, class: "ws-round__halo" }, g);
      el("circle", { r: 21, class: "ws-round__node" }, g);
      [0, 1, 2].forEach((b) => {
        const h = 5 + ((i * 7 + b * 5) % 13);
        el("rect", { x: -9 + b * 7, y: 9 - h, width: 5, height: h, rx: 1,
          class: `ws-round__bar ws-round__bar--${b}` }, g);
      });
      return { x, y, g };
    });

    // Server: rounded square with three "rack" lines.
    const server = el("g", { class: "ws-round__server", transform: `translate(${CX} ${CY})` }, svg);
    el("rect", { x: -34, y: -34, width: 68, height: 68, rx: 14, class: "ws-round__halo" }, server);
    el("rect", { x: -26, y: -26, width: 52, height: 52, rx: 10, class: "ws-round__node" }, server);
    [-10, 0, 10].forEach((dy) =>
      el("line", { x1: -13, y1: dy, x2: 13, y2: dy, class: "ws-round__rack" }, server));

    const roundText = el("text", { x: W / 2, y: 18, class: "ws-round__round" }, svg);
    const caption = el("text", { x: W / 2, y: H - 6, class: "ws-round__caption" }, svg);
    const dots = clients.map(() => el("circle", { r: 5.5 }, packets));

    box.appendChild(svg);

    const draw = (ms) => {
      const step = Math.floor(ms / PHASE_MS);
      const phase = step % 4;
      const t = ease((ms % PHASE_MS) / PHASE_MS);
      const round = (Math.floor(step / 4) % ROUNDS) + 1;
      roundText.textContent = `Round ${round} / ${ROUNDS}`;
      caption.textContent = PHASES[phase];
      svg.dataset.phase = String(phase);
      clients.forEach((c, i) => {
        const d = dots[i];
        const out = phase === 0, back = phase === 2;
        d.style.opacity = out || back ? String(Math.min(1, Math.sin(Math.PI * t) * 3)) : "0";
        d.setAttribute("class", back ? "is-update" : "is-model");
        const k = out ? t : 1 - t;
        d.setAttribute("cx", lerp(CX, c.x, k).toFixed(1));
        d.setAttribute("cy", lerp(CY, c.y, k).toFixed(1));
      });
    };

    if (reduceMotion()) {
      // Still frame: updates halfway back to the server.
      draw(2 * PHASE_MS + PHASE_MS / 2);
      roundText.textContent = "One round";
      caption.textContent = "Model out, training on local data, updates back";
      return;
    }
    draw(0);
    animate(box, draw);
  }

  // --- 2. Demo map -------------------------------------------------------------
  // France outline: Natural Earth 1:50m admin-0 (public domain), metropolitan
  // France and Corsica, equirectangular projection scaled by cos(46.5 deg),
  // simplified (Ramer-Douglas-Peucker, 0.5 unit). Width 400 units.
  const FRANCE = {
    w: 400, h: 394.1, cos: 0.688354575693754, minx: -3.2782886667415037,
    miny: -51.097119, s: 40.58231025413343,
    d: "M397.9 336.5L397.1 342.5L399.2 346.8L399.8 363.9L395.7 372.2L394.9 382.2L389.7 394.1L381.5 388.8L379.1 385.9L381.3 381.3L376.6 378.9L377.7 374.4L377.2 372.2L373.9 372.0L373.7 370.8L376.1 367.4L376.1 365.3L372.9 362.7L372.3 360.3L375.4 357.7L374.0 355.2L372.3 354.7L374.4 351.9L376.4 346.9L379.3 344.5L385.7 342.3L388.3 339.4L392.5 341.0L393.9 338.1L393.7 330.9L394.6 327.9L396.1 327.7L397.4 329.4L397.9 336.5ZM345.8 142.2L342.4 144.1L340.3 147.8L338.2 148.7L334.3 148.7L332.4 146.4L330.1 146.4L327.7 147.9L325.8 150.3L326.4 151.6L328.1 152.0L328.6 153.2L319.3 165.2L313.4 168.4L312.1 176.2L305.1 182.1L302.5 188.2L302.3 189.5L304.1 191.5L303.3 195.5L299.8 198.1L299.9 200.7L300.8 201.1L303.1 200.9L306.2 199.0L308.3 196.6L307.2 193.4L309.6 190.9L312.6 189.4L316.8 189.1L322.3 190.4L322.6 194.1L323.5 195.7L322.2 200.2L327.3 206.2L329.2 209.9L326.9 212.2L323.1 214.4L322.7 217.4L323.2 218.6L325.3 220.2L329.0 227.1L332.9 231.2L330.8 237.7L328.1 238.7L324.2 241.9L320.0 241.6L318.2 242.6L318.4 244.7L320.0 246.5L321.3 250.6L323.0 252.2L327.8 253.7L329.4 258.9L327.5 260.5L324.2 267.3L325.6 270.6L325.1 272.1L325.8 274.4L327.7 276.7L332.8 279.8L338.9 282.8L346.4 281.3L347.5 284.6L342.1 293.5L342.4 297.5L340.8 298.1L339.6 297.5L339.1 298.9L333.7 301.9L324.8 310.8L320.7 313.4L319.0 318.0L314.5 321.7L309.2 323.0L303.9 325.7L301.5 324.5L295.3 324.6L291.5 321.4L284.1 319.3L281.7 314.6L276.1 314.4L274.8 313.7L274.4 310.6L264.7 313.5L251.0 309.1L246.3 304.5L242.3 305.7L238.8 309.9L224.1 320.8L218.3 332.0L218.0 335.2L219.4 345.2L222.8 351.7L216.0 350.2L213.8 350.7L208.5 352.6L207.6 353.2L207.1 355.4L194.5 352.1L189.8 354.8L188.5 354.6L186.9 351.9L180.7 348.8L181.7 346.6L180.8 344.7L175.0 343.1L172.9 345.0L170.7 341.2L154.4 335.2L151.8 335.3L150.7 341.2L140.2 341.1L138.7 340.0L131.9 341.2L124.7 335.7L116.7 336.8L111.7 331.0L107.0 330.6L100.2 327.7L97.1 326.2L96.7 324.5L94.8 327.1L93.1 327.1L91.7 325.7L93.3 322.5L93.6 318.9L91.9 317.7L85.2 316.1L83.0 313.5L82.9 312.1L87.5 310.8L91.6 305.7L95.4 287.2L98.2 265.3L100.3 261.2L103.0 260.0L100.8 257.0L98.3 261.0L99.8 240.9L102.8 225.8L110.0 232.0L111.6 234.7L113.7 243.6L117.7 247.4L115.1 243.8L112.6 231.8L111.0 228.4L108.4 225.6L99.6 218.4L99.2 216.2L101.9 216.2L104.2 217.4L102.2 209.9L101.0 194.2L94.1 192.6L83.1 186.0L74.6 171.7L74.6 169.5L76.6 164.7L74.9 161.7L71.7 159.7L73.0 157.2L74.1 155.6L76.4 155.2L84.4 157.5L77.9 153.7L67.3 155.0L63.1 153.6L62.4 150.8L65.2 147.2L63.7 145.5L61.7 144.9L55.7 145.4L54.9 144.5L56.7 141.8L55.2 140.9L50.2 141.9L47.4 141.1L44.8 138.1L41.8 138.5L40.1 137.3L36.8 137.4L35.0 135.7L24.1 132.3L19.3 131.9L15.0 133.4L12.6 132.9L9.3 126.9L2.3 124.1L3.7 122.2L10.7 120.5L12.1 118.8L7.0 116.4L5.2 113.9L6.5 113.1L10.0 113.8L14.6 113.4L12.9 111.6L10.3 110.8L1.2 111.0L0.0 107.4L1.2 103.8L6.5 100.5L19.7 97.0L25.3 97.5L29.3 96.9L34.0 94.6L36.1 92.7L42.8 91.6L49.1 93.6L57.8 103.9L64.7 99.4L75.0 99.5L77.1 102.1L79.8 97.4L82.1 100.1L94.6 99.2L91.7 97.4L89.3 93.0L88.8 76.9L82.4 65.2L80.8 61.0L81.2 57.4L88.7 58.0L94.9 56.4L97.9 57.5L98.6 65.0L101.2 69.4L106.2 69.2L111.7 70.5L118.5 70.7L128.5 73.1L132.7 71.7L136.8 68.8L144.7 66.9L145.3 65.9L140.8 66.3L136.7 64.5L136.1 62.5L138.3 56.6L150.3 50.1L158.9 48.2L167.8 44.6L172.4 40.9L175.3 36.2L177.5 34.3L176.4 32.6L177.2 14.5L178.0 11.3L179.8 8.6L186.5 4.3L201.4 1.2L203.6 0.0L205.7 5.8L205.1 7.5L205.6 9.0L210.1 14.1L212.4 15.6L219.8 12.9L221.9 14.8L223.4 17.6L224.5 23.0L225.7 23.9L233.5 25.2L234.4 26.0L236.1 32.1L237.7 30.6L243.4 30.9L246.0 31.5L249.7 34.5L248.6 38.7L250.1 40.7L248.6 44.5L249.7 46.1L255.1 46.8L260.0 46.1L263.1 44.4L264.5 40.6L267.6 38.3L268.8 39.0L266.9 46.2L268.3 48.0L269.0 53.1L272.9 53.5L280.5 57.6L286.9 64.4L294.8 63.3L295.7 64.6L301.0 67.0L305.7 64.9L307.4 65.0L310.3 66.7L313.4 67.1L315.6 69.1L316.7 72.1L321.2 78.6L322.3 78.9L325.5 76.7L328.6 77.8L329.6 80.5L331.9 79.9L334.2 80.5L341.2 78.9L343.3 81.6L345.7 82.6L356.6 84.7L360.3 86.2L360.4 89.7L352.0 99.9L348.3 114.3L345.8 119.3L344.9 123.1L345.6 125.6L345.2 129.5L343.6 134.9L343.4 138.9L344.4 141.7L345.8 142.2Z",
  };
  const project = (lat, lon) => [
    (lon * FRANCE.cos - FRANCE.minx) * FRANCE.s,
    (-lat - FRANCE.miny) * FRANCE.s,
  ];

  // Demo sites. To change the partner centre, edit data-sites in demo.md.
  // Only sites inside the map frame (metropolitan France) can be shown.
  const SITES = {
    adastra: { name: "Adastra", centre: "CINES", city: "Montpellier", lat: 43.611, lon: 3.877 },
    jeanzay: { name: "Jean Zay", centre: "IDRIS", city: "Orsay", lat: 48.698, lon: 2.187 },
  };
  const TRIP_MS = 2600;

  function demoMap(box) {
    const ids = (box.dataset.sites || "adastra,jeanzay").split(",").map((s) => s.trim());
    if (ids.length !== 2 || !ids.every((id) => SITES[id])) {
      box.textContent = "demo-map: data-sites must name two known sites.";
      return;
    }
    const tbc = (box.dataset.tbc || "").split(",").map((s) => s.trim());
    const [a, b] = ids.map((id) => ({ ...SITES[id], tbc: tbc.includes(id),
                                      xy: project(SITES[id].lat, SITES[id].lon) }));
    const svg = el("svg", { viewBox: `-10 -10 ${FRANCE.w + 20} ${FRANCE.h + 20}`,
      class: "ws-map__svg", role: "img",
      "aria-label": `Map of France: ${a.name} (${a.centre}, ${a.city}) and ${b.name} `
        + `(${b.centre}, ${b.city})${b.tbc ? ", to be confirmed," : ""} exchange model updates; `
        + "the data stays on each cluster." });
    el("path", { d: FRANCE.d, class: "ws-map__land" }, svg);

    // Curved route between the two sites (control point pushed sideways).
    const [x1, y1] = a.xy, [x2, y2] = b.xy;
    const mx = (x1 + x2) / 2, my = (y1 + y2) / 2;
    const len = Math.hypot(x2 - x1, y2 - y1);
    let nx = -(y2 - y1) / len, ny = (x2 - x1) / len;
    if (nx > 0) { nx = -nx; ny = -ny; }              // bulge westwards, labels east
    const cx = mx + nx * len * 0.28, cy = my + ny * len * 0.28;
    const route = el("path", { d: `M${x1} ${y1} Q${cx} ${cy} ${x2} ${y2}`,
      class: "ws-map__route" }, svg);
    const total = route.getTotalLength();
    const packets = [el("circle", { r: 6, class: "ws-map__packet" }, svg),
                     el("circle", { r: 6, class: "ws-map__packet" }, svg)];

    [a, b].forEach((s) => {
      const [x, y] = s.xy;
      const g = el("g", { class: `ws-map__site${s.tbc ? " is-tbc" : ""}`,
        transform: `translate(${x} ${y})` }, svg);
      el("title", {}, g).textContent = `${s.name} (${s.centre}, ${s.city})`
        + (s.tbc ? ", to be confirmed" : "")
        + ": trains on its own data, which never leaves the cluster";
      el("circle", { r: 16, class: "ws-map__pulse" }, g);
      el("circle", { r: 8, class: "ws-map__dot" }, g);
      // Labels go to the side away from the route bulge.
      const right = (cx < x);
      const tx = right ? 16 : -16, anchor = right ? "start" : "end";
      el("text", { x: tx, y: -2, "text-anchor": anchor, class: "ws-map__name" }, g)
        .textContent = s.name;
      el("text", { x: tx, y: 15, "text-anchor": anchor, class: "ws-map__centre" }, g)
        .textContent = `${s.centre} · ${s.city}`;
      if (s.tbc) {
        el("text", { x: tx, y: 31, "text-anchor": anchor, class: "ws-map__tbc" }, g)
          .textContent = "to be confirmed";
      }
    });

    box.textContent = "";
    box.appendChild(svg);
    const cap = document.createElement("figcaption");
    cap.textContent = "Model updates travel between the two centres. "
      + "The training data never leaves its cluster.";
    box.appendChild(cap);

    const draw = (ms) => {
      const t = (ms % TRIP_MS) / TRIP_MS;
      const k = ease(t);
      const fade = String(Math.min(1, Math.sin(Math.PI * t) * 3));
      [k, 1 - k].forEach((pos, i) => {
        const p = route.getPointAtLength(pos * total);
        packets[i].setAttribute("cx", p.x.toFixed(1));
        packets[i].setAttribute("cy", p.y.toFixed(1));
        packets[i].style.opacity = fade;
      });
    };
    if (reduceMotion()) {
      draw(TRIP_MS * 0.3);
      return;
    }
    draw(0);
    animate(box, draw);
  }

  // --- Wiring --------------------------------------------------------------------
  const WIDGETS = { "fl-round": flRound, "demo-map": demoMap };

  function init() {
    document.querySelectorAll("[data-ws-widget]").forEach((box) => {
      if (box.dataset.wsReady) return;
      const fn = WIDGETS[box.dataset.wsWidget];
      if (!fn) return;
      box.dataset.wsReady = "1";
      fn(box);
    });
  }

  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(init); // also covers instant navigation
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
