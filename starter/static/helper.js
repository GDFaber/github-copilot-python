// Reusable browser helpers shared by frontend components.
(function (modules) {
  modules.formatTime = function (seconds) {
    return `${Math.floor(seconds / 60).toString().padStart(2, '0')}:${(seconds % 60).toString().padStart(2, '0')}`;
  };

  modules.readStorage = function (key, fallback) {
    try {
      const value = JSON.parse(localStorage.getItem(key) || JSON.stringify(fallback));
      return value;
    } catch (_error) {
      return fallback;
    }
  };

  modules.writeStorage = function (key, value) {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch (_error) {
      // Browser storage may be unavailable in private browsing contexts.
    }
  };
})(window.SudokuModules = window.SudokuModules || {});