'use strict';
const $ = id => document.getElementById(id);
$('year').textContent = new Date().getFullYear();
const toggle=document.querySelector('.menu-toggle');
toggle.addEventListener('click',()=>{const open=document.querySelector('.nav').classList.toggle('open');toggle.setAttribute('aria-expanded',String(open));});
document.querySelectorAll('.nav a').forEach(a=>a.addEventListener('click',()=>{document.querySelector('.nav').classList.remove('open');toggle.setAttribute('aria-expanded','false');}));
const cacheKey='tcv-market-v3';
const maxAge=5*60*1000;
const legacyKey='tcv-market-v2';
function compact(n){if(!Number.isFinite(n))return '—';if(n>=1e12)return '$'+(n/1e12).toFixed(2)+'T';if(n>=1e9)return '$'+(n/1e9).toFixed(2)+'B';if(n>=1e6)return '$'+(n/1e6).toFixed(1)+'M';return '$'+n.toLocaleString('en-US');}
function percentage(n){if(!Number.isFinite(n))return '—';return (n>0?'+':'')+n.toFixed(2).replace('.',',')+'%';}
function renderMarket(data,stamp,source,stale=false){
 $('market-cap').textContent=compact(data.cap);
 $('market-volume').textContent=compact(data.volume);
 $('btc-dom').textContent=Number.isFinite(data.btc)?data.btc.toFixed(1).replace('.',',')+'%':'—';
 $('eth-dom').textContent=Number.isFinite(data.eth)?data.eth.toFixed(1).replace('.',',')+'%':'—';
 const change=$('market-change');change.replaceChildren();
 if(Number.isFinite(data.change)){const span=document.createElement('span');span.className=data.change>=0?'positive':'negative';span.textContent=percentage(data.change);change.append(span);}
 const formatted=new Intl.DateTimeFormat('vi-VN',{timeZone:'Asia/Ho_Chi_Minh',day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'}).format(new Date(stamp));
 $('updated').textContent='Tổng quan '+source+': '+formatted+' (GMT+7)'+(stale?' · Dữ liệu cũ, chưa cập nhật được':'');
}
async function request(url){const controller=new AbortController();const timer=setTimeout(()=>controller.abort(),9000);try{const response=await fetch(url,{signal:controller.signal,cache:'no-store',headers:{accept:'application/json'}});if(!response.ok)throw Error('HTTP '+response.status);return await response.json();}finally{clearTimeout(timer);}}
function valid(n){return Number.isFinite(n)&&n>0;}
async function coingecko(){const raw=await request('https://api.coingecko.com/api/v3/global');const g=raw?.data;const cap=g?.total_market_cap?.usd,volume=g?.total_volume?.usd;if(!valid(cap)||!valid(volume))throw Error('CoinGecko returned incomplete data');return {cap,volume,btc:g.market_cap_percentage?.btc,eth:g.market_cap_percentage?.eth,change:g.market_cap_change_percentage_24h_usd};}
async function coinpaprika(){const g=await request('https://api.coinpaprika.com/v1/global');const cap=g?.market_cap_usd,volume=g?.volume_24h_usd;if(!valid(cap)||!valid(volume))throw Error('CoinPaprika returned incomplete data');let eth=NaN;try{const e=await request('https://api.coinpaprika.com/v1/tickers/eth-ethereum?quotes=USD');const ethCap=e?.quotes?.USD?.market_cap;if(valid(ethCap))eth=ethCap/cap*100;}catch(err){console.warn('ETH dominance fallback unavailable:',err.message);}return {cap,volume,btc:g.bitcoin_dominance_percentage,eth,change:NaN};}
function getSaved(){for(const key of [cacheKey,legacyKey]){try{const saved=JSON.parse(localStorage.getItem(key)||'null');if(saved?.timestamp&&saved?.data){if(saved.data.cap)return saved;const g=saved.data?.data;if(g?.total_market_cap?.usd)return {timestamp:saved.timestamp,source:'CoinGecko',data:{cap:g.total_market_cap.usd,volume:g.total_volume?.usd,btc:g.market_cap_percentage?.btc,eth:g.market_cap_percentage?.eth,change:g.market_cap_change_percentage_24h_usd}};}}catch{}}return null;}
let inFlight=false;
async function update(){if(inFlight)return;inFlight=true;const saved=getSaved();if(saved?.data)renderMarket(saved.data,saved.timestamp,saved.source||'CoinGecko',true);
 let errors=[];
 for(const [name,fn] of [['CoinGecko',coingecko],['CoinPaprika',coinpaprika]]){
  try{const data=await fn();const timestamp=Date.now();renderMarket(data,timestamp,name);try{localStorage.setItem(cacheKey,JSON.stringify({data,timestamp,source:name}));}catch{}inFlight=false;return;}
  catch(err){errors.push(name+': '+err.message);}
 }
 if(!saved?.data)$('updated').textContent='Tổng quan thị trường: chưa tải được · Kiểm tra kết nối mạng hoặc thử lại sau';
 console.warn('Market overview unavailable:',errors.join(' | '));inFlight=false;
}
update();setInterval(update,maxAge);
