/* TCV Market Radar — real scheduled scan output only, no demo quotes. */
(() => {
  'use strict';
  const inFullPage = document.body.classList.contains('radar-page');
  const grid = document.getElementById(inFullPage ? 'radar-full-grid' : 'radar-home-grid');
  if (!grid) return;
  const status = document.getElementById(inFullPage ? 'radar-full-status' : 'radar-home-status');
  const updated = document.getElementById(inFullPage ? 'radar-full-updated' : 'radar-home-updated');
  const dataUrl = inFullPage ? 'data/latest.json' : 'market-radar/data/latest.json';
  const currentMaxAge = 40 * 60 * 1000;
  const number = n => Number.isFinite(Number(n)) ? Number(n) : null;
  const fmt = v => `${v > 0 ? '+' : ''}${v.toFixed(2)}%`;
  const safe = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const renderEmpty = msg => { grid.innerHTML = ''; const el = document.createElement('div'); el.className = 'radar-empty'; el.textContent = msg; grid.append(el); };
  const query = new URLSearchParams(location.search);
  const modeSelect = document.getElementById('radar-mode');
  const sortSelect = document.getElementById('radar-sort');
  let coins = [];
  function render() {
    const mode = modeSelect ? modeSelect.value : 'all';
    const sort = sortSelect ? sortSelect.value : 'volume';
    let rows = coins.filter(c => mode === 'all' || (mode === 'up' && c.change_pct_24h > 0.25) || (mode === 'down' && c.change_pct_24h < -0.25) || (mode === 'volume' && c.volume_alert));
    rows = [...rows].sort((a,b) => sort === 'change' ? Math.abs(b.change_pct_24h) - Math.abs(a.change_pct_24h) : sort === 'anomaly' ? b.anomaly_score - a.anomaly_score : b.quote_volume_24h - a.quote_volume_24h);
    if (!inFullPage) rows = rows.slice(0,12);
    grid.innerHTML = '';
    if (!rows.length) { renderEmpty('Chưa có đồng coin phù hợp bộ lọc hiện tại.'); return; }
    for (const c of rows) {
      const cell = document.createElement('a');
      cell.className = `radar-tile ${c.change_pct_24h > 0.25 ? 'radar-up' : c.change_pct_24h < -0.25 ? 'radar-down' : 'radar-flat'}`;
      cell.href = `${inFullPage ? '../' : ''}ai-signal/?symbol=${encodeURIComponent(c.symbol)}`;
      const score = Number.isFinite(c.anomaly_score) ? ` · Điểm bất thường ${c.anomaly_score}/100` : '';
      cell.setAttribute('aria-label', `${c.symbol}, biến động 24 giờ ${fmt(c.change_pct_24h)}, xem AI Signal`);
      cell.innerHTML = `<strong>${safe(c.symbol.replace(/USDT$/,''))}</strong><small>${fmt(c.change_pct_24h)}</small><em>${c.volume_alert ? '▲ Volume bất thường' : `KL 24h ${compact(c.quote_volume_24h)}`}</em>`;
      cell.title = `Khối lượng 24h: ${compact(c.quote_volume_24h)} USDT${score}. Dữ liệu 24h, không phải tín hiệu mua bán.`;
      grid.append(cell);
    }
  }
  const compact = n => n >= 1e9 ? `${(n/1e9).toFixed(2)}B` : n >= 1e6 ? `${(n/1e6).toFixed(1)}M` : n >= 1e3 ? `${(n/1e3).toFixed(0)}K` : String(Math.round(n));
  modeSelect?.addEventListener('change',render);
  sortSelect?.addEventListener('change',render);
  async function load() {
    try {
      const res = await fetch(`${dataUrl}?t=${Date.now()}`, {cache:'no-store'});
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const payload = await res.json();
      const stamp = number(payload.generated_at);
      if (!stamp || stamp > Date.now() + 120000 || Date.now() - stamp > currentMaxAge) {
        status.textContent = 'DỮ LIỆU CHƯA SẴN SÀNG';
        if (stamp) updated.textContent = `Lần cập nhật: ${new Date(stamp).toLocaleString('vi-VN')} · Dữ liệu đã quá 40 phút`;
        renderEmpty('Chưa có dữ liệu mới từ bộ quét Binance. Vui lòng kiểm tra GitHub Actions.');
        return;
      }
      if (!Array.isArray(payload.coins) || !payload.coins.length) throw new Error('No verified coins');
      coins = payload.coins.map(x => ({symbol:String(x.symbol || ''), change_pct_24h:number(x.change_pct_24h),quote_volume_24h:number(x.quote_volume_24h),volume_alert:x.volume_alert === true,anomaly_score:number(x.anomaly_score)}))
        .filter(x => /^[A-Z0-9]{2,24}USDT$/.test(x.symbol) && x.change_pct_24h !== null && x.quote_volume_24h !== null && x.quote_volume_24h >= 0);
      if (!coins.length) throw new Error('No validated coins');
      status.textContent = `ĐÃ CẬP NHẬT · ${coins.length} COIN`;
      updated.textContent = `Cập nhật: ${new Date(stamp).toLocaleString('vi-VN')} · Nguồn: Binance USDⓈ-M Futures`;
      render();
    } catch (err) {
      status.textContent = 'CHƯA CÓ DỮ LIỆU';
      updated.textContent = 'Không tải được dữ liệu từ bộ quét';
      renderEmpty('Không tải được dữ liệu Radar. Hãy chạy bộ quét bằng GitHub Actions trước khi xuất bản.');
    }
  }
  load();
  setInterval(load, 5*60*1000);
})();
