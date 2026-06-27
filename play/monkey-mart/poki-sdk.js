(function () {
  'use strict';

  var resolved = Promise.resolve();
  var resolvedFalse = Promise.resolve(false);
  var rejected = Promise.reject();

  function noop() {}
  function noopPromise() {
    return resolved;
  }

  window.PokiSDK = {
    init: noopPromise,
    initWithVideoHB: noopPromise,
    customEvent: noop,
    commercialBreak: noopPromise,
    rewardedBreak: function () {
      return resolvedFalse;
    },
    displayAd: noop,
    destroyAd: noop,
    getLeaderboard: noopPromise,
    getSharableURL: function () {
      return rejected;
    },
    getURLParam: function () {
      return '';
    },
    disableProgrammatic: noop,
    gameLoadingStart: noop,
    gameLoadingFinished: noop,
    gameInteractive: noop,
    roundStart: noop,
    roundEnd: noop,
    muteAd: noop,
    setDebug: noop,
    gameplayStart: noop,
    gameplayStop: noop,
    gameLoadingProgress: noop,
    happyTime: noop,
    setPlayerAge: noop,
    togglePlayerAdvertisingConsent: noop,
    logError: noop,
    sendHighscore: noop,
    setDebugTouchOverlayController: noop,
  };
})();
