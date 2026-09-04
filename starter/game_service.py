"""Application service for managing the single active Sudoku game."""

import random

import sudoku_logic


class GameService:
    """Coordinate puzzle generation and operations on active game state."""

    def __init__(self, state):
        """Create a service backed by a mutable state mapping."""
        self.state = state

    def start_game(self, clues):
        """Generate and store a new puzzle for the requested clue count."""
        puzzle, solution = sudoku_logic.generate_puzzle(clues)
        self.state.update({
            'puzzle': puzzle,
            'solution': solution,
            'hint_count': 0,
            'difficulty': self._difficulty_for(clues),
        })
        return puzzle

    def give_hint(self):
        """Reveal one random empty cell from the active puzzle."""
        puzzle = self.state.get('puzzle')
        solution = self.state.get('solution')
        if puzzle is None or solution is None:
            raise LookupError("No game in progress")

        empty_cells = [
            (row, column)
            for row in range(sudoku_logic.SIZE)
            for column in range(sudoku_logic.SIZE)
            if puzzle[row][column] == sudoku_logic.EMPTY
        ]
        if not empty_cells:
            raise LookupError("No empty cells remaining")

        row, column = random.choice(empty_cells)
        puzzle[row][column] = solution[row][column]
        self.state['hint_count'] += 1
        return {
            'row': row,
            'col': column,
            'value': solution[row][column],
            'hint_count': self.state['hint_count'],
        }

    def check_solution(self, board, time_taken=0):
        """Compare a submitted board with the stored solution."""
        solution = self.state.get('solution')
        if solution is None:
            raise LookupError("No game in progress")

        if not isinstance(time_taken, int) or isinstance(time_taken, bool) or time_taken < 0:
            raise ValueError("Time taken must be a non-negative integer")

        incorrect = [
            [row, column]
            for row in range(sudoku_logic.SIZE)
            for column in range(sudoku_logic.SIZE)
            if board[row][column] != solution[row][column]
        ]
        response = {'incorrect': incorrect}
        if not incorrect:
            difficulty = self.state.get('difficulty') or 'medium'
            score = sudoku_logic.calculate_score(
                time_taken,
                self.state.get('hint_count', 0),
                difficulty,
            )
            response['entry'] = {
                'score': score,
                'time_taken': time_taken,
                'hints_used': self.state.get('hint_count', 0),
                'difficulty': difficulty,
            }
            response['score'] = score
        return response

    @staticmethod
    def _difficulty_for(clues):
        """Map standard clue presets to their display difficulty."""
        return next(
            (
                name
                for name, clue_count in {'easy': 50, 'medium': 40, 'hard': 30}.items()
                if clue_count == clues
            ),
            'medium',
        )