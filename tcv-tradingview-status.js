/* TradingView load diagnostics; no fabricated quotes or infinite spinner. */
(function () {
  var ticker = document.getElementById('tcv-tv-ticker');
  var label = document.getElementById('tcv-tv-loading');
  if (!ticker || !label) return;
  var done = false;
  var help = 'TradingView không tải được. Kiểm tra Internet, trình chặn quảng cáo hoặc mở website qua http://localhost.';
  function fail(message) {
    if (done || customElements.get('tv-ticker-tape')) return;
    done = true;
    label.textContent = message || help;
    label.setAttribute('role', 'status');
    label.classList.add('tcv-tv-error');
  }
  window.tcvTVFailed = function () { fail(help); };
  if (customElements.get('tv-ticker-tape')) { done = true; return; }
  customElements.whenDefined('tv-ticker-tape').then(function () { done = true; });
  setTimeout(function () { fail(help); }, 12000);
})();
