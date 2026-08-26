import unittest

from app import app
from sudoku_logic import SIZE


class AppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True


    def test_index_route(self):
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<title>Sudoku Game</title>', response.data)


    def test_new_game_route_default(self):
        response = self.app.get('/new')
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

        # check if there are exactly 35 clues (non-zero cells) in the puzzle
        clues_count = sum(cell != 0 for row in puzzle for cell in row)
        self.assertEqual(clues_count, 35)


    def test_new_game_route_with_clues_arg(self):
        response = self.app.get('/new?clues=10')
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

        # check if there are exactly 10 clues (non-zero cells) in the puzzle
        clues_count = sum(cell != 0 for row in puzzle for cell in row)
        self.assertEqual(clues_count, 10)


    def test_check_route_without_game(self):
        # Attempt to check a solution without starting a game; make sure the CURRENT dictionary is cleared
        from app import CURRENT
        CURRENT['puzzle'] = None
        CURRENT['solution'] = None

        # Now, check the solution with an empty board (all zeros)
        empty_board = [[0 for _ in range(SIZE)] for _ in range(SIZE)]
        response = self.app.post('/check', json={'board': empty_board})
        self.assertEqual(response.status_code, 400)
        data = response.get_json()
        self.assertIn('error', data)
        self.assertEqual(data['error'], 'No game in progress')


    def test_check_route_with_incorrect_solution(self):
        # First, create a new game to have a solution stored
        self.app.get('/new')

        # Now, check the solution with an empty board (all zeros)
        empty_board = [[0 for _ in range(SIZE)] for _ in range(SIZE)]
        response = self.app.post('/check', json={'board': empty_board})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('incorrect', data)
        self.assertTrue(data['incorrect'])


    def test_check_route_with_correct_solution(self):
        # First, create a new game to have a solution stored
        self.app.get('/new')

        # Retrieve the current solution from the app's CURRENT dictionary
        from app import CURRENT
        solution = CURRENT['solution']

        # Now, check the solution with the correct board
        response = self.app.post('/check', json={'board': solution})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertIn('incorrect', data)
        self.assertEqual(data['incorrect'], [])  # No incorrect cells
        

if __name__ == '__main__':
    unittest.main()