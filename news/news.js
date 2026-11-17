/* THE CRYPTO VIETNAM - headline-only RSS reader. Never renders HTML from RSS. */
(function(){
  'use strict';
  const list=document.querySelector('[data-tcv-news-list]');
  if(!list) return;
  const status=document.querySelector('[data-tcv-news-status]');
  const updated=document.querySelector('[data-tcv-news-updated]');
  const max=list.dataset.limit?Number(list.dataset.limit):3;
  const fmt=new Intl.DateTimeFormat('vi-VN',{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit',timeZone:'Asia/Ho_Chi_Minh'});
  function message(t){list.replaceChildren();const p=document.createElement('p');p.className='tcv-news-empty';p.textContent=t;list.append(p)}
  function safeUrl(raw){try{const url=new URL(raw);if(url.protocol!=='https:')return null;return url.href}catch(_){return null}}
  const labels={"Pháp lý":"Pháp lý","ETF & tổ chức":"ETF & tổ chức","Bảo mật":"Bảo mật","Bitcoin":"Bitcoin","Ethereum":"Ethereum","Altcoin & DeFi":"Altcoin & DeFi","Sàn & giao dịch":"Sàn & giao dịch","Thị trường":"Thị trường"};
  function approvedRow(item, translations){
    const entry=translations && translations[item.url];
    if(!entry || entry.approved!==true || typeof entry.title_vi!=='string' || !entry.title_vi.trim())return null;
    return entry;
  }
  function render(items,translations){
    list.replaceChildren();
    items.slice(0,max).forEach((article)=>{
      const url=safeUrl(article.url);if(!url||!article.title||!article.source)return;
      const row=document.createElement('article');row.className='tcv-news-item';
      const approved=approvedRow(article,translations);
      const anchor=document.createElement('a');anchor.href=url;anchor.target='_blank';anchor.rel='noopener noreferrer';anchor.textContent=approved?approved.title_vi:article.title;
      if(approved)anchor.title=article.title;
      const meta=document.createElement('div');meta.className='tcv-news-meta';
      const source=document.createElement('span');source.textContent=article.source;
      if(article.category && labels[article.category]){const category=document.createElement('span');category.className='tcv-news-topic';category.textContent=labels[article.category];meta.append(category)}
      meta.append(source);
      const dt=new Date(article.published_at);
      if(Number.isFinite(dt.getTime())){const tm=document.createElement('time');tm.dateTime=article.published_at;tm.textContent=fmt.format(dt)+' (GMT+7)';meta.append(tm)}
      row.append(anchor);
      if(approved && typeof approved.summary_vi==='string' && approved.summary_vi.trim()){
        const summary=document.createElement('p');summary.className='tcv-news-summary';summary.textContent=approved.summary_vi.slice(0,260);row.append(summary)
      }
      row.append(meta);list.append(row)
    });
    if(!list.children.length)message('Chưa có bản tin phù hợp từ RSS.')
  }
  const fetchJson=(path)=>fetch(path,{cache:'no-store'}).then(r=>{if(!r.ok)throw new Error('HTTP '+r.status);return r.json()});
  Promise.all([fetchJson('news/data/latest.json?v=2'),fetchJson('news/data/approved_vi.json?v=2').catch(()=>({items:{}}))]).then(([data,vi])=>{
    if(!data||!Array.isArray(data.items)||!data.items.length){message('Chưa có bản tin mới. Hệ thống đang chờ cập nhật RSS.');return}
    const stamp=new Date(data.updated_at);const stale=!Number.isFinite(stamp.getTime())||(Date.now()-stamp.getTime()>36*3600000);
    render(data.items,vi&&vi.items);
    if(status)status.textContent=stale?'Bản tin lưu gần nhất · Cần kiểm tra thời điểm cập nhật':'Tin chọn lọc từ RSS · Bản dịch chỉ hiển thị khi đã duyệt';
    if(updated)updated.textContent=Number.isFinite(stamp.getTime())?'Đồng bộ: '+fmt.format(stamp)+' (GMT+7)':'';
  }).catch(()=>{message('Chưa thể tải tin tức. Vui lòng xem nguồn tin trực tiếp.');if(status)status.textContent='Dữ liệu tạm thời không khả dụng'})
})();
