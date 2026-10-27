# Suggested video outline (maximum eight minutes)

This is an outline to rehearse, not evidence that a video has been recorded.
Both members should explain a substantial part in their own words.

1. **0:00-0:35 - Introductions and approach.** State the group and names. Explain
   the 81 variables, candidate domains, and row/column/box constraints.
2. **0:35-2:15 - Sudoku code.** Show `validate_grid`, `_propagate` and `_search`.
   Explain MRV, ascending candidate order, and copied branch state. Show how an
   empty domain triggers failure and how alternatives are tried.
3. **2:15-3:15 - Sudoku demonstration.** Run a `.txt` puzzle and show the readable
   solution. Run the CSV example, then `unsatisfiable_search.txt`. Explain guesses
   and backtracks using the benchmark table. Mention the theoretical A* result:
   with unit-cost cell assignments and h=blanks, every state has f=initial blanks.
4. **3:15-4:30 - Base PDDL.** Show the types, directed map edges, ownership,
   shared memory token and separate sample capacities. Explain why saved/stored
   goals require delivery. Run Mission 1 and Mission 2 with their shared domain.
5. **4:30-6:40 - Astronaut extension.** Run Mission 3 with `domain-ext.pddl`.
   Show Bob's room change before deployment, control-room presence for data,
   and Alice's return to the docking bay for sample storage. Point to the actual
   preconditions that block these actions when astronauts are in the wrong room.
6. **6:40-7:40 - Evidence and limits.** Briefly show the 33 Sudoku tests and 43
   PDDL checks. Explain that the Sudoku solver finds one solution, not uniqueness;
   benchmark results are a small sample; and PDDL plans were independently
   replayed but not checked by VAL. Leave time for a clear ending.

Agree a balanced speaking split before recording. Verify the uploaded video's
sharing permissions, then insert its URL into the report metadata and rebuild.
