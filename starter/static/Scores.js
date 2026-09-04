// Top-10 score persistence, rendering, and name collection.
(function (modules) {
  class Scores {
    constructor(body, dialog) { this.body = body; this.dialog = dialog; }
    load() {
      const entries = modules.readStorage(modules.SCORES_KEY, []);
      return Array.isArray(entries) ? entries : [];
    }
    render(entries) {
      this.body.replaceChildren();
      entries.forEach((entry, index) => {
        const row = document.createElement('tr');
        [index + 1, entry.name, entry.score, modules.formatTime(entry.time_taken), entry.hints_used, entry.difficulty]
          .forEach((value) => { const cell = document.createElement('td'); cell.textContent = value; row.appendChild(cell); });
        this.body.appendChild(row);
      });
    }
    async add(entry) {
      const entries = this.load();
      if (entries.length >= modules.TOP10_LIMIT && entry.score <= entries[entries.length - 1].score) return;
      const name = await this.name();
      if (name === null) return;
      entries.push({...entry, name});
      entries.sort((first, second) => second.score - first.score);
      const top10 = entries.slice(0, modules.TOP10_LIMIT);
      modules.writeStorage(modules.SCORES_KEY, top10);
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
  }

  modules.Scores = Scores;
})(window.SudokuModules = window.SudokuModules || {});