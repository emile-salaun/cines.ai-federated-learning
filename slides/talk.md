---
marp: true
theme: cines
paginate: true
size: 16:9
title: Federated Learning Workshop
footer: "[← Workshop site](../concepts/) CINES · Federated Learning Workshop"
---

<!-- _class: title -->
<!-- _paginate: false -->

<span class="kicker">CINES workshop · February 2027</span>

# Federated learning
## Train where the data lives

Concepts · Demo across two HPC centres · Hands-on with Flower

<!--
Speaker notes (0:00 to 0:20)
- Welcome, introduce the trainers.
- One sentence: today you will train a model on data you never see.
-->

---

<span class="kicker">Opening</span>

## The data you need is often somewhere you can't take it

<div class="cards">
<div class="card">
<svg viewBox="0 0 64 64" aria-hidden="true"><rect x="10" y="14" width="44" height="40" rx="4" fill="none" stroke="#1f3d37" stroke-width="4"/><path d="M32 22v16M24 30h16" stroke="#3d8b78" stroke-width="5" stroke-linecap="round"/></svg>
<b>Hospitals</b>
<span>Patient data is protected by law (GDPR, health data).</span>
</div>
<div class="card">
<svg viewBox="0 0 64 64" aria-hidden="true"><path d="M8 54V30l14 8V30l14 8V22l20 10v22z" fill="none" stroke="#1f3d37" stroke-width="4" stroke-linejoin="round"/><rect x="40" y="42" width="8" height="12" fill="#3d8b78"/></svg>
<b>Companies</b>
<span>Process and customer data are trade secrets.</span>
</div>
<div class="card">
<svg viewBox="0 0 64 64" aria-hidden="true"><rect x="12" y="8" width="40" height="12" rx="3" fill="none" stroke="#1f3d37" stroke-width="4"/><rect x="12" y="26" width="40" height="12" rx="3" fill="none" stroke="#1f3d37" stroke-width="4"/><rect x="12" y="44" width="40" height="12" rx="3" fill="none" stroke="#1f3d37" stroke-width="4"/><circle cx="20" cy="14" r="2.5" fill="#3d8b78"/><circle cx="20" cy="32" r="2.5" fill="#3d8b78"/><circle cx="20" cy="50" r="2.5" fill="#3d8b78"/></svg>
<b>Research centres</b>
<span>Datasets are too large to move, or must stay on national systems.</span>
</div>
</div>

<div class="takeaway">

**Federated learning:** the model travels to the data. The data never moves.

</div>

<!--
Speaker notes (0:20 to 1:00)
- Ask the room: who has data they cannot share, even with a colleague in another lab?
- Three reasons data stays put: law, competition, size and sovereignty.
- Do not explain how FL works yet: that is the next section.
-->

---

<span class="kicker">Opening</span>

## Your next two hours

<div class="timeline">
<div class="slot talk now"><span class="time">30′</span><span><span class="what">Talk</span><br><span class="detail">Concepts, frameworks, FL on HPC</span></span></div>
<div class="slot demo"><span class="time">15′</span><span><span class="what">Demo</span><br><span class="detail">NVIDIA FLARE across two HPC centres</span></span></div>
<div class="slot break"><span class="time">15′</span><span><span class="what">Break</span><br><span class="detail">Form your group</span></span></div>
<div class="slot handson"><span class="time">60′</span><span><span class="what">Hands-on</span><br><span class="detail">Flower: simulate in your notebook, then the whole room federates</span></span></div>
</div>

By the end, the whole room will have trained one model **together**, without sharing a single image, and you will have seen when this works and when it breaks.

<!--
Speaker notes (1:00 to 1:30)
- The talk gives the vocabulary; the hands-on lets you find the numbers yourselves.
- Keep a question in mind for the debrief: which data split will hurt the most?
-->

---

<!-- _class: draft -->

<span class="kicker">What is FL and why <em>4 min</em></span>

## Move the model, not the data

<div class="stage">
<div class="grid-2">
<div class="diagram"><svg viewBox="0 0 420 270" font-family="Inter, system-ui, sans-serif"><rect x="130" y="14" width="160" height="70" rx="14" fill="#1f3d37"/><g transform="translate(146 30) scale(1.5)" fill="none" stroke="#8fd3be" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/></g><text x="236" y="56" text-anchor="middle" font-size="16" font-weight="700" fill="#fff">All data</text><path d="M72 180 L210 92" stroke="#c9803a" stroke-width="3" fill="none" marker-end="url(#ah1)"/><path d="M210 180 L210 92" stroke="#c9803a" stroke-width="3" fill="none" marker-end="url(#ah1)"/><path d="M348 180 L210 92" stroke="#c9803a" stroke-width="3" fill="none" marker-end="url(#ah1)"/><rect x="20" y="182" width="104" height="70" rx="12" fill="#fff" stroke="#3d8b78" stroke-width="2.5"/><g transform="translate(34 200) scale(1.4)" fill="none" stroke="#1f3d37" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/></g><text x="96" y="224" text-anchor="middle" font-size="15" font-weight="600" fill="#1f3d37">Site A</text><rect x="158" y="182" width="104" height="70" rx="12" fill="#fff" stroke="#3d8b78" stroke-width="2.5"/><g transform="translate(172 200) scale(1.4)" fill="none" stroke="#1f3d37" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/></g><text x="234" y="224" text-anchor="middle" font-size="15" font-weight="600" fill="#1f3d37">Site B</text><rect x="296" y="182" width="104" height="70" rx="12" fill="#fff" stroke="#3d8b78" stroke-width="2.5"/><g transform="translate(310 200) scale(1.4)" fill="none" stroke="#1f3d37" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/></g><text x="372" y="224" text-anchor="middle" font-size="15" font-weight="600" fill="#1f3d37">Site C</text><defs><marker id="ah1" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#c9803a"/></marker></defs><text x="300" y="130" font-size="15" font-weight="700" fill="#c9803a">data copied</text></svg><div class="cap"><b>Centralised</b>: copy every dataset to one place</div></div>
<div class="diagram"><svg viewBox="0 0 420 270" font-family="Inter, system-ui, sans-serif"><rect x="130" y="14" width="160" height="70" rx="14" fill="#1f3d37"/><rect x="150" y="38" width="40" height="18" rx="5" fill="#8fd3be"/><text x="246" y="56" text-anchor="middle" font-size="16" font-weight="700" fill="#fff">Model</text><path d="M200 90 L64 176" stroke="#3d8b78" stroke-width="3" fill="none" marker-end="url(#ah2)"/><path d="M82 176 L222 92" stroke="#3d8b78" stroke-width="2.5" stroke-dasharray="6 5" fill="none"/><path d="M200 90 L202 176" stroke="#3d8b78" stroke-width="3" fill="none" marker-end="url(#ah2)"/><path d="M220 176 L222 92" stroke="#3d8b78" stroke-width="2.5" stroke-dasharray="6 5" fill="none"/><path d="M200 90 L340 176" stroke="#3d8b78" stroke-width="3" fill="none" marker-end="url(#ah2)"/><path d="M358 176 L222 92" stroke="#3d8b78" stroke-width="2.5" stroke-dasharray="6 5" fill="none"/><rect x="20" y="182" width="104" height="70" rx="12" fill="#fff" stroke="#3d8b78" stroke-width="2.5"/><g transform="translate(34 200) scale(1.4)" fill="none" stroke="#1f3d37" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/></g><text x="96" y="224" text-anchor="middle" font-size="15" font-weight="600" fill="#1f3d37">Site A</text><g transform="translate(102 170) scale(0.9)" fill="#fff" stroke="#3d8b78" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="13" fill="#e6f0ed" stroke="none"/><rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></g><rect x="86" y="232" width="28" height="12" rx="4" fill="#8fd3be"/><rect x="158" y="182" width="104" height="70" rx="12" fill="#fff" stroke="#3d8b78" stroke-width="2.5"/><g transform="translate(172 200) scale(1.4)" fill="none" stroke="#1f3d37" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/></g><text x="234" y="224" text-anchor="middle" font-size="15" font-weight="600" fill="#1f3d37">Site B</text><g transform="translate(240 170) scale(0.9)" fill="#fff" stroke="#3d8b78" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="13" fill="#e6f0ed" stroke="none"/><rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></g><rect x="224" y="232" width="28" height="12" rx="4" fill="#8fd3be"/><rect x="296" y="182" width="104" height="70" rx="12" fill="#fff" stroke="#3d8b78" stroke-width="2.5"/><g transform="translate(310 200) scale(1.4)" fill="none" stroke="#1f3d37" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3"/></g><text x="372" y="224" text-anchor="middle" font-size="15" font-weight="600" fill="#1f3d37">Site C</text><g transform="translate(378 170) scale(0.9)" fill="#fff" stroke="#3d8b78" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="13" fill="#e6f0ed" stroke="none"/><rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></g><rect x="362" y="232" width="28" height="12" rx="4" fill="#8fd3be"/><defs><marker id="ah2" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#3d8b78"/></marker></defs><text x="300" y="130" font-size="15" font-weight="700" fill="#3d8b78">model out,</text><text x="300" y="150" font-size="15" font-weight="700" fill="#3d8b78">weights back</text></svg><div class="cap"><b>Federated</b>: each site keeps its data, only weights travel</div></div>
</div>
<div class="band">The data never leaves a site. <strong>What travels is the model.</strong></div>
</div>

---

<!-- _class: draft -->

<span class="kicker">What is FL and why <em>4 min</em></span>

## Two flavours of federated learning

<div class="stage">
<div class="grid-2">
<div class="tile hl"><div class="icon"><svg viewBox="0 0 24 24" fill="none" stroke="#1f3d37" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 21h18M5 21V7l7-4 7 4v14M9 21v-6h6v6"/></svg></div><span class="tag">Today's workshop</span><h3>Cross-silo</h3>
<ul><li>A few institutions: hospitals, labs, HPC centres</li><li>Large datasets per client</li><li>Reliable, scheduled participants</li></ul></div>
<div class="tile"><div class="icon"><svg viewBox="0 0 24 24" fill="none" stroke="#1f3d37" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="7" y="2" width="10" height="20" rx="2"/><path d="M11 18h2"/></svg></div><span class="tag">At scale</span><h3>Cross-device</h3>
<ul><li>Millions of phones or sensors</li><li>Small datasets per client</li><li>Clients come and go</li></ul></div>
</div>
</div>

---

<!-- _class: draft -->

<span class="kicker">What is FL and why <em>4 min</em></span>

## Federated is not private by default

<div class="stage">
<div class="grid-3">
<div class="tile "><div class="icon"><svg viewBox="0 0 24 24" fill="none" stroke="#1f3d37" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/></svg></div><span class="tag">The risk</span><h3>Updates can leak</h3><p>Model weights still carry traces of the training data.</p></div>
<div class="tile "><div class="icon"><svg viewBox="0 0 24 24" fill="none" stroke="#1f3d37" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 2l8 4v6c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6z"/><path d="M9 12l2 2 4-4"/></svg></div><span class="tag">Defence</span><h3>Secure aggregation</h3><p>The server only sees the sum of the updates, never one client's.</p></div>
<div class="tile "><div class="icon"><svg viewBox="0 0 24 24" fill="none" stroke="#1f3d37" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 12c2-6 4 6 6 0s4 6 6 0 4 6 6 0"/></svg></div><span class="tag">Defence</span><h3>Differential privacy</h3><p>Calibrated noise on what leaves a site bounds what can be learned.</p></div>
</div>
<div class="band">FL is <strong>one layer</strong> of a privacy design, not the whole design.</div>
</div>

---

<span class="kicker">Non-IID data <em>5.5 min</em></span>

## How different are the clients' data?

<div class="play">
<div class="widget alpha-widget" data-alpha="0.1" data-seed="42"></div>
<div class="explain">

Each cell: how many images of one class a client holds.

**α** is the knob. Large α: everyone has the same mix. Small α: each client has a few classes, and sizes become unequal.

The exercises use **α = 0.1**.

<div class="hint">Slide α from 0.1 up to 100, then down to 0.03.</div>

<span class="tiny">Same scheme as Flower Datasets' Dirichlet partitioner. Illustration, not the exact hands-on split.</span>

</div>
</div>

---

<span class="kicker">Non-IID data <em>5.5 min</em></span>

## Your prediction

<p class="lead">Rank the three splits by final accuracy, from best to worst. Show of hands now, we check at the debrief.</p>

<div class="stage">
<div class="grid-3">
<div class="tile"><span class="tag">A</span><h3>IID</h3><div class="pict"><i style="background:#3d8b78"></i><i style="background:#3d8b78"></i><i style="background:#3d8b78"></i><i style="background:#3d8b78"></i><i style="background:#3d8b78"></i></div><p>Every client has the same mix of classes.</p></div>
<div class="tile"><span class="tag">B</span><h3>Dirichlet α = 0.1</h3><div class="pict"><i style="background:#1f3d37"></i><i style="background:#8fd3be"></i><i style="background:#2f5a51"></i><i style="background:#c9d6d2"></i><i style="background:#3d8b78"></i></div><p>Very uneven mixes and sizes.</p></div>
<div class="tile"><span class="tag">C</span><h3>Pathological</h3><div class="pict"><i style="background:#1f3d37"></i><i style="background:#eef2f1"></i><i style="background:#eef2f1"></i><i style="background:#1f3d37"></i><i style="background:#eef2f1"></i></div><p>Only 2 classes per client.</p></div>
</div>
</div>

---

<!-- _class: draft -->

<span class="kicker">FL on HPC <em>5 min</em></span>

## Who is doing it (2026)

<div class="stage">
<div class="grid-2 compact">
<div class="tile "><span class="tag">US DOE</span><h3>Argonne</h3><p>APPFL across Polaris, Aurora, Frontier and Perlmutter, 64 nodes each. Asynchronous aggregation against queue waits.</p></div>
<div class="tile "><span class="tag">US DOE</span><h3>ORNL</h3><p>96 FL clients on Frontier. Orchestration, not the model, limits scaling.</p></div>
<div class="tile "><span class="tag">Europe</span><h3>EuroHPC xFFL and IT4LIA</h3><p>MareNostrum 5 and Cineca: federated LLM training across supercomputers, as a service.</p></div>
<div class="tile dark"><span class="tag">This workshop</span><h3>Today's demo</h3><p>NVIDIA FLARE across Adastra and a second European centre.</p></div>
</div>
<span class="tiny">Sources: arXiv 2603.19544 · EuroMLSys 2026 · arXiv 2605.02125 · eurohpc-ju.europa.eu · it4lia-aifactory.eu</span>
</div>

---

<!-- _class: draft -->

<span class="kicker">FL on HPC <em>5 min</em></span>

## Why two frameworks?

<div class="stage">
<div class="grid-2">
<div class="tile "><span class="tag">Hands-on</span><h3>Flower: build and learn</h3><p>The same app runs in a notebook or across machines. Each experiment is one <code style="white-space: nowrap">--run-config</code> change.</p></div>
<div class="tile dark"><span class="tag">Demo</span><h3>NVIDIA FLARE: operate across sites</h3><p>Per-site certificates, Slurm launcher, clients that only connect out. Already federates Isambard&#8209;AI, Jean Zay and Adastra.</p></div>
</div>
<div class="takeaway">The two mature FL frameworks in 2026, and compatible: FLARE can run Flower apps.</div>
<span class="tiny">Sources: arXiv 2611.10688 · bristol.ac.uk (BriCS–GENCI, 2026) · nvflare.readthedocs.io</span>
</div>

<!--
Speaker notes
- Fit, not capability: Flower can also run on HPC (SuperNodes as Slurm jobs, TLS, node authentication).
- ConcordAI (BriCS and GENCI, with IDRIS and CINES) uses NVIDIA FLARE between Isambard-AI, Jean Zay and Adastra.
-->

---

<!-- _class: draft -->

<span class="kicker">Demo <em>15 min</em></span>

## Federated learning across two HPC centres

<div class="play">
<div class="diagram"><svg viewBox="0 0 640 280" font-family="Inter, system-ui, sans-serif"><rect x="10" y="20" width="290" height="240" rx="18" fill="#f6f9f8" stroke="#e1e7e5" stroke-width="2"/><text x="30" y="52" font-size="18" font-weight="700" fill="#1f3d37">Adastra</text><text x="30" y="74" font-size="13" fill="#5d6b67">CINES</text><rect x="340" y="20" width="290" height="240" rx="18" fill="#f6f9f8" stroke="#e1e7e5" stroke-width="2"/><text x="360" y="52" font-size="18" font-weight="700" fill="#1f3d37">Partner centre</text><text x="360" y="74" font-size="13" fill="#5d6b67">LUMI or Jean Zay (TBD)</text><rect x="40" y="100" width="150" height="56" rx="12" fill="#1f3d37"/><text x="115" y="133" text-anchor="middle" font-size="15" font-weight="700" fill="#fff">FLARE server</text><rect x="40" y="180" width="150" height="50" rx="12" fill="#fff" stroke="#3d8b78" stroke-width="2.5"/><text x="115" y="210" text-anchor="middle" font-size="14" font-weight="600" fill="#1f3d37">site-1 job</text><path d="M115 180 L115 160" stroke="#3d8b78" stroke-width="2.5" marker-end="url(#ah4)"/><rect x="420" y="110" width="150" height="50" rx="12" fill="#fff" stroke="#3d8b78" stroke-width="2.5"/><text x="495" y="140" text-anchor="middle" font-size="14" font-weight="600" fill="#1f3d37">site-2 job</text><path d="M420 135 L196 128" stroke="#3d8b78" stroke-width="2.5" stroke-dasharray="6 5" marker-end="url(#ah4)"/><rect x="420" y="180" width="150" height="50" rx="12" fill="#fff" stroke="#3d8b78" stroke-width="2.5"/><text x="495" y="210" text-anchor="middle" font-size="14" font-weight="600" fill="#1f3d37">site-3 job</text><path d="M420 205 L196 128" stroke="#3d8b78" stroke-width="2.5" stroke-dasharray="6 5" marker-end="url(#ah4)"/><defs><marker id="ah4" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#3d8b78"/></marker></defs></svg><div class="cap">Clients open <b>outbound</b> connections to the FLARE server. The data stay in each centre.</div></div>
<div class="explain">

**Watch for**

- the clients of both centres joining
- the metric improving round after round

<div class="video"><div class="play-btn"><svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M8 5l11 7-11 7z"/></svg></div>Backup video (TBD)</div>

<div class="todo">TODO: partner centre (LUMI or Jean Zay), job, metric, backup video.</div>

</div>
</div>

---

<!-- _class: break -->
<!-- _paginate: false -->

<span class="kicker">Break · 15 min</span>

<div class="countdown" data-minutes="15" title="Click: pause / resume · Double-click: reset">15:00</div>

<div class="break-steps">
<div><b>1</b> Find your group <span>4–5 people, see the site</span></div>
<div><b>2</b> Group lead <span>opens <code>lead.ipynb</code></span></div>
<div><b>3</b> Members <span>open <code>member.ipynb</code></span></div>
</div>


<!--
Speaker notes (after the demo)
- Show this slide as soon as the demo ends: the countdown starts on its own.
- Click the timer to pause it, double-click to reset.
-->

---

<!-- _class: clock -->

<div class="progress"><i class="on"></i><i class=""></i><i class=""></i></div>

<span class="kicker">Hands-on · phase 1 of 3 · 35 min</span>

## Simulate

<div class="stage">
<div class="countdown" data-minutes="35" title="Click: pause / resume · Double-click: reset">35:00</div>
<ul><li>Steps 0 to 3 in <strong>your own</strong> notebook</li><li><strong>Predict</strong> with your group before every run</li><li><strong>Done when</strong> your group table of step 3 is filled in</li></ul>
</div>

<!--
Speaker notes
- Setup 5 min, then about 10 min per step. At 0:00 everyone moves to phase 2, finished or not.
-->

---

<!-- _class: clock -->

<div class="progress"><i class="done"></i><i class="on"></i><i class=""></i></div>

<span class="kicker">Hands-on · phase 2 of 3 · 15 min</span>

## Federate the room

<div class="stage">
<div class="countdown" data-minutes="15" title="Click: pause / resume · Double-click: reset">15:00</div>
<ul><li>Start <strong>your</strong> SuperNode: one real client per seat</li><li>Pick your local epochs: the round has a deadline</li><li><strong>Done when</strong> your seat is on the leaderboard</li></ul>
</div>

<!--
Speaker notes
- Join notebook, deadline and leaderboard: to finalise after the phase 2 prototype.
- Halfway: ask half the room to stop their SuperNode, then to rejoin.
-->

---

<!-- _class: clock -->

<div class="progress"><i class="done"></i><i class="done"></i><i class="on"></i></div>

<span class="kicker">Hands-on · phase 3 of 3 · 10 min</span>

## Debrief

<div class="stage">
<div class="countdown" data-minutes="10" title="Click: pause / resume · Double-click: reset">10:00</div>
<ul><li>Room result and leaderboard</li><li>Your local-epochs choice versus step 3</li><li>Back to the demo: what changes between two HPC centres?</li></ul>
</div>

---

<!-- _class: clock -->



<span class="kicker">Hands-on · if the hub fails</span>

## Simulate anywhere

<div class="stage">

<ul><li>Phase 1 runs on <strong>Colab or your laptop</strong>: same notebook, same app</li><li>Phase 2 becomes a trainer-run federation on the projector</li><li>Your results stay comparable with the rest of the room</li></ul>
</div>

<!--
Speaker notes
- A group whose setup fails falls back to the simulation notebook; the trainers decide case by case.
-->

<script src="widgets.js"></script>
