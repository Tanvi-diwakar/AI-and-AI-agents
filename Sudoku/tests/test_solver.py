"""Behavioural tests; no third-party dependencies or solver library."""
from dataclasses import asdict
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from solver import PuzzleError, parse_grid, read_grid, solve, validate_grid


def independently_valid(givens, answer):
    """Check output directly, without using the solver's peer/domain machinery."""
    if answer is None or len(answer) != 81:
        return False
    digits = set(range(1, 10))
    if any(g and g != a for g, a in zip(givens, answer)):
        return False
    grid = [answer[r:r + 9] for r in range(0, 81, 9)]
    return (all(set(row) == digits for row in grid)
            and all({grid[r][c] for r in range(9)} == digits for c in range(9))
            and all({grid[r + dr][c + dc] for dr in range(3) for dc in range(3)} == digits
                    for r in (0, 3, 6) for c in (0, 3, 6)))


class SolverTests(unittest.TestCase):
    def fixture(self, name):
        return read_grid(ROOT/'puzzles'/name)

    def text(self):
        return (ROOT/'puzzles'/'generated_45_blanks.txt').read_text()

    def assert_solution(self, grid):
        result = solve(grid)
        self.assertTrue(independently_valid(grid, result.solution))
        return result

    def test_five_published_benchmarks(self):
        for n in range(1, 6):
            with self.subTest(puzzle=n):
                self.assert_solution(self.fixture(f'norvig_{n:02d}.txt'))

    def test_constructed_puzzle(self):
        self.assert_solution(self.fixture('generated_45_blanks.txt'))

    def test_solved_grid_unchanged(self):
        grid = self.fixture('solved.txt')
        result = self.assert_solution(grid)
        self.assertEqual(result.solution, grid)
        self.assertEqual(result.metrics.guesses, 0)

    def test_one_blank(self):
        grid = list(self.fixture('solved.txt'))
        grid[-1] = 0
        result = self.assert_solution(grid)
        self.assertEqual(result.solution, self.fixture('solved.txt'))
        self.assertEqual(result.metrics.guesses, 0)

    def test_nearly_complete(self):
        result = self.assert_solution(self.fixture('nearly_complete.txt'))
        self.assertEqual(result.solution, self.fixture('solved.txt'))
        self.assertEqual(result.metrics.guesses, 0)

    def test_multiple_solutions_accepted(self):
        self.assert_solution(self.fixture('empty.txt'))

    def test_locally_valid_unsatisfiable(self):
        grid = self.fixture('unsatisfiable.txt')
        validate_grid(grid)
        result = solve(grid)
        self.assertIsNone(result.solution)
        self.assertEqual(result.metrics.guesses, 0)
        self.assertEqual(result.metrics.contradictions, 1)

    def test_unsatisfiable_after_search(self):
        result = solve(self.fixture('unsatisfiable_search.txt'))
        self.assertIsNone(result.solution)
        self.assertGreater(result.metrics.guesses, 0)
        self.assertEqual(result.metrics.guesses, result.metrics.backtracks)

    def test_backtracking_is_exercised(self):
        result = self.assert_solution(self.fixture('norvig_04.txt'))
        self.assertGreater(result.metrics.backtracks, 0)
        self.assertGreater(result.metrics.max_depth, 1)

    def test_input_not_mutated(self):
        grid = list(self.fixture('norvig_01.txt'))
        before = grid.copy()
        solve(grid)
        self.assertEqual(grid, before)

    def test_repeated_calls_deterministic(self):
        grid = self.fixture('norvig_01.txt')
        a, b = solve(grid), solve(grid)
        self.assertEqual(a.solution, b.solution)
        ma, mb = asdict(a.metrics), asdict(b.metrics)
        ma.pop('elapsed_seconds'); mb.pop('elapsed_seconds')
        self.assertEqual(ma, mb)

    def test_csv_and_txt_equal(self):
        self.assertEqual(self.fixture('generated_45_blanks.txt'), self.fixture('generated_45_blanks.csv'))

    def test_crlf_and_whitespace(self):
        lines = self.text().splitlines()
        altered = '\r\n'.join('  '+line.replace(' ', '\t')+'  ' for line in lines)+'\r\n'
        self.assertEqual(parse_grid(altered), self.fixture('generated_45_blanks.txt'))

    def test_no_final_newline(self):
        self.assertEqual(parse_grid(self.text().rstrip('\n')), self.fixture('generated_45_blanks.txt'))

    def test_utf8_bom(self):
        with tempfile.TemporaryDirectory() as directory:
            file = Path(directory)/'input.txt'
            file.write_text('\ufeff'+self.text(), encoding='utf-8')
            self.assertEqual(read_grid(file), self.fixture('generated_45_blanks.txt'))

    def test_bad_row_counts(self):
        for text in ['', '\n'.join(self.text().splitlines()[:8]), self.text()+'\n']:
            with self.subTest(text=text), self.assertRaises(PuzzleError):
                parse_grid(text)

    def test_bad_column_counts(self):
        lines = self.text().splitlines()
        for row in ['0 '*8, '0 '*10]:
            with self.subTest(row=row), self.assertRaises(PuzzleError):
                parse_grid('\n'.join([row]+lines[1:]))

    def test_bad_tokens(self):
        for token in ['-1', '10', '1.0', 'x', '.', '+1', '01', '９']:
            with self.subTest(token=token), self.assertRaises(PuzzleError):
                parse_grid(self.text().replace(self.text()[0], token, 1))

    def test_csv_empty_value(self):
        text = (ROOT/'puzzles'/'generated_45_blanks.csv').read_text()
        with self.assertRaises(PuzzleError):
            parse_grid(','+text[2:], csv=True)

    def test_duplicate_row(self):
        grid = [0]*81; grid[0] = grid[3] = 1
        with self.assertRaisesRegex(PuzzleError, 'row'):
            solve(grid)

    def test_duplicate_column(self):
        grid = [0]*81; grid[0] = grid[27] = 1
        with self.assertRaisesRegex(PuzzleError, 'column'):
            solve(grid)

    def test_duplicate_box(self):
        grid = [0]*81; grid[0] = grid[10] = 1
        with self.assertRaisesRegex(PuzzleError, 'box'):
            solve(grid)

    def test_invalid_api_values(self):
        for value in [True, 1.0, -1, 10, '1']:
            grid = [0]*81; grid[0] = value
            with self.subTest(value=value), self.assertRaises(PuzzleError):
                solve(grid)

    def test_invalid_api_size(self):
        for n in [0, 80, 82]:
            with self.subTest(size=n), self.assertRaises(PuzzleError):
                solve([0]*n)

    def test_missing_file(self):
        with self.assertRaises(OSError):
            read_grid(ROOT/'puzzles'/'does-not-exist.txt')

    def test_wrong_extension(self):
        with self.assertRaises(PuzzleError):
            read_grid('input.json')

    def test_twenty_generated_transformations(self):
        # Shuffle bands/rows, stacks/columns and digits while preserving Sudoku.
        rng = random.Random(2026)
        original = self.fixture('solved.txt')
        for case in range(20):
            def order():
                groups = [0, 1, 2]; rng.shuffle(groups)
                result = []
                for group in groups:
                    within = [0, 1, 2]; rng.shuffle(within)
                    result.extend(3*group+i for i in within)
                return result
            rows, cols = order(), order()
            digits = list(range(1, 10)); rng.shuffle(digits)
            transformed = [digits[original[r*9+c]-1] for r in rows for c in cols]
            for cell in rng.sample(range(81), 30+case*2):
                transformed[cell] = 0
            with self.subTest(case=case):
                self.assert_solution(transformed)

    def cli(self, name, *flags):
        return subprocess.run([sys.executable, str(ROOT/'solver.py'),
            str(ROOT/'puzzles'/name), *flags], text=True, capture_output=True, timeout=10)

    def test_cli_solved(self):
        result = self.cli('generated_45_blanks.csv', '--stats')
        self.assertEqual(result.returncode, 0)
        self.assertIn('Solved Sudoku:', result.stdout)
        self.assertIn(' | ', result.stdout)
        self.assertIn('backtracks:', result.stdout)

    def test_cli_unsatisfiable(self):
        result = self.cli('unsatisfiable_search.txt')
        self.assertEqual(result.returncode, 1)
        self.assertIn('No solution exists', result.stdout)

    def test_cli_invalid(self):
        result = self.cli('invalid_duplicate.txt')
        self.assertEqual(result.returncode, 2)
        self.assertIn('Invalid input:', result.stderr)

    def test_cli_json_solved(self):
        result = self.cli('norvig_01.txt', '--json')
        payload = json.loads(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(payload['status'], 'solved')
        self.assertTrue(independently_valid(self.fixture('norvig_01.txt'),
                                          sum(payload['solution'], [])))

    def test_cli_json_invalid(self):
        result = self.cli('invalid_duplicate.txt', '--json')
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)['status'], 'invalid_input')

    def test_cli_missing_file(self):
        result = self.cli('missing.txt')
        self.assertEqual(result.returncode, 2)
        self.assertIn('Invalid input:', result.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
