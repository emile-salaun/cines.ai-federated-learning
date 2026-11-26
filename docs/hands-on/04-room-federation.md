---
hide:
  - navigation
  - toc
---

# 4. Room federation

<div class="ws-meta" markdown="span">
  <span class="ws-badge">:material-flag-outline: Step 4 / 5</span>
  <span class="ws-badge">:material-clock-outline: 15 min</span>
  <span class="ws-badge">:material-account-multiple-outline: Everyone</span>
</div>

--8<-- "hands-on-stepper.md"

!!! abstract "Goal"

    The whole room trains one model together. Each participant runs one real
    SuperNode, picks their local epochs, and the server measures what each one brings.

<!-- TODO: written after the phase 2 prototype (join notebook, round deadline,
     contribution score, leaderboard). Seat numbering across the room: TBD. -->

!!! warning "Phase 2 is being built"

    This page is completed after the prototype. Outline below.

## 4.1 Join the federation

TBD (`notebooks/join.ipynb`: starts your SuperNode on {% if scenario == "A" %}seat `__SEAT__`{% else %}your seat{% endif %}).

!!! checkpoint "You should see"

    TBD

## 4.2 Pick your local epochs

TBD (1, 2, 5 or 10; a round has a deadline: an update that arrives late does not count).

## 4.3 Stop and rejoin

TBD (the trainers ask half the room to stop their SuperNode, then to rejoin).

!!! checkpoint "You should see"

    TBD

## Done?

<div class="ws-checklist" markdown>

- [ ] My SuperNode took part in the room run
- [ ] I found my seat on the leaderboard

</div>

[:octicons-arrow-right-24: Step 5: Debrief](05-debrief.md){ .md-button .md-button--primary }
