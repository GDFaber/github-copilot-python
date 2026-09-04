import copy
import unittest
from unittest.mock import patch

import sudoku_logic


class TestSudokuLogic(unittest.TestCase):
    def _assert_not_safe(self, set_row, set_col, check_row, check_col, num):
        board = sudoku_logic.create_empty_board()
        board[set_row][set_col] = num

        self.assertFalse(sudoku_logic.is_safe(board, check_row, check_col, num))


    def test_deep_copy_returns_independent_board(self):
        original = sudoku_logic.create_empty_board()
        original[0][0] = 7

        cloned = sudoku_logic.deep_copy(original)
        cloned[0][0] = 3

        self.assertEqual(original[0][0], 7)
        self.assertEqual(cloned[0][0], 3)
        self.assertIsNot(original, cloned)


    def test_create_empty_board_shape_and_values(self):
        board = sudoku_logic.create_empty_board()

        self.assertEqual(len(board), sudoku_logic.SIZE)
        self.assertTrue(all(len(row) == sudoku_logic.SIZE for row in board))
        self.assertTrue(all(cell == sudoku_logic.EMPTY for row in board for cell in row))


    def test_is_safe_false_when_number_in_row(self):
        self._assert_not_safe(0, 5, 0, 0, 4)


    def test_is_safe_false_when_number_in_column(self):
        self._assert_not_safe(6, 0, 0, 0, 8)


    def test_is_safe_false_when_number_in_box(self):
        self._assert_not_safe(1, 1, 2, 2, 9)


    def test_is_safe_true_when_valid_placement(self):
        board = sudoku_logic.create_empty_board()
        board[0][1] = 1
        board[1][0] = 2
        board[1][1] = 3

        self.assertTrue(sudoku_logic.is_safe(board, 0, 0, 4))


    def test_validate_clues_rejects_below_known_minimum(self):
        with self.assertRaises(ValueError):
            sudoku_logic.validate_clues(sudoku_logic.MIN_CLUES - 1)


    def test_validate_clues_rejects_above_cell_count(self):
        with self.assertRaises(ValueError):
            sudoku_logic.validate_clues(sudoku_logic.MAX_CLUES + 1)

    def test_calculate_score_applies_time_hints_and_difficulty(self):
        self.assertEqual(sudoku_logic.calculate_score(0, 0, 'easy'), 1000)
        self.assertEqual(sudoku_logic.calculate_score(300, 0, 'medium'), 675)
        self.assertEqual(sudoku_logic.calculate_score(0, 2, 'hard'), 1440)

    def test_calculate_score_limits_hint_penalty(self):
        self.assertEqual(sudoku_logic.calculate_score(0, 10, 'easy'), 250)

    def test_calculate_score_rejects_invalid_values(self):
        with self.assertRaises(ValueError):
            sudoku_logic.calculate_score(-1, 0, 'easy')
        with self.assertRaises(ValueError):
            sudoku_logic.calculate_score(0, 0, 'expert')


    def test_count_solutions_stops_at_limit_for_empty_board(self):
        board = sudoku_logic.create_empty_board()

        self.assertEqual(sudoku_logic.count_solutions(board), 2)


    def test_fill_board_returns_true_for_already_full_board(self):
        board = [[1 for _ in range(sudoku_logic.SIZE)] for _ in range(sudoku_logic.SIZE)]

        self.assertTrue(sudoku_logic.fill_board(board))


    def test_fill_board_success_path_returns_true(self):
        board = [[1 for _ in range(sudoku_logic.SIZE)] for _ in range(sudoku_logic.SIZE)]
        board[0][0] = sudoku_logic.EMPTY

        original_fill_board = sudoku_logic.fill_board

        with patch("sudoku_logic.random.shuffle", side_effect=lambda values: None), patch(
            "sudoku_logic.is_safe", side_effect=lambda *_: True
        ), patch("sudoku_logic.fill_board", side_effect=lambda *_: True):
            result = original_fill_board(board)

        self.assertTrue(result)
        self.assertEqual(board[0][0], 1)


    def test_fill_board_backtracks_and_returns_false(self):
        board = [[1 for _ in range(sudoku_logic.SIZE)] for _ in range(sudoku_logic.SIZE)]
        board[0][0] = sudoku_logic.EMPTY

        def fake_is_safe(_board, _row, _col, candidate):
            return candidate == 1

        original_fill_board = sudoku_logic.fill_board

        with patch("sudoku_logic.random.shuffle", side_effect=lambda values: None), patch(
            "sudoku_logic.is_safe", side_effect=fake_is_safe
        ), patch("sudoku_logic.fill_board", side_effect=lambda *_: False):
            result = original_fill_board(board)

        self.assertFalse(result)
        self.assertEqual(board[0][0], sudoku_logic.EMPTY)


    def test_fill_board_returns_false_when_no_candidate_is_safe(self):
        board = [[1 for _ in range(sudoku_logic.SIZE)] for _ in range(sudoku_logic.SIZE)]
        board[0][0] = sudoku_logic.EMPTY

        original_fill_board = sudoku_logic.fill_board

        with patch("sudoku_logic.random.shuffle", side_effect=lambda values: None), patch(
            "sudoku_logic.is_safe", side_effect=lambda *_: False
        ):
            result = original_fill_board(board)

        self.assertFalse(result)
        self.assertEqual(board[0][0], sudoku_logic.EMPTY)


    def test_remove_cells_noop_when_clues_equal_cell_count(self):
        board = [[5 for _ in range(sudoku_logic.SIZE)] for _ in range(sudoku_logic.SIZE)]
        before = copy.deepcopy(board)

        sudoku_logic.remove_cells(board, sudoku_logic.MAX_CLUES)

        self.assertEqual(board, before)


    def test_remove_cells_keeps_removal_only_when_puzzle_stays_unique(self):
        board = [[5 for _ in range(sudoku_logic.SIZE)] for _ in range(sudoku_logic.SIZE)]

        def fake_shuffle(positions):
            positions[:] = [(0, 0), (0, 1)]

        with patch("sudoku_logic.random.shuffle", side_effect=fake_shuffle), patch(
            "sudoku_logic.count_solutions", side_effect=[2, 1]
        ):
            sudoku_logic.remove_cells(board, sudoku_logic.MAX_CLUES - 1)

        self.assertEqual(board[0][0], 5)
        self.assertEqual(board[0][1], sudoku_logic.EMPTY)


    def test_generate_puzzle_returns_puzzle_and_solution(self):
        seed_board = sudoku_logic.create_empty_board()

        def fake_fill_board(board):
            board[0][0] = 9
            return True

        def fake_remove_cells(board, _clues):
            board[0][0] = sudoku_logic.EMPTY

        with patch("sudoku_logic.create_empty_board", return_value=seed_board), patch(
            "sudoku_logic.fill_board", side_effect=fake_fill_board
        ) as fill_mock, patch(
            "sudoku_logic.remove_cells", side_effect=fake_remove_cells
        ) as remove_mock:
            puzzle, solution = sudoku_logic.generate_puzzle(clues=40)

        self.assertEqual(solution[0][0], 9)
        self.assertEqual(puzzle[0][0], sudoku_logic.EMPTY)
        self.assertIsNot(puzzle, solution)
        fill_mock.assert_called_once_with(seed_board)
        remove_mock.assert_called_once_with(seed_board, 40)


    def test_generate_puzzle_retries_when_unique_removal_fails(self):
        boards = [sudoku_logic.create_empty_board(), sudoku_logic.create_empty_board()]

        def fake_fill_board(board):
            board[0][0] = 9
            return True

        with patch("sudoku_logic.create_empty_board", side_effect=boards), patch(
            "sudoku_logic.fill_board", side_effect=fake_fill_board
        ), patch("sudoku_logic.remove_cells", side_effect=[RuntimeError, None]) as remove_mock:
            puzzle, solution = sudoku_logic.generate_puzzle(clues=40)

        self.assertEqual(remove_mock.call_count, 2)
        self.assertEqual(solution[0][0], 9)
        self.assertEqual(puzzle[0][0], 9)


if __name__ == "__main__":
    unittest.main()