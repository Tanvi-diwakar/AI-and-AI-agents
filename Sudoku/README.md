# Sudoku solver: Parts 1A and 1B

Python 3.10 or newer. Tested with Python 3.12.14. The solver, tests and benchmark
use only the standard library; no package installation is needed. The search is
implemented in `solver.py`; it does not use any Sudoku, CSP or solver library.

## Run

From this `Sudoku` directory:

```sh
python3 solver.py puzzles/norvig_01.txt
python3 solver.py puzzles/generated_45_blanks.csv --stats
python3 solver.py puzzles/unsatisfiable_search.txt
python3 solver.py puzzles/norvig_04.txt --json
```

On Windows, use `py -3` or `python` if `python3` is unavailable.

The input file must have exactly 9 lines, each with 9 single digits from 0 to 9.
Zero represents a blank. Use whitespace between values in `.txt` and commas in
`.csv`. Headers, comments, periods, blank interior lines and extra rows are
rejected. Whitespace around values, CRLF line endings, a UTF-8 BOM and an optional
final newline are supported. Examples are in `puzzles/`.

The program prints a solved grid with box separators. If consistent clues have
no completion, it prints `No solution exists for this puzzle.` Malformed files or
repeated givens are reported as invalid input with a reason. Exit codes are 0
(solved), 1 (no solution) and 2 (invalid input or unreadable file).

The solver returns the first solution. It accepts puzzles with multiple solutions
but does not test uniqueness. There is no search-node or runtime cutoff.

## Method

1. Validate the dimensions, values and givens.
2. Represent each cell's candidate set as a nine-bit integer.
3. Propagate each given: remove its value from every row/column/box peer.
   A newly singleton domain is queued for further propagation. An empty domain
   rejects the branch.
4. If every domain is singleton, return the solution.
5. Otherwise select the cell with minimum remaining values (MRV). Break ties in
   row-major order and try candidate digits in ascending order.
6. Copy the domains, set the candidate, propagate, and recursively search. If the
   attempt fails, discard that copy and try the next candidate.

This is one algorithm: depth-first backtracking with MRV and singleton constraint
propagation. Hidden singles, pairs, least-constraining-value ordering, and A* are
not implemented. A* is analysed theoretically in the report, as requested.

## Metrics

`--stats` shows:

- `search_nodes`: recursive search calls after successful propagation, including
  the root and solved leaf when reached.
- `decisions`: calls selecting a cell with more than one candidate.
- `guesses`: candidate assignments attempted.
- `backtracks`: candidate attempts whose entire branch fails. A failed child
  subtree and its failed parent attempt can both contribute.
- `contradictions`: propagation calls that detect an empty candidate domain.
- `forced_assignments`: non-singleton domains made singleton by peer elimination.
- `candidate_eliminations`: individual bits removed by propagation; excludes
  values discarded when choosing a guess.
- `max_depth`: deepest attempted decision branch; the root is depth zero.
- `elapsed_seconds`: validation, initialisation and solving, including metric
  collection. Excludes input file parsing, printing and process startup.

Counts include failed branches and are deterministic. Runtime is machine- and
load-dependent. Forced assignments can exceed 81 because failed branches count.

## Tests and benchmarks

```sh
python3 -m unittest discover -s tests -v
python3 benchmark.py
python3 benchmark.py --repeats 7 --out evaluation_new
```

All 33 unit-test methods passed, including subtests on five published puzzles and
20 generated transformations. Every returned answer is independently checked for
all Sudoku constraints and preservation of givens. Tests cover unsatisfiable
puzzles, malformed files, conflicting clues, solved/empty grids, command-line
exit codes, no input mutation, and deterministic repeat calls.

`benchmark.py` warms up once and records seven solves for each of nine cases.
`evaluation/benchmark.json` contains raw timings, deterministic counters,
environment details and file hashes. `benchmark.csv` contains summaries. The
report uses medians. Independent solution checks are outside the timed region.
The test evidence records no comparison against a separate solver, and the
results do not establish speedups over alternative methods or all puzzles.

## Puzzle sources and construction

- `norvig_01.txt` to `norvig_05.txt`: the first five puzzles, in order, from Peter
  Norvig's [top95 dataset](https://norvig.com/top95.txt), retrieved 26 October 2026.
  Periods were converted to zero and each puzzle to nine space-separated rows.
  These are published benchmark entries, not newly authored puzzles.
- `solved.txt`: constructed using `(3*r + r//3 + c) % 9 + 1`, with zero-based
  row and column indices.
- `nearly_complete.txt`: the same grid with its nine diagonal cells removed.
- `generated_45_blanks.txt` and `.csv`: 45 cells removed from the constructed grid
  using `random.Random(42).sample(range(81), 45)`; both files contain the same
  puzzle. No unverified human difficulty or uniqueness rating is assigned.
- `empty.txt`: all zeros; a deliberate multiple-solution edge case.
- `unsatisfiable.txt`: row 1 has digits 1-8 and a blank at column 9; row 2 column 9
  contains 9. All other cells are blank. There are no duplicate givens, but r1c9
  has no legal value.
- `unsatisfiable_search.txt`: Norvig entry 1 with the extra clue r1c2=6. It has no
  direct duplicate clues but exhaustive search fails after six guesses.
- `invalid_duplicate.txt`: the solved constructed grid with r1c2 changed to 1.

General conceptual reference: Peter Norvig,
[Solving Every Sudoku Puzzle](https://norvig.com/sudoku.html). The delivered code
uses its own bit-mask representation and queue-based propagation; no external
solver code or library is imported. AI assistance is disclosed in the report.
