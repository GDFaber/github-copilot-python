import unittest
from unittest.mock import patch

from app import app
from sudoku_logic import SIZE


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True


    def _assert_new_game_puzzle(self, url, expected_clues):
        response = self.app.get(url)
        self.assertEqual(response.status_code, 200)

        # get value from 'puzzle' key and check if it's a 9x9 grid
        data = response.get_json()
        self.assertIn('puzzle', data)
        puzzle = data['puzzle']
        self.assertEqual(len(puzzle), SIZE)

        # check if each row has 9 elements and each cell is in the range 0-9
        for row in puzzle:
            self.assertEqual(len(row), SIZE)
            for cell in row:
                self.assertIn(cell, range(10))  # Cells should be in range 0-9

        # check if there are exactly the expected number of clues (non-zero cells) in the puzzle
        clues_count = sum(cell != 0 for row in puzzle for cell in row)
        self.assertEqual(clues_count, expected_clues)


    def _check_board(self, board, expected_status, expected_data_key, expected_data_value=None):
        response = self.app.post('/check', json={'board': board})
        self.assertEqual(response.status_code, expected_status)
        data = response.get_json()
        self.assertIn(expected_data_key, data)
        if expected_data_value is not None:
            self.assertEqual(data[expected_data_key], expected_data_value)
        else:
            self.assertTrue(data[expected_data_key])


    def test_index_route(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<title>Sudoku Game</title>', response.data)


    def test_new_game_route_default(self):
        self._assert_new_game_puzzle('/new', 35)


    def test_new_game_route_with_clues_arg(self):
        puzzle = [[0 for _ in range(SIZE)] for _ in range(SIZE)]
        solution = [[1 for _ in range(SIZE)] for _ in range(SIZE)]
        for index in range(20):
            puzzle[index // SIZE][index % SIZE] = 1

        with patch("sudoku_logic.generate_puzzle", return_value=(puzzle, solution)) as generate_mock:
            self._assert_new_game_puzzle('/new?clues=20', 20)

        generate_mock.assert_called_once_with(20)


    def test_new_game_route_rejects_non_integer_clues(self):
        response = self.app.get('/new?clues=abc')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {'error': 'Clues must be between 17 and 81'})


    def test_new_game_route_rejects_clues_below_known_minimum(self):
        response = self.app.get('/new?clues=16')

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.get_json(), {'error': 'Clues must be between 17 and 81'})


    def test_check_route_without_game(self):
        # Attempt to check a solution without starting a game; make sure the CURRENT dictionary is cleared
        from app import CURRENT
        CURRENT['puzzle'] = None
        CURRENT['solution'] = None

        # Now, check the solution with an empty board (all zeros)
        empty_board = [[0 for _ in range(SIZE)] for _ in range(SIZE)]
        self._check_board(empty_board, 400, "error", "No game in progress")


    def test_check_route_with_incorrect_solution(self):
        # First, create a new game to have a solution stored
        self.app.get('/new')

        # Now, check the solution with an empty board (all zeros)
        empty_board = [[0 for _ in range(SIZE)] for _ in range(SIZE)]

        # The response should contain the 'incorrect' key, which lists the incorrect cells
        self._check_board(empty_board, 200, "incorrect")


    def test_check_route_with_correct_solution(self):
        # First, create a new game to have a solution stored
        self.app.get('/new')

        # Retrieve the current solution from the app's CURRENT dictionary
        from app import CURRENT
        solution = CURRENT['solution']

        # Now, check the solution with the correct board (no incorrect cells)
        self._check_board(solution, 200, "incorrect", [])

    def test_logging_to_app_log_file_when_debug_true(self):
        # Set app.debug to True to enable INFO logging
        app.debug = True
        try:
            response = self.app.get('/new?clues=30')
            self.assertEqual(response.status_code, 200)

            # Verify app.log contains INFO logs
            import os
            self.assertTrue(os.path.exists('app.log'))
            with open('app.log', 'r', encoding='utf-8') as f:
                content = f.read()

            self.assertIn('app.py', content)
            self.assertIn('Response Code: 200', content)
            self.assertIn('GET /new?clues=30', content)
        finally:
            app.debug = False

    def test_logging_info_omitted_when_debug_false(self):
        # Ensure app.debug is False
        app.debug = False

        # Clear log file content for clean assertion
        with open('app.log', 'w', encoding='utf-8') as f:
            f.truncate(0)

        # Make an INFO request and a WARNING request
        response_ok = self.app.get('/new?clues=30')
        self.assertEqual(response_ok.status_code, 200)

        response_warn = self.app.get('/new?clues=16')
        self.assertEqual(response_warn.status_code, 400)

        with open('app.log', 'r', encoding='utf-8') as f:
            content = f.read()

        # INFO logs should be omitted when debug is False
        self.assertNotIn('GET /new?clues=30', content)
        self.assertNotIn('[INFO]', content)

        # WARNING logs should still be included
        self.assertIn('[WARNING]', content)
        self.assertIn('Invalid clue parameter', content)


if __name__ == '__main__':
    unittest.main()