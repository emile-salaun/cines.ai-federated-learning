/* =============================================================================
   groups.js - TRAINERS: one entry per hands-on group, filled in on the day.

   - id         group number shown to participants
   - superlink  address of the group's SuperLink (host:port), injected
                wherever a page contains __SUPERLINK__
   - size       number of seats in the group (seat picker 1..size, __SEAT__)
   ============================================================================= */
window.WS_GROUPS = [
  { id: 1, superlink: "TBD:9092", size: 5 }, // EDIT
  { id: 2, superlink: "TBD:9192", size: 5 }, // EDIT
  { id: 3, superlink: "TBD:9292", size: 5 }, // EDIT
];
