"""Pure Sudoku board generation, validation, and scoring logic."""

import copy
import random

SIZE = 9
EMPTY = 0
MIN_CLUES = 17
MAX_CLUES = SIZE * SIZE
MAX_GENERATION_ATTEMPTS = 20
DIFFICULTY_MULTIPLIERS = {
    'easy': 1.0,
    'medium': 1.35,
    'hard': 1.8,
}

def deep_copy(board):
    """Return an independent copy of a Sudoku board."""
    return copy.deepcopy(board)

def create_empty_board():
    """Return a new 9x9 board filled with empty cells."""
    return [[EMPTY for _ in range(SIZE)] for _ in range(SIZE)]

def is_safe(board, row, col, num):
    """Return whether ``num`` can be placed at the given coordinates."""
    # Check row and column
    for x in range(SIZE):
        if board[row][x] == num or board[x][col] == num:
            return False
    # Check 3x3 box
    start_row = row - row % 3
    start_col = col - col % 3
    for i in range(3):
        for j in range(3):
            if board[start_row + i][start_col + j] == num:
                return False
    return True

def validate_clues(clues):
    """Raise ``ValueError`` when a clue count is outside the supported range."""
    if isinstance(clues, bool) or not isinstance(clues, int) or not MIN_CLUES <= clues <= MAX_CLUES:
        raise ValueError(f"Clues must be between {MIN_CLUES} and {MAX_CLUES}")

def calculate_score(time_taken, hints_taken, difficulty):
    """Calculate a Sudoku score from elapsed time, hints, and difficulty."""
    if time_taken < 0 or hints_taken < 0:
        raise ValueError("Time and hints cannot be negative")
    if difficulty not in DIFFICULTY_MULTIPLIERS:
        raise ValueError(f"Unknown difficulty: {difficulty}")

    time_factor = 300 / (300 + time_taken)
    hint_factor = max(0.25, 1 - (0.10 * hints_taken))
    return round(1000 * DIFFICULTY_MULTIPLIERS[difficulty] * time_factor * hint_factor)

def count_solutions(board, limit=2):
    """Count board completions, stopping once ``limit`` is reached."""
    for row in range(SIZE):
        for col in range(SIZE):
            if board[row][col] == EMPTY:
                solutions = 0
                for candidate in range(1, SIZE + 1):
                    if is_safe(board, row, col, candidate):
                        board[row][col] = candidate
                        solutions += count_solutions(board, limit - solutions)
                        board[row][col] = EMPTY
                        if solutions >= limit:
                            return solutions
                return solutions
    return 1

def fill_board(board):
    """Fill a board in place using randomized backtracking."""
    for row in range(SIZE):
        for col in range(SIZE):
            if board[row][col] == EMPTY:
                possible = list(range(1, SIZE + 1))
                random.shuffle(possible)
                for candidate in possible:
                    if is_safe(board, row, col, candidate):
                        board[row][col] = candidate
                        if fill_board(board):
                            return True
                        board[row][col] = EMPTY
                return False
    return True

def remove_cells(board, clues):
    """Remove cells in place while preserving a unique puzzle solution."""
    validate_clues(clues)
    cells_to_remove = MAX_CLUES - clues
    positions = [(row, col) for row in range(SIZE) for col in range(SIZE)]

    while cells_to_remove > 0:
        random.shuffle(positions)
        removed_this_pass = False

        for row, col in positions:
            if board[row][col] == EMPTY:
                continue

            removed = board[row][col]
            board[row][col] = EMPTY
            if count_solutions(board) == 1:
                cells_to_remove -= 1
                removed_this_pass = True
                if cells_to_remove == 0:
                    return
            else:
                board[row][col] = removed

        if not removed_this_pass:
            raise RuntimeError("Unable to generate a puzzle with a unique solution")

def generate_puzzle(clues=35):
    """Return a uniquely solvable puzzle and its complete solution."""
    validate_clues(clues)

    for _ in range(MAX_GENERATION_ATTEMPTS):
        board = create_empty_board()
        if not fill_board(board):
            continue
        solution = deep_copy(board)
        try:
            remove_cells(board, clues)
        except RuntimeError:
            continue
        puzzle = deep_copy(board)
        return puzzle, solution

    raise RuntimeError("Unable to generate a puzzle with a unique solution")
