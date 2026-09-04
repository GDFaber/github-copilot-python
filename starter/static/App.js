// Application coordinator for the Sudoku frontend.
(function (modules) {
  class App {
    constructor() {
      this.api = new modules.Api();
      this.board = new modules.Board(document.getElementById('sudoku-board'), document.getElementById('message'));
      this.clock = new modules.Clock(document.getElementById('timer'));
      this.scores = new modules.Scores(document.getElementById('top10-entries'), document.getElementById('top10-name-dialog'));
      this.newButton = document.getElementById('new-game');
      this.checkButton = document.getElementById('check-solution');
      this.hintButton = document.getElementById('hint-button');
    }
    initialize() {
      this.setupTheme();
      this.newButton.addEventListener('click', () => this.newGame());
      this.checkButton.addEventListener('click', () => this.check());
      this.hintButton.addEventListener('click', () => this.hint());
      this.board.render(Array.from({length: modules.SIZE}, () => Array(modules.SIZE).fill(0)));
      this.scores.render(this.scores.load());
    }
    async newGame() {
      this.setBusy(true);
      this.board.clearFeedback();
      let started = false;
      try {
        const difficulty = document.getElementById('difficulty-select').value;
        const data = await this.api.newGame(modules.CLUES[difficulty]);
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
        const input = this.board.inputs()[data.row * modules.SIZE + data.col];
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
        const incorrect = new Set(data.incorrect.map(([row, column]) => row * modules.SIZE + column));
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
      try { saved = localStorage.getItem(modules.THEME_KEY) || 'system'; } catch (_error) { /* Use system theme. */ }
      select.value = ['light', 'dark', 'system'].includes(saved) ? saved : 'system';
      this.applyTheme(select.value);
      select.addEventListener('change', (event) => this.applyTheme(event.target.value));
    }
    applyTheme(theme) {
      const selected = ['light', 'dark', 'system'].includes(theme) ? theme : 'system';
      if (selected === 'system') delete document.documentElement.dataset.theme;
      else document.documentElement.dataset.theme = selected;
      try { localStorage.setItem(modules.THEME_KEY, selected); } catch (_error) { /* Current page remains themed. */ }
    }
  }

  modules.App = App;
})(window.SudokuModules = window.SudokuModules || {});