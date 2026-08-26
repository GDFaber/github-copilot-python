import copy
import unittest
from unittest.mock import patch

import sudoku_logic


class TestSudokuLogic(unittest.TestCase):
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
        board = sudoku_logic.create_empty_board()
        board[0][5] = 4

        self.assertFalse(sudoku_logic.is_safe(board, 0, 0, 4))


    def test_is_safe_false_when_number_in_column(self):
        board = sudoku_logic.create_empty_board()
        board[6][0] = 8

        self.assertFalse(sudoku_logic.is_safe(board, 0, 0, 8))


    def test_is_safe_false_when_number_in_box(self):
        board = sudoku_logic.create_empty_board()
        board[1][1] = 9

        self.assertFalse(sudoku_logic.is_safe(board, 2, 2, 9))


    def test_is_safe_true_when_valid_placement(self):
        board = sudoku_logic.create_empty_board()
        board[0][1] = 1
        board[1][0] = 2
        board[1][1] = 3

        self.assertTrue(sudoku_logic.is_safe(board, 0, 0, 4))


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

        sudoku_logic.remove_cells(board, sudoku_logic.SIZE * sudoku_logic.SIZE)

        self.assertEqual(board, before)


    def test_remove_cells_removes_only_when_selected_cell_is_not_empty(self):
        board = sudoku_logic.create_empty_board()
        board[0][0] = 7
        board[0][1] = 8

        # Coordinates: (0,0) remove, (0,0) already empty, (0,1) remove
        with patch("sudoku_logic.random.randrange", side_effect=[0, 0, 0, 0, 0, 1]):
            sudoku_logic.remove_cells(board, 79)

        self.assertEqual(board[0][0], sudoku_logic.EMPTY)
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


if __name__ == "__main__":
    unittest.main()