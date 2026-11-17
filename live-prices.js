'use strict';
/* CoinGecko ranks by USD market cap; Binance Spot USDT streams update eligible prices. */
(()=>{
 const table=document.getElementById('coin-rows'),status=document.getElementById('live-status');
 if(!table||!status)return;
 const RANK_INTERVAL=30*60*1000, RANK_KEY='tcv-dynamic-top5-v1';
 const stableIds=new Set(['tether','usd-coin','dai','first-digital-usd','ethena-usde','usds','paypal-usd','true-usd','frax','usdd','pax-dollar','gemini-dollar','usual-usd','binance-usd','staked-usde','usde','usd1','ripple-usd','rlusd','global-dollar','usdt0','wrapped-steth','wrapped-bitcoin']);
 const stableSymbols=new Set(['USDT','USDC','DAI','FDUSD','USDE','USDS','PYUSD','TUSD','FRAX','USDD','BUSD','GUSD','USD1','RLUSD','USDG','USDT0']);
 const icons={btc:'₿',eth:'◆',bnb:'⬡',sol:'◎',xrp:'✕'};
 let assets=[],socket=null,retryTimer=null,rankTimer=null,attempt=0,closed=false,lastMessage=0,watchdog=null;
 let activeSymbolMap=new Map(), lastPrices=new Map(),fallbackData=new Map(),sourceIsCached=false;
 const fmt=n=>Number.isFinite(n)?n.toLocaleString('en-US',{minimumFractionDigits:n<1?4:2,maximumFractionDigits:n<1?6:2}):'—';
 function state(s,kind='pending'){status.textContent=s;status.dataset.state=kind;}
 function isStable(c){return stableIds.has(c.id)||stableSymbols.has((c.symbol||'').toUpperCase())||/\b(stablecoin|stable coin)\b/i.test(c.name||'');}
 function valid(c){return c&&typeof c.id==='string'&&typeof c.symbol==='string'&&Number.isFinite(c.market_cap)&&c.market_cap>0&&!isStable(c);}
 function readCache(){try{const v=JSON.parse(localStorage.getItem(RANK_KEY)||'null');return v&&Array.isArray(v.assets)&&v.assets.length===5?v:null;}catch{return null;}}
 function storeCache(list){try{localStorage.setItem(RANK_KEY,JSON.stringify({assets:list,stamp:Date.now()}));}catch{}}
 function setRows(list,cached){assets=list;sourceIsCached=cached;activeSymbolMap=new Map();fallbackData=new Map();lastPrices=new Map();table.replaceChildren();
  list.forEach((a,i)=>{const symbol=a.symbol.toUpperCase(),pair=symbol+'USDT';activeSymbolMap.set(pair,a.id);fallbackData.set(a.id,a);const tr=document.createElement('tr');tr.dataset.symbol=pair;
   const rank=document.createElement('td');rank.textContent=String(i+1);const name=document.createElement('td');const wrap=document.createElement('div');wrap.className='coin-name';const badge=document.createElement('span');badge.className='coin-live-icon';badge.textContent=icons[a.symbol.toLowerCase()]||symbol.slice(0,2);badge.setAttribute('aria-hidden','true');badge.style.background='#174a72';const title=document.createElement('span');title.textContent=a.name;const ticker=document.createElement('small');ticker.textContent=symbol;wrap.append(badge,title,ticker);name.append(wrap);const price=document.createElement('td');price.className='live-price';price.textContent=Number.isFinite(a.current_price)?'$'+fmt(a.current_price):'—';const change=document.createElement('td');change.className='live-change';const pct=a.price_change_percentage_24h;change.textContent=Number.isFinite(pct)?(pct>0?'+':'')+pct.toFixed(2).replace('.',',')+'%':'—';change.classList.add(pct>=0?'positive':'negative');tr.append(rank,name,price,change);table.append(tr);});
  state(cached?'Top 5 theo vốn hóa · bảng xếp hạng đã lưu, đang thử cập nhật…':'Top 5 theo vốn hóa CoinGecko · đang kết nối giá Binance…',cached?'offline':'pending');connect();
 }
 function renderTicker(t){if(!t||!activeSymbolMap.has(t.s))return;const row=Array.from(table.rows).find(r=>r.dataset.symbol===t.s);if(!row)return;const value=Number(t.c),pct=Number(t.P);if(!Number.isFinite(value)||!Number.isFinite(pct))return;const price=row.querySelector('.live-price'),change=row.querySelector('.live-change'),old=lastPrices.get(t.s);price.textContent='$'+fmt(value);if(old!==undefined&&old!==value){price.classList.remove('flash-up','flash-down');void price.offsetWidth;price.classList.add(value>old?'flash-up':'flash-down');}lastPrices.set(t.s,value);change.textContent=(pct>0?'+':'')+pct.toFixed(2).replace('.',',')+'%';change.className='live-change '+(pct>=0?'positive':'negative');}
 function stopSocket(){clearTimeout(retryTimer);clearInterval(watchdog);if(socket){const old=socket;socket=null;old.onclose=null;old.close();}}
 function connect(){stopSocket();if(closed||!assets.length)return;const streams=assets.map(a=>a.symbol.toLowerCase()+'usdt@ticker').join('/');const hosts=['data-stream.binance.vision','stream.binance.com'];const host=hosts[attempt%hosts.length];state('Top 5 theo vốn hóa · Binance đang kết nối…','pending');let ws;try{ws=new WebSocket('wss://'+host+':443/stream?streams='+streams);}catch{scheduleReconnect();return;}socket=ws;
  ws.onopen=()=>{if(socket!==ws)return;attempt=0;lastMessage=Date.now();state('Top 5 theo vốn hóa · Binance đã kết nối','pending');watchdog=setInterval(()=>{if(socket===ws&&Date.now()-lastMessage>45000)ws.close();},5000);};
  ws.onmessage=e=>{if(socket!==ws)return;let t;try{const p=JSON.parse(e.data);t=p.data||p;}catch{return;}if(t.e!=='24hrTicker')return;lastMessage=Date.now();renderTicker(t);const time=new Intl.DateTimeFormat('vi-VN',{timeZone:'Asia/Ho_Chi_Minh',hour:'2-digit',minute:'2-digit',second:'2-digit'}).format(new Date());state('Top 5 vốn hóa CoinGecko · giá Binance trực tiếp '+time+(sourceIsCached?' · xếp hạng đã lưu':''),'live');};
  ws.onerror=()=>{if(socket===ws)state('Binance chưa kết nối được · hiển thị giá CoinGecko gần nhất','offline');};
  ws.onclose=()=>{if(socket!==ws)return;socket=null;clearInterval(watchdog);scheduleReconnect();};
 }
 function scheduleReconnect(){if(closed)return;clearTimeout(retryTimer);const delay=Math.min(30000,1500*Math.pow(1.7,Math.min(attempt,7)));attempt++;state('Binance tạm mất kết nối · đang thử lại…','offline');retryTimer=setTimeout(connect,delay);}
 async function loadRank(){try{const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),12000);let res;try{res=await fetch('https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=50&page=1&sparkline=false&price_change_percentage=24h',{signal:controller.signal,cache:'no-store'});}finally{clearTimeout(timer);}if(!res.ok)throw Error('CoinGecko HTTP '+res.status);const coins=await res.json();if(!Array.isArray(coins))throw Error('Invalid CoinGecko response');const list=coins.filter(valid).slice(0,5);if(list.length!==5)throw Error('Incomplete ranking');const previous=assets.map(a=>a.id).join('|');storeCache(list);sourceIsCached=false;if(previous!==list.map(a=>a.id).join('|'))setRows(list,false);else{fallbackData=new Map(list.map(a=>[a.id,a]));assets=list;}
  }catch(err){console.warn('Cannot refresh Top 5 market-cap ranking:',err);if(!assets.length){const saved=readCache();if(saved)setRows(saved.assets,true);else{table.innerHTML='<tr><td colspan="4" class="loading">Chưa tải được Top 5 theo vốn hóa. Vui lòng kiểm tra mạng hoặc thử lại sau.</td></tr>';state('Chưa lấy được bảng xếp hạng từ CoinGecko','offline');}}else{sourceIsCached=true;state('Xếp hạng gần nhất · chưa thể cập nhật CoinGecko','offline');}}
 }
 document.addEventListener('visibilitychange',()=>{if(document.hidden){closed=true;stopSocket();state('Đã tạm dừng khi tab không hoạt động','paused');}else{closed=false;attempt=0;loadRank().then(()=>{if(!socket&&assets.length)connect();});}});
 window.addEventListener('pagehide',()=>{closed=true;stopSocket();clearInterval(rankTimer);});
 const saved=readCache();if(saved)setRows(saved.assets,true);loadRank();rankTimer=setInterval(()=>{if(!document.hidden)loadRank();},RANK_INTERVAL);
})();
