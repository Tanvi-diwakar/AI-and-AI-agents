# F29AI Coursework 1 — Sudoku and Automated Planning

## Project Overview

This repository contains the implementation, evaluation, and validation artefacts for F29AI Coursework 1. The coursework covers Sudoku as a Constraint Satisfaction Problem (CSP) and PDDL-based automated planning for lunar rover missions.

## Team

- **Nashitah Abdia Shahid**
- **Tanvi Sandeep Diwakar**

## Repository Structure

```text
AI coursework/
├── README.md
├── Coursework_Report.pdf
├── Coursework_Report.md
├── DEMO_GUIDE.md
├── Sudoku/
│   ├── solver.py
│   ├── benchmark.py
│   ├── puzzles/
│   ├── tests/
│   └── evaluation/
├── PDDL/
│   ├── PartA&B/
│   │   ├── domain.pddl
│   │   ├── mission1.pddl
│   │   ├── mission1.pddl.soln
│   │   ├── mission2.pddl
│   │   └── mission2.pddl.soln
│   └── PartC/
│       ├── domain-ext.pddl
│       ├── mission3.pddl
│       └── mission3.pddl.soln
├── validation/
│   ├── check_model.py
│   ├── check-results.txt
│   ├── mission1.plan
│   ├── mission2.plan
│   └── mission3.plan
└── .vscode/
    └── run-pddl-validation.ps1
```

## 1. Sudoku: CSP Implementation and Evaluation

The Sudoku solver is implemented in Python without an external CSP-solving library. It combines candidate-mask representation, constraint propagation, Minimum Remaining Values (MRV) variable selection, and depth-first backtracking.

The implementation validates puzzle inputs, detects contradictions, and returns the first solution found. Solution uniqueness is not checked. A* is analysed theoretically in the coursework report and is not implemented in the solver.

### Requirements

- Python 3.10 or newer
- Python standard library for the solver, tests, and benchmark

### Run

Execute commands from the repository root.

**Solve a puzzle:**

```bash
python Sudoku/solver.py Sudoku/puzzles/norvig_01.txt
```

**Display solving statistics:**

```bash
python Sudoku/solver.py Sudoku/puzzles/norvig_01.txt --stats
```

**Run unit tests:**

```bash
python -m unittest discover -s Sudoku/tests -v
```

**Run the benchmark suite:**

```bash
python Sudoku/benchmark.py
```

### Recorded Evaluation

- **Unit tests:** 33 passed.
- **Benchmark suite:** 9 puzzle cases, each measured over 7 runs following a warm-up.
- **Solvable cases:** 7.
- **Unsatisfiable cases:** 2.

Benchmark summaries and raw measurements are available in `Sudoku/evaluation/`. Reported execution times are machine-dependent; detailed methodology and results are presented in the coursework report.

## 2. Automated Planning: PDDL

The planning component models lunar rover operations using typed STRIPS-style PDDL.

The base domain defines rover deployment and movement, image capture, scanning, data transmission, sample collection, and sample storage. The extended domain introduces astronauts and room-location constraints.

### Domain and Problem Files

| Mission | Domain | Problem | Plan file |
|---|---|---|---|
| 1 | `PDDL/PartA&B/domain.pddl` | `PDDL/PartA&B/mission1.pddl` | `PDDL/PartA&B/mission1.pddl.soln` |
| 2 | `PDDL/PartA&B/domain.pddl` | `PDDL/PartA&B/mission2.pddl` | `PDDL/PartA&B/mission2.pddl.soln` |
| 3 | `PDDL/PartC/domain-ext.pddl` | `PDDL/PartC/mission3.pddl` | `PDDL/PartC/mission3.pddl.soln` |

### Plan Generation

The plans were generated using Pyperplan 2.1 with greedy best-first search and the FF heuristic.

Example command:

```bash
pyperplan -H hff -s gbf "PDDL/PartA&B/domain.pddl" "PDDL/PartA&B/mission1.pddl"
```

### Validation

The recorded plans were validated using VAL.

| Mission | Plan length | VAL result |
|---|---:|---|
| 1 | 10 actions | Plan valid |
| 2 | 20 actions | Plan valid |
| 3 | 24 actions | Plan valid |

The separate semantic checker reported **43 checks passed**. These checks examine selected domain constraints, plan execution, and mission goals; they are not a formal proof of correctness.

**Run the semantic checker:**

```bash
python validation/check_model.py
```

**Run VAL validation on Windows:**

```cmd
powershell -ExecutionPolicy Bypass -File ".vscode\run-pddl-validation.ps1"
```

The VAL validation script requires a working VAL installation at the location configured in the script.

## Coursework Artefacts

- `Coursework_Report.pdf` — combined coursework report.
- `Coursework_Report.md` — report source.
- `DEMO_GUIDE.md` — demonstration instructions.
- `Sudoku/evaluation/` — benchmark results and supporting evidence.
- `validation/` — planning validation scripts, recorded plans, and results.

## Reproducibility

Run the commands from the repository root and ensure the required Python environment and planning-validation tools are available. The report documents the implementation approach, experimental methodology, results, and analysis.

