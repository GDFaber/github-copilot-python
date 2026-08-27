# Sudoku App Project Instructions

## Purpose

These instructions define how to set up, extend, test, review, and operate this Sudoku application. The project is a small Flask application with a browser client and pure-Python Sudoku logic. Keep changes focused, understandable, and consistent with the existing stack.

## Setup

1. Use Python 3.10 or newer and create an isolated virtual environment.
2. Install dependencies from `requirements.txt`:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   py -m pip install --upgrade pip
   py -m pip install -r requirements.txt
   ```

3. Run the test suite from the project root:

   ```powershell
   py -m unittest discover -s tests -p "test_*.py" -v
   ```

4. Start the development server locally:

   ```powershell
   py app.py
   ```

   Open `http://127.0.0.1:5000/` in a browser.

Do not use Flask debug mode in a deployed environment. Pin or regularly review dependencies before a release, and document any new dependency in `requirements.txt`.

## Project Structure

- `app.py`: Flask application, HTTP routes, request validation, response formatting, and game-session coordination.
- `sudoku_logic.py`: Sudoku board representation, validation helpers, solving/generation algorithms, and puzzle creation.
- `templates/index.html`: Accessible page structure and controls.
- `static/main.js`: Browser rendering, input handling, API calls, and user-facing status updates.
- `static/styles.css`: Presentation and responsive layout.
- `tests/test_app.py`: Flask route and API contract tests.
- `tests/test_sudoku_logic.py`: Unit tests for board and generation behavior.
- `requirements.txt`: Runtime dependencies.

Keep domain logic out of route functions and keep browser-only behavior out of Python modules. Preserve the existing JSON API unless a deliberate versioned change is required.

## Architecture Rules

- Treat `SIZE` and `EMPTY` in `sudoku_logic.py` as the source of truth for board dimensions and empty cells.
- Keep board operations deterministic in their contracts even when generation uses randomness. A generated puzzle must have a valid complete solution and exactly the requested number of clues when the request is valid.
- Keep puzzle and solution copies independent. Never expose the server's stored solution in a normal response.
- Route handlers should orchestrate validation, domain calls, state updates, and serialization; they should not implement solving or generation algorithms.
- The current in-memory state is suitable only for a single-process demonstration. For multi-user or multi-worker deployment, introduce a session or database-backed state store and define ownership, expiration, and concurrency behavior before enabling it.
- Prefer small, single-purpose functions with explicit inputs and outputs. Avoid hidden global mutation except behind a clearly defined state abstraction.
- Keep frontend and backend contracts documented through tests. Changes to field names, status codes, or board shape require updates to both sides and their tests.

## Error Handling

- Validate every external input before indexing, iterating, converting, or passing it to domain logic.
- `/new` must reject missing, non-integer, non-finite, or out-of-range `clues` values with a controlled `4xx` JSON response. Define and test the supported range; do not allow negative values or more clues than the board contains.
- `/check` must reject missing JSON, non-object JSON, missing `board`, non-list boards, incorrect dimensions, and cells that are not integers in the permitted range. Return a consistent JSON error shape and an appropriate `4xx` status.
- Never allow malformed input to produce an uncaught `IndexError`, `TypeError`, `ValueError`, or server traceback in the HTTP response.
- Handle generation failures and unexpected internal failures with controlled responses. Log diagnostic details server-side without exposing stack traces, secrets, filesystem paths, or implementation details to clients.
- Use clear status codes: successful requests return `2xx`, client validation or missing-game errors return `4xx`, and unexpected server failures return `5xx`.
- Frontend requests must handle network failures, non-OK responses, invalid JSON, and missing response fields. Show a useful, non-sensitive message and leave the UI in a usable state.
- Do not silently accept invalid or partial boards. A check operation must have a well-defined result for every valid board.

## Quality and Testing

Every behavior change must include or update focused tests before it is considered complete.

- Test valid default and boundary clue counts, invalid clue input, and generation invariants.
- Test valid solution checks, incorrect cells, no active game, malformed JSON, malformed board shapes, invalid cell values, and unexpected request types.
- Test that fixed puzzle clues cannot be changed through the check API if that is part of the product rule.
- Test Sudoku invariants: dimensions, values, row uniqueness, column uniqueness, 3x3-box uniqueness, and solution independence from the puzzle.
- Use mocks or seeded randomness for algorithm edge cases so tests remain fast and repeatable.
- Keep tests isolated: reset application state between tests or replace global state with an injectable store.
- Run the full test command after changes to shared logic or routes. Run a focused test while iterating, then run the full suite before completion.
- Add browser-level coverage when changing JavaScript workflows, accessibility behavior, or API integration.
- Do not weaken assertions merely to make a failing test pass. Fix the implementation or update the contract explicitly.

## Security Requirements

- Treat all query parameters, JSON bodies, headers, and browser values as untrusted.
- Use strict allow-list validation for clue counts, board dimensions, and cell values. Enforce reasonable request-size limits.
- Keep debug mode disabled outside local development. Do not return exception details to clients.
- Do not trust client-side validation; repeat all validation on the server.
- Never accept a client-provided solution as authoritative. Compare against server-controlled state only after validating the submitted board.
- Avoid logging submitted boards or other data unless needed for diagnosis, and never log credentials, tokens, or secrets.
- Configure secure headers, appropriate cookie settings, and CSRF protection if state-changing browser requests, authentication, or cookies are introduced.
- Apply rate limiting or equivalent abuse controls before exposing puzzle generation or checking endpoints publicly.
- Keep dependencies current and review security advisories before deployment.
- Bind development services to localhost by default. Use a production WSGI server and a reverse proxy or managed platform for deployment.

## Maintainability and Code Commentary

- Follow PEP 8 and use descriptive names; avoid one-letter names except for tightly scoped mathematical or coordinate loops where the meaning is obvious.
- Add type hints to new Python functions and use docstrings for public modules or functions whose behavior is not obvious.
- Comments should explain why a non-obvious algorithmic choice, invariant, validation rule, or state transition exists. Do not add comments that merely repeat the code.
- Keep comments and docstrings accurate when behavior changes. Remove stale explanations.
- Prefer standard-library solutions and existing project patterns before adding abstractions or packages.
- Keep patches small and avoid unrelated formatting or refactoring.
- Make API error messages stable enough for the frontend and tests, but do not make clients depend on internal exception text.
- Update this file and relevant tests when architecture, commands, contracts, or operational assumptions change.

## Operational Requirements

- Provide a health or readiness signal before production deployment if the application is run as a service.
- Use structured application logging with timestamps and severity levels. Include request outcome and duration where practical, while excluding sensitive payloads.
- Set explicit production configuration for host, port, debug state, secret keys, proxy behavior, and resource limits through environment variables or the deployment platform.
- Use a process manager or production WSGI server, define restart behavior, and document the deployment command.
- Define the consequences of process restarts: the current in-memory implementation loses all active games.
- Monitor error rates, latency, resource use, and generation failures. Alert on sustained failures rather than individual expected client errors.
- Keep deployment artifacts minimal and exclude virtual environments, caches, test output, and secrets from version control.
- Document rollback steps and verify that a deployed version can serve `/` and successfully complete `/new` and `/check` smoke tests.

## Definition Of Done

A change is done only when all applicable items are true:

- The behavior and API contract are clear and documented near the owning code or in this file.
- External inputs are validated, expected failures return controlled responses, and unexpected failures are safely handled and logged.
- The implementation preserves puzzle correctness, state isolation, and existing supported behavior.
- Relevant unit, route, integration, and browser tests are added or updated.
- `py -m unittest discover -s tests -p "test_*.py" -v` passes from the project root.
- New or changed Python files have no reported type, syntax, or lint errors under the project's configured tools.
- Frontend changes work with the current API, handle failure states, remain usable on narrow screens, and preserve accessible labels, focus behavior, and keyboard operation.
- No secrets, debug configuration, unsafe error details, unnecessary dependencies, or unrelated changes were introduced.
- Documentation, dependency declarations, and operational notes match the delivered behavior.
- A local smoke test covers loading `/`, starting a new game, and checking a valid board when the change affects the web workflow.
