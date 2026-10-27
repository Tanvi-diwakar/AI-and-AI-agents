#!/usr/bin/env python3
"""Solve 9x9 Sudoku using MRV backtracking and singleton propagation.

Python 3.10+; standard library only. No Sudoku/CSP/constraint-solver library.
Run: python3 solver.py puzzles/norvig_01.txt --stats
"""
from __future__ import annotations

import argparse
from collections import deque
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import sys
from time import perf_counter
from typing import Sequence

SIZE = 9
ALL_DIGITS = (1 << SIZE) - 1
ROWS = tuple(tuple(r * SIZE + c for c in range(SIZE)) for r in range(SIZE))
COLUMNS = tuple(tuple(r * SIZE + c for r in range(SIZE)) for c in range(SIZE))
BOXES = tuple(
    tuple((br + dr) * SIZE + bc + dc for dr in range(3) for dc in range(3))
    for br in (0, 3, 6) for bc in (0, 3, 6)
)
UNITS = ROWS + COLUMNS + BOXES
# Sorted peers make propagation, tie-breaking and search counts reproducible.
PEERS = tuple(
    tuple(sorted({j for unit in UNITS if i in unit for j in unit} - {i}))
    for i in range(81)
)


class PuzzleError(ValueError):
    """Malformed input or conflicting givens, rather than a searched dead end."""


def validate_grid(grid: Sequence[int]) -> None:
    """Validate shape, value range and direct row/column/box clue conflicts."""
    if len(grid) != 81:
        raise PuzzleError(f'Expected 81 cells; found {len(grid)}.')
    for index, value in enumerate(grid):
        if type(value) is not int or not 0 <= value <= 9:
            raise PuzzleError(f'Cell r{index // 9 + 1}c{index % 9 + 1} must be an integer 0-9.')
    for number, unit in enumerate(UNITS):
        seen = set()
        for index in unit:
            digit = grid[index]
            if digit and digit in seen:
                kind = ('row', 'column', 'box')[number // 9]
                raise PuzzleError(f'Conflicting givens: digit {digit} repeats in {kind} {number % 9 + 1}.')
            seen.add(digit)


def parse_grid(text: str, *, csv: bool = False) -> tuple[int, ...]:
    """Read exactly nine rows with nine single-digit values in each row.

    Blank lines inside a puzzle, comments and headers are deliberately rejected.
    A trailing newline and whitespace around values are accepted.
    """
    lines = text.splitlines()
    if len(lines) != 9:
        raise PuzzleError(f'Expected 9 rows; found {len(lines)}.')
    grid = []
    for row, line in enumerate(lines, start=1):
        fields = [part.strip() for part in line.split(',')] if csv else line.split()
        if len(fields) != 9:
            raise PuzzleError(f'Row {row}: expected 9 values; found {len(fields)}.')
        for col, field in enumerate(fields, start=1):
            if field not in tuple('0123456789'):
                raise PuzzleError(f'Cell r{row}c{col}: expected a single digit 0-9; found {field!r}.')
            grid.append(int(field))
    validate_grid(grid)
    return tuple(grid)


def read_grid(path: str | Path) -> tuple[int, ...]:
    path = Path(path)
    if path.suffix.lower() not in {'.txt', '.csv'}:
        raise PuzzleError('Use a .txt (space-separated) or .csv (comma-separated) file.')
    return parse_grid(path.read_text(encoding='utf-8-sig'), csv=path.suffix.lower() == '.csv')


@dataclass
class Metrics:
    # Counters include unsuccessful branches. No counters are rolled back.
    search_nodes: int = 0       # Recursive calls after successful propagation.
    decisions: int = 0          # Search nodes at which a non-singleton is chosen.
    guesses: int = 0            # Candidate assignments actually attempted.
    backtracks: int = 0         # Attempted candidate branches returning failure.
    contradictions: int = 0     # Propagation calls that discover an empty domain.
    forced_assignments: int = 0 # Peer eliminations changing a domain to singleton.
    candidate_eliminations: int = 0  # Bits removed by propagation, not guesses.
    max_depth: int = 0          # Deepest attempted decision branch; root is zero.
    elapsed_seconds: float = 0.0


@dataclass
class SolveResult:
    solution: tuple[int, ...] | None
    metrics: Metrics


def _singleton(mask: int) -> bool:
    return mask != 0 and mask & (mask - 1) == 0


def _propagate(domains: list[int], seeds: Sequence[int], metrics: Metrics) -> bool:
    """Forward-check peers, recursively propagating every new singleton.

    Bit d-1 in a domain represents digit d. Only values conflicting with a
    singleton peer are removed, so no completion consistent with that state is
    lost. An empty domain proves that the current branch cannot be completed.
    """
    queue = deque(seeds)
    while queue:
        cell = queue.popleft()
        value = domains[cell]
        for peer in PEERS[cell]:
            previous = domains[peer]
            if not previous & value:
                continue
            reduced = previous & ~value
            domains[peer] = reduced
            metrics.candidate_eliminations += 1
            if reduced == 0:
                metrics.contradictions += 1
                return False
            if _singleton(reduced):
                metrics.forced_assignments += 1
                queue.append(peer)
    return True


def _search(domains: list[int], metrics: Metrics, depth: int) -> list[int] | None:
    metrics.search_nodes += 1
    # MRV: fewest candidates first, with cell index as a deterministic tie-break.
    candidates = [(mask.bit_count(), cell) for cell, mask in enumerate(domains)
                  if mask.bit_count() > 1]
    if not candidates:
        return domains
    _, cell = min(candidates)
    metrics.decisions += 1
    options = domains[cell]
    while options:
        # Lowest remaining bit selects the smallest candidate digit.
        value = options & -options
        options ^= value
        metrics.guesses += 1
        metrics.max_depth = max(metrics.max_depth, depth + 1)
        # Copying avoids leaking propagated changes into sibling branches.
        child = domains.copy()
        child[cell] = value
        if _propagate(child, [cell], metrics):
            answer = _search(child, metrics, depth + 1)
            if answer is not None:
                return answer
        metrics.backtracks += 1
    return None


def solve(grid: Sequence[int]) -> SolveResult:
    """Return the first solution, or None if no solution exists.

    Conflicting givens raise PuzzleError. Valid clues do not guarantee existence
    or uniqueness; this solver does not count solutions or certify uniqueness.
    The input sequence is never modified. Search has no artificial node cap.
    """
    started = perf_counter()
    validate_grid(grid)
    metrics = Metrics()
    domains = [(1 << (digit - 1)) if digit else ALL_DIGITS for digit in grid]
    seeds = [cell for cell, digit in enumerate(grid) if digit]
    result = None
    if _propagate(domains, seeds, metrics):
        result = _search(domains, metrics, 0)
    solution = None if result is None else tuple(mask.bit_length() for mask in result)
    metrics.elapsed_seconds = perf_counter() - started
    return SolveResult(solution, metrics)


def format_grid(grid: Sequence[int]) -> str:
    """Print box separators without depending on terminal colour support."""
    rows = []
    for row in range(9):
        if row and row % 3 == 0:
            rows.append('------+-------+------')
        values = [str(grid[row * 9 + col]) if grid[row * 9 + col] else '.' for col in range(9)]
        rows.append(' | '.join(' '.join(values[start:start + 3]) for start in (0, 3, 6)))
    return '\n'.join(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('puzzle', type=Path, help='9x9 .txt or .csv file; 0 means blank')
    parser.add_argument('--stats', action='store_true', help='display measured search statistics')
    parser.add_argument('--json', action='store_true', help='emit a machine-readable result')
    args = parser.parse_args(argv)
    try:
        grid = read_grid(args.puzzle)
        result = solve(grid)
    except (PuzzleError, OSError, UnicodeError) as error:
        if args.json:
            print(json.dumps({'status': 'invalid_input', 'error': str(error)}))
        else:
            print(f'Invalid input: {error}', file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps({'status': 'solved' if result.solution is not None else 'unsatisfiable',
                          'solution': ([list(result.solution[r:r + 9]) for r in range(0, 81, 9)]
                                       if result.solution is not None else None),
                          'metrics': asdict(result.metrics)}, indent=2))
    else:
        print('Solved Sudoku:' if result.solution is not None else 'No solution exists for this puzzle.')
        if result.solution is not None:
            print(format_grid(result.solution))
        if args.stats:
            print('\nSearch statistics:')
            for name, value in asdict(result.metrics).items():
                print(f'  {name}: {value:.6f}' if isinstance(value, float) else f'  {name}: {value}')
    return 0 if result.solution is not None else 1


if __name__ == '__main__':
    raise SystemExit(main())
