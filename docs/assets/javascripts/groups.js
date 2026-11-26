/* =============================================================================
   groups.js - TRAINERS: one entry per hands-on group, filled in on the day.

   - id    group number shown to participants (the group predicts and discusses
           together, and splits the step 3 runs by seat)
   - size  number of seats in the group (seat picker 1..size, __SEAT__; the
           participant's client in the dashboard is seat - 1, __CLIENT__)

   Used in scenario "A" only (zensical.toml, [project.extra] scenario): the
   picker on the hands-on overview. In scenario "B" this list is not shown.

   Phase 2 uses one room SuperLink, run by the trainers: its address goes on the
   room federation page, not here.
   ============================================================================= */
window.WS_GROUPS = [
  { id: 1, size: 5 }, // EDIT
  { id: 2, size: 5 }, // EDIT
  { id: 3, size: 5 }, // EDIT
];
