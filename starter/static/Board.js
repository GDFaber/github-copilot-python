// Sudoku board rendering, input handling, and conflict feedback.
(function (modules) {
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
      return Array.from({length: modules.SIZE}, (_, row) => Array.from({length: modules.SIZE}, (_, column) => {
        const value = inputs[row * modules.SIZE + column].value;
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

  modules.Board = Board;
})(window.SudokuModules = window.SudokuModules || {});