// Modular browser client for the Flask-backed Sudoku game.
const SudokuApp = (() => {
  const SIZE = 9;
  const THEME_KEY = 'sudoku-theme';
  const SCORES_KEY = 'sudoku-top10';
  const CLUES = {easy: 50, medium: 40, hard: 30};

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

  class Clock {
    constructor(element) { this.element = element; this.startedAt = 0; this.interval = null; }
    start() {
      this.stop();
      this.startedAt = Date.now();
      this.render();
      this.interval = setInterval(() => this.render(), 1000);
    }
    stop() { if (this.interval !== null) clearInterval(this.interval); this.interval = null; }
    elapsed() { return this.startedAt ? Math.floor((Date.now() - this.startedAt) / 1000) : 0; }
    render() { this.element.textContent = `Time: ${this.format(this.elapsed())}`; }
    format(seconds) {
      return `${Math.floor(seconds / 60).toString().padStart(2, '0')}:${(seconds % 60).toString().padStart(2, '0')}`;
    }
  }

  class Board {
    constructor(element, message) { this.element = element; this.message = message; }
    inputs() { return [...this.element.querySelectorAll('.sudoku-cell')]; }
    render(puzzle) {
      this.element.replaceChildren();
      puzzle.forEach((row, rowIndex) => {
        const rowElement = document.createElement('div');
        rowElement.className = 'sudoku-row';
        rowElement.setAttribute('role', 'row');
        row.forEach((value, columnIndex) => {
          const input = document.createElement('input');
          input.type = 'text';
          input.inputMode = 'numeric';
          input.maxLength = 1;
          input.className = 'sudoku-cell';
          input.dataset.row = rowIndex;
          input.dataset.col = columnIndex;
          input.setAttribute('aria-label', `Row ${rowIndex + 1}, column ${columnIndex + 1}`);
          input.addEventListener('input', (event) => this.onInput(event));
          if (value !== 0) {
            input.value = value;
            input.disabled = true;
            input.classList.add('prefilled');
          }
          rowElement.appendChild(input);
        });
        this.element.appendChild(rowElement);
      });
    }
    values() {
      const inputs = this.inputs();
      return Array.from({length: SIZE}, (_, row) => Array.from({length: SIZE}, (_, column) => {
        const value = inputs[row * SIZE + column].value;
        return value ? Number.parseInt(value, 10) : 0;
      }));
    }
    clearFeedback() {
      this.inputs().forEach((input) => { input.classList.remove('conflicting'); input.removeAttribute('title'); });
      this.clearMessage();
    }
    clearMessage() { this.message.textContent = ''; this.message.className = ''; }
    showMessage(text, type = 'error') { this.message.textContent = text; this.message.className = type; }
    onInput(event) {
      const input = event.target;
      const raw = input.value;
      const value = raw.replace(/[^1-9]/g, '').slice(0, 1);
      input.value = value;
      input.classList.remove('incorrect', 'player-filled');
      const conflicts = this.findConflicts();
      if (raw !== value) this.showMessage('Enter a single digit from 1 to 9.');
      else if (conflicts.has(input)) this.showMessage(this.describe(conflicts.get(input)));
      else this.clearMessage();
    }
    findConflicts() {
      const inputs = this.inputs();
      const conflicts = new Map();
      inputs.forEach((input) => { input.classList.remove('conflicting'); input.removeAttribute('title'); });
      inputs.forEach((input) => {
        if (!input.value) return;
        const row = Number(input.dataset.row);
        const column = Number(input.dataset.col);
        inputs.forEach((other) => {
          if (input === other || input.value !== other.value) return;
          const otherRow = Number(other.dataset.row);
          const otherColumn = Number(other.dataset.col);
          const sameRow = row === otherRow;
          const sameColumn = column === otherColumn;
          const sameBox = Math.floor(row / 3) === Math.floor(otherRow / 3)
            && Math.floor(column / 3) === Math.floor(otherColumn / 3);
          if (sameRow || sameColumn || sameBox) {
            const types = conflicts.get(input) || new Set();
            if (sameRow) types.add('row');
            if (sameColumn) types.add('column');
            if (sameBox) types.add('3x3 box');
            conflicts.set(input, types);
            conflicts.set(other, conflicts.get(other) || new Set());
          }
        });
      });
      conflicts.forEach((types, input) => { input.classList.add('conflicting'); input.title = this.describe(types); });
      return conflicts;
    }
    describe(types) { return `Conflicts with the same number in the ${[...types].join(' and ')}.`; }
  }

  class Scores {
    constructor(body, dialog) { this.body = body; this.dialog = dialog; }
    load() { try { const data = JSON.parse(localStorage.getItem(SCORES_KEY) || '[]'); return Array.isArray(data) ? data : []; } catch (_error) { return []; } }
    render(entries) {
      this.body.replaceChildren();
      entries.forEach((entry, index) => {
        const row = document.createElement('tr');
        [index + 1, entry.name, entry.score, this.time(entry.time_taken), entry.hints_used, entry.difficulty]
          .forEach((value) => { const cell = document.createElement('td'); cell.textContent = value; row.appendChild(cell); });
        this.body.appendChild(row);
      });
    }
    async add(entry) {
      const entries = this.load();
      if (entries.length >= 10 && entry.score <= entries[entries.length - 1].score) return;
      const name = await this.name();
      if (name === null) return;
      entries.push({...entry, name});
      entries.sort((first, second) => second.score - first.score);
      const top10 = entries.slice(0, 10);
      try { localStorage.setItem(SCORES_KEY, JSON.stringify(top10)); } catch (_error) { /* UI still works. */ }
      this.render(top10);
    }
    name() {
      const form = document.getElementById('top10-name-form');
      const input = document.getElementById('top10-name-input');
      const cancel = document.getElementById('top10-name-cancel');
      input.value = '';
      return new Promise((resolve) => {
        const close = (value) => { this.dialog.close(); form.removeEventListener('submit', submit); cancel.removeEventListener('click', abort); resolve(value); };
        const submit = (event) => { event.preventDefault(); if (form.reportValidity()) close(input.value.trim()); };
        const abort = () => close(null);
        form.addEventListener('submit', submit); cancel.addEventListener('click', abort); this.dialog.showModal(); input.focus();
      });
    }
    time(seconds) { return `${Math.floor(seconds / 60).toString().padStart(2, '0')}:${(seconds % 60).toString().padStart(2, '0')}`; }
  }

  class App {
    constructor() {
      this.api = new Api();
      this.board = new Board(document.getElementById('sudoku-board'), document.getElementById('message'));
      this.clock = new Clock(document.getElementById('timer'));
      this.scores = new Scores(document.getElementById('top10-entries'), document.getElementById('top10-name-dialog'));
      this.newButton = document.getElementById('new-game');
      this.checkButton = document.getElementById('check-solution');
      this.hintButton = document.getElementById('hint-button');
    }
    initialize() {
      this.setupTheme();
      this.newButton.addEventListener('click', () => this.newGame());
      this.checkButton.addEventListener('click', () => this.check());
      this.hintButton.addEventListener('click', () => this.hint());
      this.board.render(Array.from({length: SIZE}, () => Array(SIZE).fill(0)));
      this.scores.render(this.scores.load());
    }
    async newGame() {
      this.setBusy(true);
      this.board.clearFeedback();
      let started = false;
      try {
        const difficulty = document.getElementById('difficulty-select').value;
        const data = await this.api.newGame(CLUES[difficulty]);
        this.board.render(data.puzzle);
        this.clock.start();
        started = true;
        document.getElementById('hint-count').textContent = 'Hints used: 0';
        this.board.clearMessage();
      } catch (error) { this.board.showMessage(error.message); }
      finally { this.setBusy(false); this.checkButton.disabled = !started; this.hintButton.disabled = !started; }
    }
    async hint() {
      this.hintButton.disabled = true;
      try {
        const data = await this.api.hint();
        const input = this.board.inputs()[data.row * SIZE + data.col];
        input.value = data.value; input.disabled = true; input.className = 'sudoku-cell hinted';
        this.board.findConflicts();
        document.getElementById('hint-count').textContent = `Hints used: ${data.hint_count}`;
        this.hintButton.disabled = !this.board.inputs().some((cell) => !cell.disabled);
      } catch (error) { this.board.showMessage(error.message); }
    }
    async check() {
      this.board.clearFeedback();
      try {
        const data = await this.api.check(this.board.values(), this.clock.elapsed());
        const incorrect = new Set(data.incorrect.map(([row, column]) => row * SIZE + column));
        this.board.inputs().forEach((input, index) => {
          if (input.disabled) return;
          input.className = input.value ? 'sudoku-cell player-filled' : 'sudoku-cell';
          if (incorrect.has(index)) input.className = 'sudoku-cell incorrect';
        });
        if (incorrect.size === 0) {
          this.clock.stop(); this.checkButton.disabled = true; this.hintButton.disabled = true;
          this.board.showMessage(`Congratulations! You solved it! Score: ${data.score}`, 'success');
          await this.scores.add(data.entry);
        } else this.board.showMessage('Some cells are incorrect.');
      } catch (error) { this.board.showMessage(error.message); }
    }
    setBusy(busy) { this.newButton.disabled = busy; this.checkButton.disabled = busy; this.hintButton.disabled = busy; }
    setupTheme() {
      const select = document.getElementById('theme-select');
      let saved = 'system';
      try { saved = localStorage.getItem(THEME_KEY) || 'system'; } catch (_error) { /* Use system theme. */ }
      select.value = ['light', 'dark', 'system'].includes(saved) ? saved : 'system';
      this.applyTheme(select.value);
      select.addEventListener('change', (event) => this.applyTheme(event.target.value));
    }
    applyTheme(theme) {
      const selected = ['light', 'dark', 'system'].includes(theme) ? theme : 'system';
      if (selected === 'system') delete document.documentElement.dataset.theme;
      else document.documentElement.dataset.theme = selected;
      try { localStorage.setItem(THEME_KEY, selected); } catch (_error) { /* Current page remains themed. */ }
    }
  }

  return {initialize: () => new App().initialize()};
})();

window.addEventListener('DOMContentLoaded', () => SudokuApp.initialize());
