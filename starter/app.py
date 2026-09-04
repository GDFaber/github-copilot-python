"""
Flask web application for the Sudoku game.

Provides HTTP routes for rendering the Sudoku web UI, generating new game
puzzles with customizable clue counts, and checking user solutions.
Configures server-side logging to output formatted logs to 'app.log'.
"""

import logging
import random
from flask import Flask, render_template, jsonify, request
import sudoku_logic

app = Flask(__name__)

# Keep a simple in-memory store for current puzzle, solution and hint count
CURRENT = {
    'puzzle': None,
    'solution': None,
    'hint_count': 0,
    'difficulty': None
}


class DebugInfoFilter(logging.Filter):
    """
    Logging filter that allows INFO entries only when flask_app.debug is True.
    WARNING, ERROR, and higher log levels are always logged.
    """
    def __init__(self, flask_app):
        super().__init__()
        self.flask_app = flask_app

    def filter(self, record):
        if record.levelno < logging.WARNING:
            return bool(self.flask_app.debug)
        return True


def setup_logging(flask_app):
    """
    Configure file handler logging to 'app.log'.

    Includes timestamp, log level, filename, line number, response code, and log message.
    Ties logging of INFO entries to flask_app.debug being True.
    """
    # Remove existing FileHandlers for app.log to prevent duplicates on re-import
    for handler in list(flask_app.logger.handlers):
        if isinstance(handler, logging.FileHandler) and getattr(handler, 'baseFilename', '').endswith('app.log'):
            flask_app.logger.removeHandler(handler)

    file_handler = logging.FileHandler('app.log')
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    file_handler.addFilter(DebugInfoFilter(flask_app))

    flask_app.logger.addHandler(file_handler)
    flask_app.logger.setLevel(logging.INFO)
    flask_app.logger.propagate = False


setup_logging(app)


@app.after_request
def log_request_info(response):
    """
    Log request details and response status code after each HTTP request.
    """
    app.logger.info(
        "Request: %s %s | IP: %s | Response Code: %d",
        request.method,
        request.full_path.rstrip('?'),
        request.remote_addr or '127.0.0.1',
        response.status_code
    )
    return response


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    """
    Log unhandled exceptions with full stack trace and return a 500 JSON error response.
    """
    app.logger.error("Unhandled server exception: %s | Response Code: 500", error, exc_info=True)
    return jsonify({'error': 'Internal server error'}), 500


@app.route('/')
def index():
    """Render the main Sudoku game interface."""
    app.logger.info("Rendering index page")
    return render_template('index.html')


@app.route('/new')
def new_game():
    """
    Generate a new Sudoku puzzle and solution.

    Query Parameters:
        clues (int, optional): Number of clues to keep (default: 35).

    Returns:
        JSON object containing the puzzle matrix or an error message with HTTP status code.
    """
    raw_clues = request.args.get('clues', 35)
    try:
        clues = int(raw_clues)
        puzzle, solution = sudoku_logic.generate_puzzle(clues)
    except (TypeError, ValueError) as err:
        app.logger.warning(
            "Invalid clue parameter '%s': %s | Response Code: 400",
            raw_clues,
            err
        )
        return jsonify({
            'error': f'Clues must be between {sudoku_logic.MIN_CLUES} and {sudoku_logic.MAX_CLUES}'
        }), 400
    except RuntimeError as err:
        app.logger.error(
            "Puzzle generation failed for clues=%s: %s | Response Code: 500",
            raw_clues,
            err,
            exc_info=True
        )
        return jsonify({'error': 'Internal server error'}), 500

    CURRENT['puzzle'] = puzzle
    CURRENT['solution'] = solution
    CURRENT['hint_count'] = 0
    CURRENT['difficulty'] = next(
        (name for name, clue_count in {'easy': 50, 'medium': 40, 'hard': 30}.items()
         if clue_count == clues),
        'medium'
    )
    app.logger.info("Successfully generated puzzle with %d clues", clues)
    return jsonify({'puzzle': puzzle})


@app.route('/hint', methods=['POST'])
def hint():
    """
    Reveal the correct value for one random empty cell of the current puzzle.

    Returns:
        JSON object containing the row, column, value and updated hint count,
        or an error message with HTTP status code.
    """
    puzzle = CURRENT.get('puzzle')
    solution = CURRENT.get('solution')

    if puzzle is None or solution is None:
        app.logger.warning("Hint request failed: No game in progress | Response Code: 400")
        return jsonify({'error': 'No game in progress'}), 400

    empty_cells = [
        (row, col)
        for row in range(sudoku_logic.SIZE)
        for col in range(sudoku_logic.SIZE)
        if puzzle[row][col] == sudoku_logic.EMPTY
    ]

    if not empty_cells:
        app.logger.warning("Hint request failed: No empty cells remaining | Response Code: 400")
        return jsonify({'error': 'No empty cells remaining'}), 400

    row, col = random.choice(empty_cells)
    value = solution[row][col]
    puzzle[row][col] = value
    CURRENT['hint_count'] += 1

    app.logger.info(
        "Hint given for cell (%d, %d) | Total hints: %d",
        row,
        col,
        CURRENT['hint_count']
    )
    return jsonify({'row': row, 'col': col, 'value': value, 'hint_count': CURRENT['hint_count']})


@app.route('/check', methods=['POST'])
def check_solution():
    """
    Check the submitted board solution against the stored solution.

    JSON Payload:
        board (list of list of int): 9x9 board matrix submitted by client.

    Returns:
        JSON object containing a list of incorrect cell coordinates [row, col]
        or an error message with HTTP status code.
    """
    data = request.json or {}
    board = data.get('board')
    solution = CURRENT.get('solution')

    if solution is None:
        app.logger.warning("Check solution failed: No game in progress | Response Code: 400")
        return jsonify({'error': 'No game in progress'}), 400

    if not board:
        app.logger.warning("Check solution failed: Missing board payload | Response Code: 400")
        return jsonify({'error': 'Invalid request board'}), 400

    incorrect = []
    for i in range(sudoku_logic.SIZE):
        for j in range(sudoku_logic.SIZE):
            if board[i][j] != solution[i][j]:
                incorrect.append([i, j])

    response = {'incorrect': incorrect}
    if not incorrect:
        elapsed_seconds = max(0, int(data.get('time_taken', 0)))
        score = sudoku_logic.calculate_score(
            elapsed_seconds,
            CURRENT['hint_count'],
            CURRENT['difficulty'] or 'medium'
        )
        response['entry'] = {
            'score': score,
            'time_taken': elapsed_seconds,
            'hints_used': CURRENT['hint_count'],
            'difficulty': CURRENT['difficulty'] or 'medium'
        }
        response['score'] = score

    app.logger.info(
        "Solution check completed: %d incorrect cells found",
        len(incorrect)
    )
    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=True)