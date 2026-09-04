// Shared frontend constants for the Sudoku application.
(function (modules) {
  modules.SIZE = 9;
  modules.THEME_KEY = 'sudoku-theme';
  modules.SCORES_KEY = 'sudoku-top10';
  modules.TOP10_LIMIT = 10;
  modules.CLUES = {easy: 50, medium: 40, hard: 30};
})(window.SudokuModules = window.SudokuModules || {});