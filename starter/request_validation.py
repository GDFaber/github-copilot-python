"""Validation helpers for data received by the Flask API."""

from numbers import Integral

import sudoku_logic


def parse_clues(raw_clues):
    """Convert and validate a clue-count query parameter."""
    try:
        clues = int(raw_clues)
    except (TypeError, ValueError) as error:
        raise ValueError(
            f"Clues must be between {sudoku_logic.MIN_CLUES} and "
            f"{sudoku_logic.MAX_CLUES}"
        ) from error

    sudoku_logic.validate_clues(clues)
    return clues


def validate_board(board):
    """Validate and return a 9x9 Sudoku board."""
    if not isinstance(board, list) or len(board) != sudoku_logic.SIZE:
        raise ValueError("Board must be 9x9")

    if any(
        not isinstance(row, list) or len(row) != sudoku_logic.SIZE
        for row in board
    ):
        raise ValueError("Board must be 9x9")

    if any(
        not isinstance(cell, Integral) or isinstance(cell, bool) or not 0 <= cell <= 9
        for row in board
        for cell in row
    ):
        raise ValueError("Cell values must be 0-9")

    return board


def parse_json_board(flask_request):
    """Read and validate the board payload from a Flask request."""
    if not flask_request.is_json:
        raise ValueError("Invalid JSON")

    payload = flask_request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValueError("Invalid JSON")

    if "board" not in payload:
        raise ValueError("Invalid request board")

    return validate_board(payload["board"]), payload