"""Flask composition root and HTTP routes for the Sudoku application."""

import logging

from flask import Flask, jsonify, render_template, request

import request_validation
from game_service import GameService


CURRENT = {
    'puzzle': None,
    'solution': None,
    'hint_count': 0,
    'difficulty': None,
}


class DebugInfoFilter(logging.Filter):
    """Allow informational logs only when the application is in debug mode."""

    def __init__(self, flask_app):
        super().__init__()
        self.flask_app = flask_app

    def filter(self, record):
        return record.levelno >= logging.WARNING or self.flask_app.debug


def setup_logging(flask_app):
    """Configure the application file logger without duplicate handlers."""
    for handler in list(flask_app.logger.handlers):
        if isinstance(handler, logging.FileHandler) and handler.baseFilename.endswith('app.log'):
            flask_app.logger.removeHandler(handler)

    file_handler = logging.FileHandler('app.log')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    ))
    file_handler.addFilter(DebugInfoFilter(flask_app))
    flask_app.logger.addHandler(file_handler)
    flask_app.logger.setLevel(logging.INFO)
    flask_app.logger.propagate = False


def create_app(state=None):
    """Create and configure a Flask application instance.

    Args:
        state: Optional mutable game-state mapping, useful for isolated tests.
    """
    flask_app = Flask(__name__)
    # Flask derives the default logger name from the import name; use an
    # instance-specific logger so application factories remain isolated.
    flask_app.logger = logging.getLogger(f"sudoku_app.{id(flask_app)}")
    game_state = state if state is not None else CURRENT
    game_service = GameService(game_state)
    setup_logging(flask_app)

    @flask_app.after_request
    def log_request_info(response):
        flask_app.logger.info(
            "Request: %s %s | IP: %s | Response Code: %d",
            request.method,
            request.full_path.rstrip('?'),
            request.remote_addr or '127.0.0.1',
            response.status_code,
        )
        return response

    @flask_app.errorhandler(405)
    def handle_method_not_allowed(error):
        return jsonify({'error': 'Method not allowed'}), 405

    @flask_app.errorhandler(Exception)
    def handle_unexpected_error(error):
        flask_app.logger.error(
            "Unhandled server exception: %s | Response Code: 500",
            error,
            exc_info=True,
        )
        return jsonify({'error': 'Internal server error'}), 500

    @flask_app.route('/')
    def index():
        """Render the main Sudoku game interface."""
        return render_template('index.html')

    @flask_app.route('/new')
    def new_game():
        """Generate a puzzle from the optional ``clues`` query parameter."""
        raw_clues = request.args.get('clues', 35)
        try:
            clues = request_validation.parse_clues(raw_clues)
            puzzle = game_service.start_game(clues)
        except ValueError as error:
            flask_app.logger.warning("Invalid clue parameter '%s': %s", raw_clues, error)
            return jsonify({'error': str(error)}), 400
        except RuntimeError:
            flask_app.logger.error(
                "Puzzle generation failed for clues=%s",
                raw_clues,
                exc_info=True,
            )
            return jsonify({'error': 'Internal server error'}), 500

        flask_app.logger.info("Successfully generated puzzle with %d clues", clues)
        return jsonify({'puzzle': puzzle})

    @flask_app.route('/hint', methods=['POST'])
    def hint():
        """Reveal one empty cell from the active puzzle."""
        try:
            return jsonify(game_service.give_hint())
        except LookupError as error:
            flask_app.logger.warning("Hint request failed: %s", error)
            return jsonify({'error': str(error)}), 400

    @flask_app.route('/check', methods=['POST'])
    def check_solution():
        """Validate a submitted 9x9 board against the active solution."""
        try:
            board, payload = request_validation.parse_json_board(request)
            result = game_service.check_solution(board, payload.get('time_taken', 0))
        except LookupError as error:
            flask_app.logger.warning("Check solution failed: %s", error)
            return jsonify({'error': str(error)}), 400
        except ValueError as error:
            flask_app.logger.warning("Invalid solution request: %s", error)
            return jsonify({'error': str(error)}), 400

        flask_app.logger.info(
            "Solution check completed: %d incorrect cells found",
            len(result['incorrect']),
        )
        return jsonify(result)

    return flask_app


app = create_app()


if __name__ == '__main__':
    app.run(debug=True)