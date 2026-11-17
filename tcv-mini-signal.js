/* Compact homepage feed. Real scan records only; never synthesizes trade ideas. */
(() => {
  'use strict';
  const state = document.getElementById('mini-state');
  const board = document.getElementById('mini-signals');
  const updated = document.getElementById('mini-updated');
  if (!state || !board || !updated) return;
  const MAX_AGE_MS = 40 * 60 * 1000;
  const fmt = (time) => new Intl.DateTimeFormat('vi-VN', {
    timeZone: 'Asia/Ho_Chi_Minh', hour:'2-digit', minute:'2-digit',
    day:'2-digit', month:'2-digit', year:'numeric', hour12:false
  }).format(new Date(time));
  function setState(message, type) {
    state.textContent = message;
    state.className = 'mini-state' + (type ? ' is-' + type : '');
  }
  function placeholder(message) {
    const div = document.createElement('div');
    div.className = 'mini-placeholder';
    div.textContent = message;
    board.replaceChildren(div);
  }
  function addSignal(signal) {
    const card = document.createElement('div');
    card.className = 'mini-signal';
    const main = document.createElement('div');
    main.className = 'mini-signal-main';
    const coin = document.createElement('div');
    coin.className = 'mini-symbol';
    coin.textContent = String(signal.symbol).replace(/USDT$/, '/USDT');
    const detail = document.createElement('div');
    detail.className = 'mini-detail';
    const score = Number(signal.score);
    detail.textContent = 'Khung ' + signal.interval.toUpperCase() +
      (Number.isFinite(score) ? ' · Điểm lọc ' + Math.round(score) + '/100' : '');
    main.append(coin, detail);
    const badge = document.createElement('span');
    badge.className = 'mini-direction ' + signal.signal.toLowerCase();
    badge.textContent = signal.signal;
    card.append(main, badge);
    board.append(card);
  }
  async function refresh() {
    try {
      const response = await fetch('ai-signal/data/latest.json?t=' + Date.now(), {cache: 'no-store'});
      if (!response.ok) throw new Error('HTTP ' + response.status);
      const data = await response.json();
      const generated = Number(data.generated_at);
      if (!Number.isFinite(generated) || generated <= 0) {
        setState('CHƯA CÓ DỮ LIỆU');
        updated.textContent = 'Chưa chạy bộ quét Futures';
        placeholder('Chưa có dữ liệu xác thực. Hệ thống cần chạy lần quét Binance đầu tiên.');
        return;
      }
      updated.textContent = 'Quét lúc ' + fmt(generated) + ' (GMT+7)';
      const age = Date.now() - generated;
      if (age < -5 * 60 * 1000 || age > MAX_AGE_MS) {
        setState('DỮ LIỆU CŨ', 'stale');
        placeholder('Lần quét đã quá 40 phút hoặc sai thời gian. Không hiển thị tín hiệu cũ như tín hiệu mới.');
        return;
      }
      if (!Array.isArray(data.signals)) throw new Error('Invalid signal list');
      // Incomplete scans are explicitly identified; the displayed entries must come
      // from this recent, successful scan, not from defaults or stale cached values.
      setState(data.status === 'live' ? 'ĐÃ CẬP NHẬT' : 'DỮ LIỆU MỘT PHẦN', data.status === 'live' ? 'fresh' : 'stale');
      const good = data.signals.filter(s => s && (s.signal === 'LONG' || s.signal === 'SHORT') &&
        typeof s.symbol === 'string' && /^[A-Z0-9]{2,24}USDT$/.test(s.symbol) &&
        ['15m', '1h', '4h'].includes(s.interval) &&
        Number.isFinite(Number(s.close_time)) &&
        Math.abs(generated - Number(s.close_time)) <= 5 * 60 * 60 * 1000)
        .sort((a,b) => Number(b.close_time)-Number(a.close_time) || Number(b.score)-Number(a.score))
        .slice(0, 3);
      board.replaceChildren();
      if (!good.length) {
        placeholder('Chưa phát hiện tín hiệu LONG/SHORT đủ điều kiện. Đang theo dõi Top 20 Futures.');
        return;
      }
      good.forEach(addSignal);
    } catch (error) {
      setState('MẤT KẾT NỐI', 'error');
      updated.textContent = 'Không tải được dữ liệu';
      placeholder('Chưa thể tải tín hiệu. Vui lòng thử lại sau.');
    }
  }
  refresh();
  window.setInterval(refresh, 60 * 1000);
})();
