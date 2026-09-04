// HTTP client for the Flask Sudoku API.
(function (modules) {
  class Api {
    async request(url, options = {}) {
      let response;
      try {
        response = await fetch(url, options);
      } catch (_error) {
        throw new Error('Unable to connect to the game server.');
      }
      let data;
      try {
        data = await response.json();
      } catch (_error) {
        throw new Error('The server returned an invalid response.');
      }
      if (!response.ok || data.error) throw new Error(this.message(data.error, response.status));
      return data;
    }

    message(serverMessage, status) {
      const known = {
        'No game in progress': 'Start a new game before using this control.',
        'No empty cells remaining': 'There are no empty cells left for a hint.',
        'Board must be 9x9': 'The board is incomplete. Fill every cell before checking.',
        'Cell values must be 0-9': 'The board contains an invalid cell value.',
      };
      return known[serverMessage]
        || (status >= 500 ? 'The game server encountered an error.' : 'Please check your input and try again.');
    }

    newGame(clues) { return this.request(`/new?clues=${encodeURIComponent(clues)}`); }
    hint() { return this.request('/hint', {method: 'POST'}); }
    check(board, timeTaken) {
      return this.request('/check', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({board, time_taken: timeTaken}),
      });
    }
  }

  modules.Api = Api;
})(window.SudokuModules = window.SudokuModules || {});