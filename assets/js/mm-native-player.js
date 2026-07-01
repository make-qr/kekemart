(function () {
  'use strict';

  if (!document.documentElement.hasAttribute('data-native-game')) return;

  var frame = document.getElementById('playerFrame');
  var iframe = document.getElementById('playerIframe');
  if (!frame || !iframe) return;

  var GAME_KEYS = {
    ArrowUp: 1,
    ArrowDown: 1,
    ArrowLeft: 1,
    ArrowRight: 1,
    ' ': 1,
    Spacebar: 1,
  };

  function focusGame() {
    try {
      iframe.focus({ preventScroll: true });
    } catch (e) {
      try {
        iframe.focus();
      } catch (e2) {}
    }
  }

  iframe.setAttribute('tabindex', '0');

  frame.addEventListener(
    'pointerdown',
    function () {
      focusGame();
    },
    { passive: true }
  );

  var hint = document.createElement('div');
  hint.className = 'mm-play-hint';
  hint.setAttribute('role', 'status');
  hint.innerHTML =
    '<span class="mm-play-hint-text">Bấm vào vùng game để chơi (phím mũi tên / WASD)</span>';
  frame.appendChild(hint);

  var hintDismissed = false;
  try {
    hintDismissed = sessionStorage.getItem('mm_native_play_hint') === '1';
  } catch (e) {}

  function hideHint() {
    hintDismissed = true;
    hint.classList.add('is-hidden');
    frame.classList.remove('mm-needs-focus');
    try {
      sessionStorage.setItem('mm_native_play_hint', '1');
    } catch (e) {}
  }

  function maybeShowHint() {
    if (hintDismissed) return;
    var src = iframe.getAttribute('src') || '';
    if (!src || src === 'about:blank') return;
    hint.classList.remove('is-hidden');
    frame.classList.add('mm-needs-focus');
  }

  frame.addEventListener('pointerdown', hideHint, { once: true, passive: true });
  iframe.addEventListener('load', function () {
    setTimeout(maybeShowHint, 1200);
  });

  document.addEventListener(
    'keydown',
    function (e) {
      if (!GAME_KEYS[e.key]) return;
      var rect = frame.getBoundingClientRect();
      if (rect.bottom < 0 || rect.top > window.innerHeight) return;
      if (document.activeElement === iframe) return;
      e.preventDefault();
      focusGame();
    },
    true
  );
})();
