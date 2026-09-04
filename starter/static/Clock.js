// Elapsed-game timer.
(function (modules) {
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
    render() { this.element.textContent = `Time: ${modules.formatTime(this.elapsed())}`; }
  }

  modules.Clock = Clock;
})(window.SudokuModules = window.SudokuModules || {});