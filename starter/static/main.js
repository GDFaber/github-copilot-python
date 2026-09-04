// Frontend bootstrap entry point.
(function (modules) {
  window.addEventListener('DOMContentLoaded', () => new modules.App().initialize());
})(window.SudokuModules = window.SudokuModules || {});