/* =============================================================================
   hands-on.js - Participant-side helpers for the hands-on pages.

   1. Group picker   <div id="ws-group-picker"></div>  (hands-on/index.md)
                     Group + seat saved in the browser (localStorage).
   2. Variables      __GROUP__, __SUPERLINK__, __SEAT__ anywhere in a page
                     (prose or code blocks) are replaced by the participant's
                     values. Groups come from groups.js.
   3. Checklists     Markdown task lists become clickable and are remembered.
                     A page is "done" when every box in its .ws-checklist is
                     ticked; the stepper then shows a check mark.
   4. Stepper        .ws-stepper (includes/hands-on-stepper.md): highlights the
                     current step, marks done steps, shows the group chip.
   ============================================================================= */
(() => {
  "use strict";

  // --- Storage (can be unavailable: private mode, blocked site data) --------
  const PREFIX = "ws:";
  const store = {
    get(key) {
      try { return localStorage.getItem(PREFIX + key); } catch { return null; }
    },
    set(key, value) {
      try {
        if (value === null || value === "") localStorage.removeItem(PREFIX + key);
        else localStorage.setItem(PREFIX + key, value);
      } catch { /* ignore */ }
    },
    clear() {
      try {
        Object.keys(localStorage)
          .filter((k) => k.startsWith(PREFIX))
          .forEach((k) => localStorage.removeItem(k));
      } catch { /* ignore */ }
    },
  };

  const GROUPS = Array.isArray(window.WS_GROUPS) ? window.WS_GROUPS : [];
  const normPath = (p) => p.replace(/index\.html$/, "").replace(/\/?$/, "/");
  const here = () => normPath(location.pathname);
  const group = () => GROUPS.find((g) => String(g.id) === store.get("group"));
  const seat = () => store.get("seat");

  // --- 2. Variables ----------------------------------------------------------
  const VARS = {
    GROUP: () => (group() ? String(group().id) : null),
    SUPERLINK: () => (group() ? group().superlink : null),
    SEAT: () => seat(),
  };
  const SPLIT = /(__(?:GROUP|SUPERLINK|SEAT)__)/;

  function wrapVars(root) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: (n) =>
        SPLIT.test(n.data) && !n.parentElement.closest(".ws-var, script, style, textarea")
          ? NodeFilter.FILTER_ACCEPT
          : NodeFilter.FILTER_REJECT,
    });
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach((node) => {
      const frag = document.createDocumentFragment();
      node.data.split(SPLIT).forEach((part) => {
        const m = part.match(/^__(\w+)__$/);
        if (m && VARS[m[1]]) {
          const span = document.createElement("span");
          span.className = "ws-var";
          span.dataset.var = m[1];
          frag.appendChild(span);
        } else if (part) {
          frag.appendChild(document.createTextNode(part));
        }
      });
      node.replaceWith(frag);
    });
  }

  function renderVars() {
    document.querySelectorAll(".ws-var").forEach((el) => {
      const value = VARS[el.dataset.var]();
      el.textContent = value || `<${el.dataset.var.toLowerCase()}>`;
      el.classList.toggle("ws-var--unset", !value);
      el.title = value ? "" : "Pick your group on the Hands-on overview page";
    });
  }

  // --- 1. Group picker -------------------------------------------------------
  function renderPicker() {
    const box = document.getElementById("ws-group-picker");
    if (!box) return;
    if (!GROUPS.length) {
      box.innerHTML = '<p class="ws-muted">No groups configured yet (groups.js).</p>';
      return;
    }
    const g = group();
    const groupOpts = GROUPS.map(
      (x) => `<option value="${x.id}" ${g && g.id === x.id ? "selected" : ""}>Group ${x.id}</option>`
    ).join("");
    const seats = g ? Array.from({ length: g.size || 5 }, (_, i) => String(i + 1)) : [];
    const seatOpts = seats
      .map((s) => `<option value="${s}" ${seat() === s ? "selected" : ""}>Seat ${s}</option>`)
      .join("");

    box.innerHTML = `
      <div class="ws-picker__fields">
        <label>Your group
          <select data-ws-select="group">
            <option value="">Choose…</option>${groupOpts}
          </select>
        </label>
        <label>Your seat
          <select data-ws-select="seat" ${g ? "" : "disabled"}>
            <option value="">Choose…</option>${seatOpts}
          </select>
        </label>
      </div>
      <dl class="ws-picker__summary">
        <div><dt>SuperLink</dt><dd><code>__SUPERLINK__</code></dd></div>
        <div><dt>Group</dt><dd><code>__GROUP__</code></dd></div>
        <div><dt>Seat</dt><dd><code>__SEAT__</code></dd></div>
      </dl>
      <button type="button" class="md-button ws-picker__reset" data-ws-reset>
        Reset my progress
      </button>`;

    box.querySelectorAll("[data-ws-select]").forEach((sel) =>
      sel.addEventListener("change", () => {
        store.set(sel.dataset.wsSelect, sel.value);
        if (sel.dataset.wsSelect === "group") store.set("seat", null);
        refresh();
      })
    );
    box.querySelector("[data-ws-reset]").addEventListener("click", () => {
      if (confirm("Clear your group, seat and ticked checklists on this browser?")) {
        store.clear();
        location.reload();
      }
    });
    wrapVars(box);
  }

  // --- 3. Checklists ---------------------------------------------------------
  function initChecklists() {
    const boxes = document.querySelectorAll(".md-typeset .task-list-item input[type=checkbox]");
    boxes.forEach((cb, i) => {
      const key = `task:${here()}:${i}`;
      cb.disabled = false;
      cb.checked = store.get(key) === "1";
      cb.addEventListener("change", () => {
        store.set(key, cb.checked ? "1" : null);
        updateDone();
        renderStepper();
      });
    });
    updateDone();
  }

  function updateDone() {
    const required = document.querySelectorAll(".ws-checklist input[type=checkbox]");
    if (!required.length) return;
    const done = Array.from(required).every((cb) => cb.checked);
    store.set(`done:${here()}`, done ? "1" : null);
  }

  // --- 4. Stepper ------------------------------------------------------------
  function renderStepper() {
    document.querySelectorAll(".ws-stepper").forEach((nav) => {
      const links = nav.querySelectorAll("li > a");
      links.forEach((a) => {
        const path = normPath(new URL(a.href, location.href).pathname);
        const li = a.parentElement;
        const current = path === here();
        li.classList.toggle("is-current", current);
        li.classList.toggle("is-done", store.get(`done:${path}`) === "1");
        if (current) a.setAttribute("aria-current", "step");
        else a.removeAttribute("aria-current");
      });

      let chip = nav.querySelector(".ws-group-chip");
      if (!chip && links.length) {
        chip = document.createElement("a");
        chip.className = "ws-group-chip";
        chip.href = new URL(links[0].getAttribute("href"), location.href).pathname + "#your-group";
        nav.appendChild(chip);
      }
      if (chip) {
        const g = group();
        chip.textContent = g ? `Group ${g.id}${seat() ? ` · Seat ${seat()}` : ""}` : "Pick your group";
        chip.classList.toggle("is-unset", !g);
      }
    });
  }

  // --- Wiring ----------------------------------------------------------------
  function refresh() {
    renderPicker();
    renderVars();
    renderStepper();
  }

  function init() {
    const content = document.querySelector(".md-content") || document.body;
    wrapVars(content);
    initChecklists();
    refresh();
  }

  if (window.document$ && typeof window.document$.subscribe === "function") {
    window.document$.subscribe(init); // Material (also covers instant navigation)
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
