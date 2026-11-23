---
marp: true
theme: cines
paginate: true
size: 16:9
title: Federated Learning Workshop
footer: CINES · Federated Learning Workshop
---

<!-- _class: title -->
<!-- _paginate: false -->

<span class="kicker">CINES workshop · February 2027</span>

# Federated learning
## Train where the data lives

Concepts · Demo on Adastra · Hands-on with Flower

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
<div class="slot demo"><span class="time">15′</span><span><span class="what">Demo</span><br><span class="detail">NVIDIA FLARE on Adastra</span></span></div>
<div class="slot break"><span class="time">15′</span><span><span class="what">Break</span><br><span class="detail">Form your group</span></span></div>
<div class="slot handson"><span class="time">60′</span><span><span class="what">Hands-on</span><br><span class="detail">Flower, in groups of 4–5: one federation per group, your notebook is one client</span></span></div>
</div>

By the end, your group will have trained a model **together**, without sharing a single image, and seen when this works and when it breaks.

<!--
Speaker notes (1:00 to 1:30)
- The talk gives the vocabulary; the hands-on lets you find the numbers yourselves.
- Keep a question in mind for the debrief: which data split will hurt the most?
-->
