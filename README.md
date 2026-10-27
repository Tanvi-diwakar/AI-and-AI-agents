# F29AI Coursework 1: Sudoku and Automated Planning

Prepared for:
- Nashitah Abdia Shahid - H00555549
- Tanvi Sandeep Diwakar - H00561261

## Deliverables

- `Coursework_Report.pdf`: combined report, with a title page, four pages for
  Parts 1A/1B, three pages for Parts 2A/2B/2C, and references.
- `Coursework_Report.md`: editable report text.
- `Sudoku/solver.py`: original implementation using MRV backtracking and
  singleton constraint propagation; accepts `.txt` and `.csv` files.
- `Sudoku/README.md`: run instructions, metrics, tests and puzzle provenance.
- `Sudoku/tests/`, `Sudoku/puzzles/`, `Sudoku/evaluation/`: reproducible tests,
  sample inputs, actual measurements and example outputs.
- `PDDL/PartA&B/` and `PDDL/PartC/`: exactly five PDDL files with the starter
  filenames, folders and domain/problem names preserved.
- `validation/`: the previously generated PDDL plans, logs and 43-check validator.
- `report/`: editable content, title metadata and a PDF-generation script.
- `DEMO_GUIDE.md`: an optional outline for the required video; not a recording.

## Quick start

From this package directory:

```sh
python3 Sudoku/solver.py Sudoku/puzzles/norvig_01.txt --stats
python3 -m unittest discover -s Sudoku/tests -v
python3 Sudoku/benchmark.py --out Sudoku/evaluation_new
python3 validation/check_model.py
```

Sudoku requires Python 3.10+ and no third-party libraries. It passed 33 unit-test
methods, including generated and published-puzzle subtests. The recorded Sudoku
benchmark has nine cases, one warm-up and seven measured runs each.

## PDDL planner

Tested using Pyperplan 2.1 and Python 3.12. Install in a separate environment:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install pyperplan==2.1
.venv/bin/pyperplan -H hff -s gbf "PDDL/PartA&B/domain.pddl" "PDDL/PartA&B/mission1.pddl"
.venv/bin/pyperplan -H hff -s gbf "PDDL/PartA&B/domain.pddl" "PDDL/PartA&B/mission2.pddl"
.venv/bin/pyperplan -H hff -s gbf "PDDL/PartC/domain-ext.pddl" "PDDL/PartC/mission3.pddl"
```

On Windows, use `.venv\Scripts\python.exe` and `.venv\Scripts\pyperplan.exe`.
Pyperplan 2.1 calls greedy best-first search `gbf`; use its installed help. Plans
are saved beside the problem as `.pddl.soln`. The recorded plans contain 10, 20
and 24 actions. Different valid orders are possible, and shortest-plan optimality
is not claimed. The 43-check independent replay suite passed. VAL was not run.

The domains use only `:strips :typing`. In Mission 1 L1 lands at chosen WP1. In
Missions 2/3 L1 is at specified WP2 and L2 lands at chosen WP1. Maps follow the
arrows exactly. The report explains data memory, sample delivery, ownership and
astronaut constraints.

## Finish the title page before submission

The names and IDs above are included. Two fields remain clearly marked because
they have not been supplied: **Canvas group/campus** and **video-demo URL**.
Update `report/metadata.json`, then rebuild:

```sh
python3 -m venv .report-venv
.report-venv/bin/python -m pip install reportlab
.report-venv/bin/python report/build_report.py
```

The report source is `report/content.json`; the generator also writes the editable
Markdown copy. PDF generation dependencies are separate from the Sudoku solver.
If you edit report text, recheck the four-page Part 1 and three-page Part 2 limits.

Review the report and code, record the required demonstration with both members
presenting substantial parts, and put the link on the title page. Do not include
the video file in the ZIP. The truthful GenAI statement already describes Codex's
role in implementation, tests and report drafting; update it for any other use.
The supplied excerpts do not contain the full referenced GenAI rules or marking
rubric, so check the full Canvas guidance before submitting.

Rename the final ZIP `F29AI CW1 <Campus> <GroupNumber>.zip` using your actual group.
Supplementary test evidence and report-generation sources may be omitted from
that submission if preferred. Keep the single final report, Sudoku code/README
and the five PDDL files. This package does not claim a recorded video or university
submission has been completed.
