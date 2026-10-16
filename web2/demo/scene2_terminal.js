/* Progressive terminal build for the demo.
 *
 * The server sends `style-src 'self'`, which blocks inline <style> and
 * style="" attributes, so this lives in its own same-origin file. It exposes
 * window.__reveal(n) so the recorder can sync the reveal to the voiceover
 * instead of relying on a blind timed animation.
 */
(function () {
  "use strict";
  var body = document.querySelector(".term-body");
  if (!body) return;

  var blocks = Array.prototype.slice.call(body.children);

  window.__revealCount = 0;
  window.__reveal = function (n) {
    n = Math.max(0, Math.min(n | 0, blocks.length));
    blocks.forEach(function (b, i) {
      b.classList.toggle("pending", i >= n);
    });
    window.__revealCount = n;
    return n;
  };

  /* Blink a caret on the most recently revealed command line. */
  window.__caret = function (on) {
    var shown = blocks.filter(function (b) {
      return b.classList.contains("cmd-line") && !b.classList.contains("pending");
    });
    shown.forEach(function (b) { b.classList.toggle("typing", !!on); });
    return shown.length;
  };

  window.__reveal(0);
})();