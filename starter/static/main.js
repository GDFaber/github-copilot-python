// Client-side rendering and interaction for the Flask-backed Sudoku
const SIZE = 9;
const THEME_STORAGE_KEY = 'sudoku-theme';
const TOP10_STORAGE_KEY = 'sudoku-top10';
const TOP10_LIMIT = 10;
const CLUES_BY_DIFFICULTY = {
  easy: 50,
  medium: 40,
  hard: 30
};
let puzzle = [];
let timerInterval = null;
let timerStart = 0;

function formatTime(totalSeconds) {
  const minutes = Math.floor(totalSeconds / 60).toString().padStart(2, '0');
  const seconds = (totalSeconds % 60).toString().padStart(2, '0');
  return `${minutes}:${seconds}`;
}

function updateTimer() {
  const elapsedSeconds = Math.floor((Date.now() - timerStart) / 1000);
  document.getElementById('timer').innerText = `Time: ${formatTime(elapsedSeconds)}`;
}

function startTimer() {
  if (timerInterval !== null) clearInterval(timerInterval);
  timerStart = Date.now();
  updateTimer();
  timerInterval = setInterval(updateTimer, 1000);
}

function stopTimer() {
  if (timerInterval !== null) {
    clearInterval(timerInterval);
    timerInterval = null;
    updateTimer();
  }
}

function renderTop10(entries) {
  const tableBody = document.getElementById('top10-entries');
  tableBody.innerHTML = '';
  const medals = ['\u{1F947}', '\u{1F948}', '\u{1F949}'];

  for (const [index, entry] of entries.entries()) {
    const row = document.createElement('tr');
    const values = [
      `${index + 1} ${medals[index] || ''}`.trim(),
      entry.name,
      entry.score,
      formatTime(entry.time_taken),
      entry.hints_used,
      entry.difficulty
    ];
    for (const value of values) {
      const cell = document.createElement('td');
      cell.textContent = value;
      row.appendChild(cell);
    }
    tableBody.appendChild(row);
  }
}

function loadTop10() {
  try {
    const entries = JSON.parse(localStorage.getItem(TOP10_STORAGE_KEY) || '[]');
    return Array.isArray(entries) ? entries : [];
  } catch (_error) {
    return [];
  }
}

function saveTop10(entries) {
  localStorage.setItem(TOP10_STORAGE_KEY, JSON.stringify(entries));
}

function requestPlayerName() {
  const dialog = document.getElementById('top10-name-dialog');
  const form = document.getElementById('top10-name-form');
  const input = document.getElementById('top10-name-input');
  const cancelButton = document.getElementById('top10-name-cancel');
  input.value = '';

  return new Promise((resolve) => {
    const closeDialog = (name) => {
      dialog.close();
      form.removeEventListener('submit', submitName);
      cancelButton.removeEventListener('click', cancelEntry);
      resolve(name);
    };
    const submitName = (event) => {
      event.preventDefault();
      if (form.reportValidity()) closeDialog(input.value.trim());
    };
    const cancelEntry = () => closeDialog(null);

    form.addEventListener('submit', submitName);
    cancelButton.addEventListener('click', cancelEntry);
    dialog.showModal();
    input.focus();
  });
}

async function submitTop10Entry(entry) {
  const entries = loadTop10();
  const qualifies = entries.length < TOP10_LIMIT || entry.score > entries[entries.length - 1].score;
  if (!qualifies) return;

  const name = await requestPlayerName();
  if (name === null) return;

  entries.push({...entry, name});
  entries.sort((first, second) => second.score - first.score);
  const top10 = entries.slice(0, TOP10_LIMIT);
  saveTop10(top10);
  renderTop10(top10);
}

function getBoardInputs() {
  return Array.from(document.querySelectorAll('#sudoku-board .sudoku-cell'));
}

function clearMessage() {
  const message = document.getElementById('message');
  message.innerText = '';
  message.style.color = '';
}

function clearInvalidFeedback(inputs = getBoardInputs()) {
  for (const input of inputs) {
    input.classList.remove('conflicting');
    input.removeAttribute('title');
  }
  clearMessage();
}

function conflictDescription(conflictTypes) {
  return `Conflicts with the same number in the ${conflictTypes.join(' and ')}.`;
}

function validateBoardConflicts(inputs) {
  const conflicts = new Map();

  for (const input of inputs) {
    input.classList.remove('conflicting');
    input.removeAttribute('title');
  }

  for (const input of inputs) {
    const value = input.value;
    if (!value) continue;

    const row = Number(input.dataset.row);
    const col = Number(input.dataset.col);
    const conflictTypes = new Set();
    const matchingInputs = [];

    for (const otherInput of inputs) {
      if (input === otherInput || otherInput.value !== value) continue;

      const otherRow = Number(otherInput.dataset.row);
      const otherCol = Number(otherInput.dataset.col);
      if (otherRow === row) conflictTypes.add('row');
      if (otherCol === col) conflictTypes.add('column');
      if (Math.floor(otherRow / 3) === Math.floor(row / 3)
          && Math.floor(otherCol / 3) === Math.floor(col / 3)) {
        conflictTypes.add('3x3 box');
      }
      if (otherRow === row || otherCol === col
          || (Math.floor(otherRow / 3) === Math.floor(row / 3)
              && Math.floor(otherCol / 3) === Math.floor(col / 3))) {
        matchingInputs.push(otherInput);
      }
    }

    if (conflictTypes.size > 0) {
      conflicts.set(input, conflictTypes);
      for (const matchingInput of matchingInputs) {
        if (!conflicts.has(matchingInput)) conflicts.set(matchingInput, new Set());
      }
    }
  }

  for (const [input, conflictTypes] of conflicts) {
    input.classList.add('conflicting');
    input.title = conflictTypes.size > 0
      ? conflictDescription([...conflictTypes])
      : 'Conflicts with another number in this row, column, or 3x3 box.';
  }

  return conflicts;
}

function applyTheme(theme) {
  const selectedTheme = ['light', 'dark', 'system'].includes(theme) ? theme : 'system';
  const root = document.documentElement;

  if (selectedTheme === 'system') {
    delete root.dataset.theme;
  } else {
    root.dataset.theme = selectedTheme;
  }

  localStorage.setItem(THEME_STORAGE_KEY, selectedTheme);
}

function createBoardElement() {
  const boardDiv = document.getElementById('sudoku-board');
  boardDiv.innerHTML = '';
  for (let i = 0; i < SIZE; i++) {
    const rowDiv = document.createElement('div');
    rowDiv.className = 'sudoku-row';
    for (let j = 0; j < SIZE; j++) {
      const input = document.createElement('input');
      input.type = 'text';
      input.maxLength = 1;
      input.className = 'sudoku-cell';
      input.dataset.row = i;
      input.dataset.col = j;
      input.addEventListener('input', (e) => {
        const rawValue = e.target.value;
        const value = rawValue.replace(/[^1-9]/g, '').slice(0, 1);
        e.target.value = value;
        e.target.classList.remove('incorrect');

        const message = document.getElementById('message');
        const conflicts = validateBoardConflicts(getBoardInputs());
        if (rawValue !== value) {
          e.target.title = 'Enter a single digit from 1 to 9.';
          message.style.color = '#d32f2f';
          message.innerText = 'Enter a single digit from 1 to 9.';
          return;
        }

        if (conflicts.has(e.target)) {
          message.style.color = '#d32f2f';
          message.innerText = conflictDescription([...conflicts.get(e.target)]);
        } else {
          clearMessage();
        }
      });
      rowDiv.appendChild(input);
    }
    boardDiv.appendChild(rowDiv);
  }
}

function renderPuzzle(puz) {
  puzzle = puz;
  createBoardElement();
  const boardDiv = document.getElementById('sudoku-board');
  const inputs = boardDiv.getElementsByTagName('input');
  for (let i = 0; i < SIZE; i++) {
    for (let j = 0; j < SIZE; j++) {
      const idx = i * SIZE + j;
      const val = puzzle[i][j];
      const inp = inputs[idx];
      if (val !== 0) {
        inp.value = val;
        inp.disabled = true;
        inp.className += ' prefilled';
      } else {
        inp.value = '';
        inp.disabled = false;
      }
    }
  }
}

async function newGame() {
  startTimer();
  clearInvalidFeedback();
  const difficulty = document.getElementById('difficulty-select').value;
  const clues = CLUES_BY_DIFFICULTY[difficulty];
  const res = await fetch(`/new?clues=${clues}`);
  const data = await res.json();
  renderPuzzle(data.puzzle);
  clearMessage();
  document.getElementById('hint-count').innerText = 'Hints used: 0';
  document.getElementById('hint-button').disabled = false;
  document.getElementById('check-solution').disabled = false;
}

async function requestHint() {
  const res = await fetch('/hint', {method: 'POST'});
  const data = await res.json();
  const msg = document.getElementById('message');
  if (data.error) {
    msg.style.color = '#d32f2f';
    msg.innerText = data.error;
    document.getElementById('hint-button').disabled = true;
    return;
  }
  const boardDiv = document.getElementById('sudoku-board');
  const inputs = boardDiv.getElementsByTagName('input');
  const idx = data.row * SIZE + data.col;
  const inp = inputs[idx];
  const replacesConflictingMove = inp.classList.contains('conflicting');
  inp.value = data.value;
  inp.disabled = true;
  inp.className = 'sudoku-cell hinted';
  if (replacesConflictingMove) {
    const remainingConflicts = validateBoardConflicts(inputs);
    if (remainingConflicts.size === 0) {
      clearMessage();
    } else {
      const [remainingInput, conflictTypes] = remainingConflicts.entries().next().value;
      msg.innerText = conflictTypes.size > 0
        ? conflictDescription([...conflictTypes])
        : remainingInput.title;
    }
  }
  document.getElementById('hint-count').innerText = `Hints used: ${data.hint_count}`;
  const hasEmptyCell = Array.from(inputs).some((cell) => !cell.disabled);
  if (!hasEmptyCell) {
    document.getElementById('hint-button').disabled = true;
  }
}

async function checkSolution() {
  const boardDiv = document.getElementById('sudoku-board');
  const inputs = boardDiv.getElementsByTagName('input');
  clearInvalidFeedback(inputs);
  const board = [];
  for (let i = 0; i < SIZE; i++) {
    board[i] = [];
    for (let j = 0; j < SIZE; j++) {
      const idx = i * SIZE + j;
      const val = inputs[idx].value;
      board[i][j] = val ? parseInt(val, 10) : 0;
    }
  }
  const res = await fetch('/check', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      board,
      time_taken: Math.floor((Date.now() - timerStart) / 1000)
    })
  });
  const data = await res.json();
  const msg = document.getElementById('message');
  if (data.error) {
    msg.style.color = '#d32f2f';
    msg.innerText = data.error;
    return;
  }
  const incorrect = new Set(data.incorrect.map(x => x[0]*SIZE + x[1]));
  for (let idx = 0; idx < inputs.length; idx++) {
    const inp = inputs[idx];
    if (inp.disabled) continue;
    inp.className = 'sudoku-cell';
    if (incorrect.has(idx)) {
      inp.className = 'sudoku-cell incorrect';
    }
  }
  if (incorrect.size === 0) {
    stopTimer();
    document.getElementById('check-solution').disabled = true;
    msg.style.color = '#388e3c';
    msg.innerText = `Congratulations! You solved it! Score: ${data.score}`;
    await submitTop10Entry(data.entry);
  } else {
    msg.style.color = '#d32f2f';
    msg.innerText = 'Some cells are incorrect.';
  }
}

// Wire buttons
window.addEventListener('load', () => {
  const themeSelect = document.getElementById('theme-select');
  const savedTheme = localStorage.getItem(THEME_STORAGE_KEY) || 'system';
  themeSelect.value = ['light', 'dark', 'system'].includes(savedTheme) ? savedTheme : 'system';
  applyTheme(themeSelect.value);
  themeSelect.addEventListener('change', (event) => applyTheme(event.target.value));
  document.getElementById('new-game').addEventListener('click', newGame);
  document.getElementById('check-solution').addEventListener('click', checkSolution);
  document.getElementById('hint-button').addEventListener('click', requestHint);
  renderTop10(loadTop10());
  // initialize
  newGame();
});