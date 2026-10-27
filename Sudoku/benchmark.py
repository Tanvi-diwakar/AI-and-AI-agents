#!/usr/bin/env python3
"""Reproduce the report's measurements; uses only the Python standard library.

One warm-up and seven measured solves per puzzle by default. Input parsing and
independent answer verification are outside the solver's internal timer. Reports
include all repetitions, platform details, source hashes, and search counters.
"""
import argparse
from dataclasses import asdict
from datetime import datetime, timezone
import csv
import hashlib
import json
from pathlib import Path
import platform
import statistics
import subprocess

from solver import read_grid, solve

ROOT = Path(__file__).resolve().parent
CASES = [
    ('nearly_complete.txt', 'Nearly complete', 'solved'),
    ('generated_45_blanks.txt', 'Generated-45', 'solved'),
    *[(f'norvig_{n:02d}.txt', f'Norvig {n}', 'solved') for n in range(1, 6)],
    ('unsatisfiable.txt', 'Unsat-immediate', 'unsatisfiable'),
    ('unsatisfiable_search.txt', 'Unsat-search', 'unsatisfiable'),
]


def verify(givens, answer):
    if answer is None or len(answer) != 81:
        return False
    digits = set(range(1, 10))
    return (all(g == 0 or g == a for g, a in zip(givens, answer))
        and all(set(answer[r:r+9]) == digits for r in range(0, 81, 9))
        and all(set(answer[c::9]) == digits for c in range(9))
        and all({answer[(r+dr)*9+c+dc] for dr in range(3) for dc in range(3)} == digits
                for r in (0, 3, 6) for c in (0, 3, 6)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repeats', type=int, default=7)
    parser.add_argument('--out', type=Path, default=ROOT/'evaluation')
    args = parser.parse_args()
    if args.repeats < 1:
        parser.error('--repeats must be positive')
    args.out.mkdir(parents=True, exist_ok=True)
    summaries, runs = [], []
    for filename, label, expected in CASES:
        path = ROOT/'puzzles'/filename
        grid = read_grid(path)
        solve(grid)  # Warm-up excluded from statistics.
        measurements = []
        deterministic = None
        for repeat in range(args.repeats):
            result = solve(grid)
            status = 'solved' if result.solution is not None else 'unsatisfiable'
            assert status == expected, filename
            if result.solution is not None:
                assert verify(grid, result.solution), filename
            metrics = asdict(result.metrics)
            counts = {k:v for k,v in metrics.items() if k != 'elapsed_seconds'}
            if deterministic is None:
                deterministic = counts
            else:
                assert counts == deterministic
            measurements.append(metrics['elapsed_seconds']*1000)
            runs.append({'puzzle': filename, 'repeat': repeat+1, 'status': status, **metrics})
        if result.solution is not None:
            (args.out/(path.stem+'-solution.txt')).write_text('\n'.join(
                ' '.join(map(str,result.solution[r:r+9])) for r in range(0,81,9))+'\n')
        summary = {'puzzle': filename, 'label': label, 'givens': sum(v != 0 for v in grid),
                   'status': expected, 'repeats': args.repeats,
                   'median_ms': statistics.median(measurements),
                   'min_ms': min(measurements), 'max_ms': max(measurements), **deterministic}
        summaries.append(summary)
        print(f'{label:18} {expected:13} {summary["median_ms"]:9.3f} ms  '
              f'guesses={summary["guesses"]:6}  backtracks={summary["backtracks"]:6}')
    cpu = platform.processor() or platform.machine()
    if platform.system() == 'Darwin':
        cpu = subprocess.check_output(['sysctl','-n','machdep.cpu.brand_string'], text=True).strip()
    metadata = {'date_utc': datetime.now(timezone.utc).isoformat(),
                'python': platform.python_version(), 'platform': platform.platform(), 'cpu': cpu,
                'timer': 'time.perf_counter inside solve: includes validation/initialisation/search; excludes file I/O and printing',
                'warmups_per_puzzle': 1, 'repeats': args.repeats,
                'solver_sha256': hashlib.sha256((ROOT/'solver.py').read_bytes()).hexdigest(),
                'puzzle_sha256': {name:hashlib.sha256((ROOT/'puzzles'/name).read_bytes()).hexdigest()
                                  for name,_,_ in CASES}}
    (args.out/'benchmark.json').write_text(json.dumps({'environment':metadata,'summary':summaries,'runs':runs}, indent=2)+'\n')
    with (args.out/'benchmark.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summaries[0]))
        writer.writeheader(); writer.writerows(summaries)


if __name__ == '__main__':
    main()
