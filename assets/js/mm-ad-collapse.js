(function () {
  'use strict';

  function isFilled(ins) {
    if (!ins) return false;
    var status = ins.getAttribute('data-ad-status');
    if (status === 'filled') return true;
    if (ins.querySelector('iframe')) return ins.offsetHeight > 40;
    return false;
  }

  function isUnfilled(ins) {
    if (!ins) return false;
    var status = ins.getAttribute('data-ad-status');
    return status === 'unfilled' || status === 'error';
  }

  function updateSlot(wrap) {
    var ins = wrap.querySelector('ins.adsbygoogle');
    if (!ins) return;
    if (isFilled(ins)) {
      wrap.classList.add('is-filled');
      wrap.classList.remove('is-empty');
      return;
    }
    if (isUnfilled(ins) || (ins.offsetHeight <= 1 && !ins.querySelector('iframe'))) {
      wrap.classList.add('is-empty');
    }
  }

  function watchSlot(wrap) {
    var ins = wrap.querySelector('ins.adsbygoogle');
    if (!ins) return;
    updateSlot(wrap);
    if (typeof MutationObserver === 'function') {
      var obs = new MutationObserver(function () {
        updateSlot(wrap);
      });
      obs.observe(ins, { attributes: true, attributeFilter: ['data-ad-status'], childList: true, subtree: true });
    }
    [1500, 4000, 10000].forEach(function (ms) {
      setTimeout(function () {
        updateSlot(wrap);
      }, ms);
    });
  }

  function init() {
    document.querySelectorAll('.mm-ad').forEach(watchSlot);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
