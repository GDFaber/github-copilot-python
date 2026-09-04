# Sudoku Application Implementation Guide

## Purpose

This document defines the architectural standards, quality expectations, security requirements, and development practices for the Flask-based Sudoku puzzle application. All contributions must align with the standards and processes described below.

---

## 1. Project Objectives

The Sudoku application is a single-user puzzle game demonstrating clean code practices, comprehensive testing, and production-ready development discipline applied to a small project scope.

### Primary Goals

- Maintain clean, readable, and self-documenting code in line with PEP 8.
- Clearly separate puzzle generation and validation logic from HTTP request handling.
- Validate all external input and provide structured error responses.
- Ensure comprehensive test coverage of critical paths and failure modes.
- Document code behavior through docstrings and comments explaining intent, not implementation.
- Keep the codebase maintainable and suitable for learning, reference, or future enhancement.

---

## 2. Code Quality and Documentation Standards

### Code Quality

All Python code must:

- Follow PEP 8 style guidelines.
- Use descriptive, intent-revealing names for variables, functions, and modules.
- Apply the DRY (Don't Repeat Yourself) principle; extract common patterns into reusable functions.
- Keep functions small and focused on a single responsibility.
- Avoid unnecessary complexity; favor clarity over clever implementations.
- Validate inputs at function boundaries, especially in routes and before domain logic.

### Documentation Requirements

All code contributions must include:

- **Module docstrings**: A concise description of the module's purpose and key responsibilities at the top of each Python file.
- **Function/method docstrings**: Clear descriptions of input parameters, expected return values, and exceptions raised.
- **Inline comments**: Explain *why* non-obvious logic, algorithmic choices, or validation rules exist. Do not comment obvious code.
- **API documentation**: Query parameters, JSON field expectations, and response formats must be documented in or near the route.
- **Configuration and constants**: Default values, clue ranges, board dimensions, and any business rules must be clearly defined and explained.

### Maintainability

Code must be written such that:

- Puzzle generation and validation remain independent of HTTP handling.
- Validation logic is easily testable and reusable.
- Route handlers orchestrate without hiding domain logic.
- State and configuration changes are clearly tracked.
- Future maintainers can understand intent without reverse-engineering behavior.

---

## 3. Project Structure and Responsibilities

### Current Directory Layout

```
starter/
+-- app.py                    # Flask application, routes, and session management
+-- sudoku_logic.py           # Puzzle generation, validation, and board operations
+-- requirements.txt          # Python dependencies
+-- instructions.md           # This file
+-- static/
¦   +-- main.js              # Client-side rendering, interaction, API calls
¦   +-- styles.css           # Presentation and layout
+-- templates/
¦   +-- index.html           # Page structure and controls
+-- tests/
    +-- test_app.py          # Route and API contract tests
    +-- test_sudoku_logic.py # Unit tests for puzzle logic
```

### Backend Responsibilities (app.py)

- Accept HTTP requests and validate query parameters and JSON bodies.
- Enforce constraints: clue count ranges, board dimensions, and cell values.
- Orchestrate calls to puzzle generation and validation functions.
- Maintain the single active game session in memory (puzzle and solution).
- Return appropriate HTTP status codes and JSON responses.
- Handle and log errors without exposing stack traces to the client.

### Domain Logic Responsibilities (sudoku_logic.py)

- Generate valid, solvable Sudoku puzzles with exactly the requested clues.
- Validate that placements follow Sudoku rules (rows, columns, 3×3 boxes).
- Perform board operations (copying, searching, filling) deterministically.
- Never handle HTTP requests, JSON formatting, or session state.

### Frontend Responsibilities (main.js, styles.css, index.html)

- Render the 9×9 board and accept user input.
- Disable prefilled clues and visually distinguish them.
- Provide "New Game" and "Check Solution" controls.
- Make asynchronous requests to the backend API.
- Display validation errors, success messages, and incorrect cells.
- Handle network failures and invalid server responses gracefully.

### Separation of Concerns

- Never implement puzzle logic in routes or JavaScript.
- Never mix HTTP handling with domain algorithms.
- Never trust client-provided solutions; always verify against server-side state.
- Keep configuration (clue ranges, SIZE, EMPTY) centralized and consistent.

---

## 4. Flask Application Organization

The current application is simple and does not require Application Factory or Blueprint patterns. However, maintainable structure is still critical:

### Current Approach

- A single Flask app instance defined in `app.py`.
- Game session (puzzle and solution) stored in module-level dictionary `CURRENT`.
- All routes defined in a single module for clarity and ease of testing.

The implementation uses `create_app(state=None)` as a lightweight application
factory. `app.py` composes the Flask routes and error handlers, while
`request_validation.py` owns HTTP payload validation and `game_service.py`
owns game state transitions. The module-level `app` and `CURRENT` remain as
development and backwards-compatibility entry points.

### Key Constraints

- Do not introduce global mutable state beyond `CURRENT` without clear justification.
- If a future feature requires multiple game sessions or user identification, introduce session management or a database-backed store only after defining ownership, expiration, and concurrency rules.
- Keep the application runnable as `python app.py` from the project root.
- Avoid dependency on external configuration files; use environment variables for production overrides only.

### Future Refactoring

If the application grows significantly, consider:

- **Blueprints**: Separate game logic (`/new`, `/check`) from page serving (`/`).
- **Service layer**: Extract validation and puzzle operations into reusable service functions.
- **Configuration class**: Move hardcoded settings into a config object.

---

## 5. API Design Standards

### Current API

The application exposes three endpoints:

#### GET `/`
- Returns the HTML page.
- Status code: `200 OK` or appropriate error code.

#### GET `/new?clues=<int>`
- Generates and returns a new puzzle.
- Query parameter `clues` (optional): number of clues to include. Default: 35.
- Success response (200):
  ```json
  {
    "puzzle": [[0, 5, 3, ...], [...]]
  }
  ```
- Error response (400):
  ```json
  {
    "error": "Invalid clue count"
  }
  ```

#### POST `/check`
- Validates a completed board against the current solution.
- Request body:
  ```json
  {
    "board": [[1, 2, 3, ...], [...]]
  }
  ```
- Success response (200):
  ```json
  {
    "incorrect": [[0, 0], [1, 5]]
  }
  ```
  If `incorrect` is empty, the puzzle is solved.
- Error response (400):
  ```json
  {
    "error": "No game in progress"
  }
  ```

### HTTP Status Code Requirements

- **200 OK**: Successful request with data.
- **400 Bad Request**: Invalid input (missing game, malformed JSON, invalid clue count, invalid board).
- **405 Method Not Allowed**: Wrong HTTP method for an endpoint.
- **500 Internal Server Error**: Unexpected server failure (never return 500 for validation errors).

### Response Format Rules

- Always return JSON from API endpoints.
- Include an `error` field only when an error occurs.
- Do not expose stack traces, file paths, internal exception names, or implementation details in error messages.
- Keep error messages concise and actionable from a user perspective.

---

## 6. Error Handling Requirements

### Input Validation

Every route must validate inputs before processing:

**`GET /new?clues=<int>`**
- Clues parameter must be present, numeric, finite, and within a valid range (e.g., 1–81).
- Return `400` with an `error` field if invalid.

**`POST /check`**
- JSON body must be valid and contain a `board` field.
- Board must be a list of 9 rows, each containing 9 integers in range 0–9.
- Solution must exist (check CURRENT['solution'] is not None).
- Return `400` with a descriptive error if validation fails.

### Common Error Scenarios

Handle these cases with appropriate responses:

- No active game: `{"error": "No game in progress"}` with status `400`.
- Invalid JSON: `{"error": "Invalid JSON"}` with status `400`.
- Wrong board dimensions: `{"error": "Board must be 9x9"}` with status `400`.
- Invalid cell value: `{"error": "Cell values must be 0-9"}` with status `400`.
- Invalid clue count: `{"error": "Clues must be between 1 and 81"}` with status `400`.
- Unexpected server error: `{"error": "Internal server error"}` with status `500`.

### Failure Handling in Domain Logic

If puzzle generation fails (e.g., backtracking exhausts possibilities):

- Log the failure server-side with diagnostic context.
- Return `500` with a generic message to the client.
- Do not retry automatically; let the user start a new game.

### Logging Best Practices

- Log unexpected errors with timestamps and context (route, input summary).
- Log puzzle generation failures with the requested clue count and seed (if available).
- Do not log complete boards or solutions.
- Do not log users' submitted answers or solutions.
- Errors go to stderr or a log file; info/debug messages may go to stdout.

### User Experience

- Frontend must handle network errors, timeouts, and non-200 status codes.
- Display user-friendly error messages; never show raw JSON error text.
- Keep the UI interactive even after an error (buttons remain clickable).

---

## 7. Security Requirements

### Input Validation

- All external inputs (query parameters, JSON bodies, headers) must be validated before use.
- Enforce strict allow-lists: clues between 1 and 81, board must be 9×9, cells must be 0–9.
- Reject requests with oversized payloads (e.g., boards larger than 9×9).
- Never trust client-provided solutions; always compare against server-stored state.

### Configuration and Secrets

- No secrets, API keys, passwords, or credentials in version control or code.
- Debug mode must be disabled in any non-local environment.
- Use environment variables for production configuration (host, port, debug flag).
- Keep default configuration in code only if it is safe and sensible for development.

### Error Response Safety

- Never expose stack traces, exception types, file paths, or implementation details in HTTP responses.
- Return generic error messages to clients ("Invalid input") while logging diagnostic details server-side.
- Log enough context to diagnose issues (requested clue count, board dimensions) without logging complete boards or user input.

### Development Practices

- Do not commit `.venv/`, `__pycache__/`, or other build artifacts.
- Use `.gitignore` to prevent accidental secret commits.
- Code reviews must verify that no hardcoded secrets, debug flags, or unsafe defaults were introduced.

### Future Enhancements

If the application grows to support multiple players or persistent state:

- Implement session management with secure cookie settings.
- Add CSRF protection for state-changing requests.
- Use a database with parameterized queries to prevent injection attacks.
- Never accept unvalidated user-supplied SQL, commands, or paths.

---

## 8. Testing Strategy

### Unit Tests (test_sudoku_logic.py)

Test puzzle generation and validation in isolation:

- **Board creation**: Verify `create_empty_board()` returns a 9×9 grid of zeros.
- **Copying**: Verify `deep_copy()` creates independent board copies.
- **Placement validation**: Verify `is_safe()` correctly checks row, column, and 3×3 box constraints.
- **Board filling**: Verify `fill_board()` produces valid, complete grids or returns False on failure.
- **Clue removal**: Verify `remove_cells()` removes exactly the requested number of clues (when valid).
- **Puzzle generation**: Verify the generated puzzle has exactly the requested clues and the solution is valid.
- **Edge cases**: Test boundary clue counts (1, 81), already-full boards, and backtracking failure scenarios.

Use mocking or seeded randomness to ensure tests are deterministic and fast.

### Integration Tests (test_app.py)

Test Flask routes and API contracts:

- **Index route**: Verify `GET /` returns HTML with status 200.
- **New game—default**: Verify `GET /new` returns a 9×9 board with 35 clues.
- **New game—custom clues**: Verify `GET /new?clues=10` respects the parameter.
- **New game—invalid input**: Test missing clues, non-integer clues, out-of-range clues; verify 400 status.
- **Check solution—correct**: Verify a correct board returns `{"incorrect": []}` with status 200.
- **Check solution—incorrect**: Verify an empty board lists all non-clue cells as incorrect.
- **Check solution—no game**: Verify checking without an active game returns error with status 400.
- **Check solution—invalid input**: Test malformed JSON, missing board, wrong dimensions, invalid values.

Reset game state between tests to ensure isolation.

### Test Requirements

- Use Python's built-in `unittest` module.
- Keep tests deterministic: use `unittest.mock.patch` to control randomness or side effects.
- Aim for meaningful coverage (critical paths, error conditions, invariants) rather than arbitrary coverage metrics.
- Run all tests before committing: `python -m unittest discover -s tests -p "test_*.py" -v`.
- Update tests when API contracts change; do not weaken tests to pass failing code.

### Browser Testing

When JavaScript changes significantly:

- Manually verify that the board renders correctly on page load.
- Verify that new-game and check-solution buttons work end-to-end.
- Verify that prefilled cells are disabled and incorrect cells are highlighted.
- Verify that error messages display appropriately (network failure, no game in progress).

---

## 9. Frontend Standards

### HTML (index.html)

- Use semantic HTML5 elements (`<main>`, `<button>`, `<input>`).
- Provide clear, descriptive labels and accessible element attributes.
- Avoid inline styles; use CSS classes instead.
- Keep JavaScript separate from markup; use event listeners instead of inline handlers.
- Ensure the page is readable and functional with CSS disabled (progressive enhancement).

### CSS (styles.css)

- Organize rules by component or section with clear comments.
- Use consistent, meaningful class names (e.g., `sudoku-cell`, `prefilled`, `incorrect`).
- Avoid duplicate styling rules; extract shared styles into base classes.
- Use visual hierarchy (colors, typography, spacing) to guide users.
- Test layout on narrow screens; ensure controls remain accessible.

### JavaScript (main.js)

- Keep presentation logic (DOM manipulation) separate from game state.
- Validate user input on the client where helpful (input masking), but always validate on the server.
- Handle API errors gracefully: show user-friendly messages, log issues, keep the UI interactive.
- Use fetch for API calls; handle network failures and non-JSON responses.
- Do not implement puzzle generation or validation in JavaScript; all logic resides in Python.
- Avoid global variables; scope state appropriately.

### Error Handling in Frontend

- Catch fetch errors (network, timeout, CORS) and display a user-friendly message.
- Validate server responses: check status code, parse JSON safely, verify expected fields.
- If an error occurs during check or new-game, leave the board interactive so users can retry.
- Display error messages with a color and clear text (e.g., red text, "Something went wrong").

---

## 10. Change Management and Development Workflow

### Before Starting Work

1. Understand the existing behavior by reading the code and running tests.
2. If changing an API contract or fixing a bug, add or update a test first to document the expected behavior.
3. Identify what could break: dependent tests, related features, frontend code.

### During Implementation

1. Keep changes focused and small. Avoid refactoring unrelated code in the same pull request.
2. Update comments and docstrings if behavior changes.
3. Add logging or diagnostic output for complex operations.
4. Run tests frequently: `python -m unittest discover -s tests -p "test_*.py" -v`.
5. Manually test the user-facing workflow (new game, check solution, error scenarios).

### Before Completion

1. Verify all tests pass.
2. Check that new code follows PEP 8 and project conventions.
3. Ensure no hardcoded secrets, debug flags, or unsafe defaults were introduced.
4. Update this file (`instructions.md`) if you change architecture, add requirements, or alter key processes.
5. Verify the application still runs: `python app.py` and `http://127.0.0.1:5000/`.

### Backwards Compatibility

- Preserve existing API contracts unless explicitly versioning or deprecating an endpoint.
- If removing or changing endpoint behavior, update tests and frontend code together.
- Document breaking changes in this file and provide migration guidance.

---

## 11. Definition of Done

A change, feature, or bug fix is ready for completion only when ALL of the following are true:

### Code Quality
- [ ] Code follows PEP 8 and project naming conventions.
- [ ] No unnecessary complexity; logic is clear and maintainable.
- [ ] Puzzle generation and validation logic remains independent of HTTP handling.

### Documentation
- [ ] Module, function, and class docstrings are clear and accurate.
- [ ] Complex logic has inline comments explaining *why*, not just *what*.
- [ ] API request/response formats are documented near the route.
- [ ] Configuration, defaults, and business rules are explicitly defined.

### Testing
- [ ] All existing tests pass: `python -m unittest discover -s tests -p "test_*.py" -v`.
- [ ] New or changed behavior is covered by added or updated tests.
- [ ] Tests are deterministic and isolated (no random failures, no global state pollution).
- [ ] Error cases and boundary conditions are tested.

### Error Handling
- [ ] All external inputs are validated with appropriate error responses.
- [ ] Route handlers return correct HTTP status codes (200, 400, 500).
- [ ] Error messages are user-friendly and do not expose stack traces or implementation details.
- [ ] Failures are handled gracefully; the application does not crash or hang.

### Security
- [ ] No hardcoded secrets, API keys, passwords, or debug flags.
- [ ] Client-provided data is never trusted; server always validates and verifies.
- [ ] Configuration uses environment variables for production settings.

### Frontend
- [ ] Changes integrate cleanly with the existing API and JavaScript.
- [ ] Frontend handles network failures and invalid responses.
- [ ] The page remains interactive even after errors.
- [ ] Layout works on narrow and wide screens.
- [ ] No inline scripts or styles (all in separate files).

### Verification
- [ ] Manual smoke test: load the page, start a game, and check a board.
- [ ] No errors in the Flask debug console or browser console.
- [ ] No unintended side effects or behavior changes.

### Documentation
- [ ] This file (`instructions.md`) is updated if architecture, processes, or requirements changed.
- [ ] Commit messages clearly describe *what* changed and *why*.
