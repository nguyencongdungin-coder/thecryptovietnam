/* TCV MARKET PULSE - Top 100 Binance Spot USDT pairs by 24h quote volume.
   Public market data only; NOT a buy/sell indicator. */
(()=>{'use strict';
const $=id=>document.getElementById(id);
const container=$('tcv-pulse-bar');if(!container)return;
const endpoints=[
  'https://data-api.binance.vision/api/v3/ticker/24hr',
  'https://api.binance.com/api/v3/ticker/24hr',
  'https://api1.binance.com/api/v3/ticker/24hr'
];
const STABLE=new Set(['USDT','USDC','FDUSD','TUSD','USDP','DAI','BUSD','USDD','PYUSD','USD1','RLUSD','EURI','EUR','GBP','BRL','TRY','ARS','UAH','AUD','RUB','JPY','BIDR','IDRT','NGN','ZAR','PLN','RON','CZK','MXN','VAI','AEUR','USTC']);
const LEVERAGED=/(UP|DOWN|BULL|BEAR)$/;
const countsFrom=(raw)=>{
 if(!Array.isArray(raw))throw Error('Định dạng dữ liệu không hợp lệ');
 const coins=raw.filter(r=>{
   if(typeof r?.symbol!=='string'||!r.symbol.endsWith('USDT'))return false;
   const base=r.symbol.slice(0,-4);
   return base&&!STABLE.has(base)&&!LEVERAGED.test(base)&&Number(r.quoteVolume)>0&&Number.isFinite(Number(r.priceChangePercent))&&Number(r.lastPrice)>0;
 }).sort((a,b)=>Number(b.quoteVolume)-Number(a.quoteVolume));
 const seen=new Set(), top=[];
 for(const row of coins){const base=row.symbol.slice(0,-4);if(seen.has(base))continue;seen.add(base);top.push(row);if(top.length===100)break;}
 if(top.length<30)throw Error('Không đủ dữ liệu thị trường');
 let up=0,down=0,flat=0;
 for(const row of top){const v=Number(row.priceChangePercent);if(v>0.1)up++;else if(v< -0.1)down++;else flat++;}
 return {up,down,flat,total:top.length};
};
const setStatus=s=>{$('tcv-pulse-status').textContent=s};
const fmt=(v)=>new Intl.DateTimeFormat('vi-VN',{hour:'2-digit',minute:'2-digit',timeZone:'Asia/Ho_Chi_Minh'}).format(new Date(v));
const render=(r)=>{
 const pct=v=>Math.round(v*100/r.total);
 $('tcv-pulse-up').textContent=pct(r.up)+'%';$('tcv-pulse-down').textContent=pct(r.down)+'%';$('tcv-pulse-flat').textContent=pct(r.flat)+'%';
 ['up','down','flat'].forEach(key=>{$('tcv-pulse-'+key+'-bar').style.width=(r[key]*100/r.total)+'%'});
 container.setAttribute('aria-label',`Trong ${r.total} coin: ${r.up} tăng, ${r.down} giảm, ${r.flat} đi ngang`);
 setStatus(`Top ${r.total} coin · Giá 24H · ${fmt(Date.now())} (GMT+7)`);
};
const load=async url=>{
 const c=new AbortController(),timeout=setTimeout(()=>c.abort(),9000);
 try{const res=await fetch(url,{signal:c.signal,cache:'no-store'});if(!res.ok)throw Error('HTTP '+res.status);return countsFrom(await res.json());}
 finally{clearTimeout(timeout);}
};
let running=false,hasData=false;
async function refresh(){if(running||document.hidden)return;running=true;
 if(!hasData)setStatus('Đang tải dữ liệu thị trường…');
 for(const url of endpoints){try{const result=await load(url);render(result);hasData=true;running=false;return;}catch(err){console.warn('TCV Market Pulse:',err.message);}}
 setStatus(hasData?'Mất kết nối · Số liệu gần nhất, chưa cập nhật':'Chưa tải được dữ liệu thị trường · Kiểm tra kết nối');running=false;
}
refresh();setInterval(refresh,5*60*1000);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh();});
})();
