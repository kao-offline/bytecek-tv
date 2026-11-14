'use strict';

const BASE = [
  {id:'spilled',name:'Spilled',url:'https://spilled.kaooffline.top/',mode:'app',icon:'spilled'},
  {id:'ct24',name:'ČT24',url:'https://ct24.ceskatelevize.cz/video/zive-vysilani',mode:'app',icon:'ct24'},
  {id:'chrome',name:'Chrome',url:'https://www.google.com/',mode:'browser',icon:'chrome'}
];
const STORAGE_KEY = 'bytecek-shortcuts-v1';
const REDUCED = matchMedia('(prefers-reduced-motion: reduce)').matches;
const $ = (id) => document.getElementById(id);
let apiToken = '';
let shortcuts = [];
let resumeItems = [];
let selected = 0;
let pendingAction = '';
let priorFocus = null;
let toastTimer;

const ICONS = {
  spilled: '<img class="app-icon" src="/icons/spilled.png" alt="">',
  ct24: '<img class="app-icon" src="/icons/ct24.svg" alt="">',
  chrome: '<img class="app-icon" src="/icons/chrome.svg" alt="">',
  add: `<svg viewBox="0 0 100 100" aria-hidden="true"><path stroke="#f6e9cc" stroke-linecap="round" stroke-width="9" d="M50 18v64M18 50h64"/></svg>`,
  custom: `<svg viewBox="0 0 100 100" aria-hidden="true"><circle cx="50" cy="50" r="34" stroke="#3a2418" stroke-width="7" fill="none"/><path d="M16 50h68M50 16a52 52 0 0 1 0 68M50 16a52 52 0 0 0 0 68" fill="none" stroke="#3a2418" stroke-width="5"/></svg>`
};

function loadShortcuts(){
  try {const val=JSON.parse(localStorage.getItem(STORAGE_KEY)||'[]');return Array.isArray(val)?val.filter(v=>v && typeof v.id==='string' && typeof v.name==='string' && isValidUrl(v.url) && v.mode==='app').slice(0,20):[]}
  catch{return []}
}
function saveShortcuts(){localStorage.setItem(STORAGE_KEY,JSON.stringify(shortcuts))}
function isValidUrl(value){try{const u=new URL(value);return ['http:','https:'].includes(u.protocol)}catch{return false}}
function escapeText(s){return String(s).replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]))}
function showToast(message){const t=$('toast');t.textContent=message;t.classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>t.classList.remove('visible'),4000)}

function tileIcon(item){
  if(item.icon!=='custom')return ICONS[item.icon]||ICONS.custom;
  // Domain only: paths, query strings and credentials never leave the launcher.
  const domain=new URL(item.url).hostname;
  return `<span class="site-fallback">${ICONS.custom}</span><img class="app-icon site-icon" referrerpolicy="no-referrer" src="https://www.google.com/s2/favicons?domain=${encodeURIComponent(domain)}&sz=128" alt="">`;
}
function hoverFocus(el){el.addEventListener('mouseenter',()=>{if(document.activeElement!==el&&$('add-modal').hidden&&$('confirm').hidden)el.focus({preventScroll:true})})}
function render(){
  const entries=[...BASE,...shortcuts,{id:'add',name:'Add Shortcut',icon:'add'}];
  const root=$('shortcuts');root.style.setProperty('--columns',Math.min(6,entries.length));root.innerHTML=entries.map((item,index)=>`<button class="tile ${escapeText(item.icon||'custom')}" style="--i:${index}" data-index="${index}" data-id="${escapeText(item.id)}" aria-label="${escapeText(item.name)}" title="${escapeText(item.name)}${item.icon==='custom'?' (Delete to remove)':''}"><span class="tile-square">${tileIcon(item)}</span><span class="tile-label">${escapeText(item.name)}</span></button>`).join('');
  root.querySelectorAll('.tile').forEach(tile=>{
    tile.addEventListener('click',()=>activateTile(Number(tile.dataset.index)));
    tile.addEventListener('focus',()=>{selected=Number(tile.dataset.index)});
    tile.addEventListener('contextmenu',e=>{const x=entries[Number(tile.dataset.index)];if(x.icon!=='custom')return;e.preventDefault();removeShortcut(x.id)});
    hoverFocus(tile);
  });
  root.querySelectorAll('.site-icon').forEach(img=>{
    img.addEventListener('load',()=>img.previousElementSibling.hidden=true);
    img.addEventListener('error',()=>img.remove());
  });
  selected=Math.min(selected,entries.length-1);
}

/* Continue watching: the browser extension reports Spilled progress to the local service. */
function renderResume(){
  const row=$('resume-row'),list=$('resume-list');
  row.hidden=!resumeItems.length;
  list.innerHTML=resumeItems.map((item,i)=>{
    const art=item.image?`<img data-src="${escapeText(item.image)}" alt="" referrerpolicy="no-referrer" decoding="async">`:'';
    const meta=[item.label,item.left].filter(Boolean).join(' · ');
    return `<button class="resume" style="--i:${BASE.length+shortcuts.length+1+i}" data-resume="${i}" aria-label="${escapeText(item.show)}${meta?', '+escapeText(meta):''}"><span class="resume-art"><span class="resume-initial" aria-hidden="true">${escapeText(item.show.slice(0,1))}</span>${art}</span><span class="resume-text"><span class="resume-show">${escapeText(item.show)}</span><span class="resume-meta">${escapeText(meta)}</span></span><span class="resume-progress" style="--p:${Math.max(0,Math.min(100,Number(item.progress)||0))}%"></span></button>`;
  }).join('');
  list.querySelectorAll('.resume').forEach(card=>{
    card.addEventListener('click',()=>activateResume(Number(card.dataset.resume)));
    hoverFocus(card);
  });
  list.querySelectorAll('img').forEach(img=>img.addEventListener('error',()=>img.remove()));
  if(curtainSettled)showPosters();
}
let curtainSettled=false;
function showPosters(){document.querySelectorAll('.resume-art img[data-src]').forEach(img=>{img.src=img.dataset.src;img.removeAttribute('data-src')})}
async function loadResume(){
  try{
    const res=await fetch('/api/continue',{cache:'no-store'});
    if(!res.ok)return;
    const data=await res.json();
    const items=Array.isArray(data?.items)?data.items.filter(x=>x&&typeof x.show==='string'&&isValidUrl(x.url)).slice(0,12):[];
    if(JSON.stringify(items)===JSON.stringify(resumeItems))return;
    const hadFocus=document.activeElement?.classList.contains('resume');
    resumeItems=items;renderResume();
    if(hadFocus)(document.querySelector('.resume')||document.querySelector('.tile'))?.focus();
  }catch{}
}

/* Keyboard: arrows move within a row and between rows by on-screen position. */
function navItems(){return [...document.querySelectorAll('.tile, .resume')]}
function rowTarget(items,index,direction){
  const current=items[index].getBoundingClientRect();
  const candidates=items.map((el,i)=>({i,r:el.getBoundingClientRect()})).filter(x=>direction*(x.r.top-current.top)>10);
  if(!candidates.length)return -1;
  const row=Math.min(...candidates.map(x=>Math.abs(x.r.top-current.top)));
  const cx=current.left+current.width/2;
  return candidates.filter(x=>Math.abs(Math.abs(x.r.top-current.top)-row)<5).sort((a,b)=>Math.abs(a.r.left+a.r.width/2-cx)-Math.abs(b.r.left+b.r.width/2-cx))[0].i;
}
function focusEl(el){if(!el)return;el.focus({preventScroll:true});el.scrollIntoView({block:'nearest',inline:'nearest',behavior:REDUCED?'auto':'smooth'})}
function focusTile(index){const tiles=[...document.querySelectorAll('.tile')];selected=Math.max(0,Math.min(index,tiles.length-1));focusEl(tiles[selected])}

let tokenRefresh=null;
async function refreshToken(){
  if(!tokenRefresh)tokenRefresh=(async()=>{
    const response=await fetch('/api/config',{cache:'no-store'});
    if(!response.ok)throw Error('Launcher service is unavailable');
    const data=await response.json();
    if(!data.token)throw Error('Launcher service is unavailable');
    apiToken=data.token;
  })().finally(()=>{tokenRefresh=null});
  return tokenRefresh;
}
async function request(path,payload){
  try{
    if(!apiToken)await refreshToken();
    const send=()=>fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-Bytecek-Token':apiToken},body:JSON.stringify(payload)});
    let res=await send();
    // A service restart invalidates the old token. Rejected requests have no side effects.
    if(res.status===401||res.status===403){await refreshToken();res=await send()}
    const data=await res.json();if(!res.ok)throw Error(data.error||'Request failed');return data;
  }catch(e){showToast(e.message);return null}
}

/* Curtain: closes on launch; on return Home it closes over the screen, then opens. */
let curtainFallback;
let returning=false;
let homeShown=null;
const curtain=()=>$('curtain');
function closeCurtain(){curtain().classList.add('closed','lit')}
function openCurtain(){clearTimeout(curtainFallback);$('launching').hidden=true;curtain().classList.remove('closed','lit')}
function playReturn(){
  if(returning)return;returning=true;
  // Normally the curtain is still closed from the launch or exit: just open it.
  if(curtain().classList.contains('closed')){setTimeout(()=>{openCurtain();returning=false},REDUCED?0:200);return}
  closeCurtain();
  setTimeout(()=>{openCurtain();returning=false},REDUCED?0:1250);
}
// show-launcher.sh stamps the moment Home is brought back (F9, Menu, Home key).
async function checkHomeShown(){
  try{
    const res=await fetch('/api/home',{cache:'no-store'});if(!res.ok)return;
    const shown=Number((await res.json())?.shown)||0;
    if(homeShown!==null&&shown>homeShown){homeShown=shown;welcomeBack(true);return}
    homeShown=shown;
  }catch{}
}
setInterval(checkHomeShown,300);checkHomeShown();
function nothingFocused(){const a=document.activeElement;return !a||a===document.body}
function welcomeBack(returned){
  loadResume();
  if(nothingFocused()&&$('add-modal').hidden&&$('confirm').hidden)focusTile(selected);
  if(returned===true)playReturn();
}
addEventListener('focus',welcomeBack);
document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')welcomeBack()});

function openAdd(){priorFocus=document.activeElement;$('add-form').reset();$('form-error').textContent='';$('add-modal').hidden=false;$('shortcut-name').focus()}
function closeAdd(){$('add-modal').hidden=true;(priorFocus&&priorFocus.isConnected?priorFocus:document.querySelector('.tile.add'))?.focus()}
function removeShortcut(id){const s=shortcuts.find(s=>s.id===id);if(!s)return; if(!window.confirm(`Remove ${s.name}?`))return;shortcuts=shortcuts.filter(x=>x.id!==id);saveShortcuts();render();focusTile(0)}
let launching=false;
async function launch(name,url,mode){
  if(launching)return;launching=true;
  $('launch-label').textContent='Opening '+name;$('launching').hidden=false;
  closeCurtain();
  // Let the curtain finish closing; the app then appears behind its own closed curtain.
  if(!REDUCED)await new Promise(r=>setTimeout(r,850));
  const ok=await request('/api/launch',{url,mode});
  setTimeout(()=>{$('launching').hidden=true;launching=false},900);
  if(!ok){setTimeout(openCurtain,600);return}
  // The app window normally covers the launcher; the curtain reopens when Home returns.
  // Stay closed behind the app; returning Home opens it.
}
function activateTile(index){const items=[...BASE,...shortcuts,{id:'add'}];const item=items[index];if(!item)return;if(item.id==='add'){openAdd();return}launch(item.name,item.url,item.mode||'app')}
function activateResume(index){const item=resumeItems[index];if(item)launch(item.show,item.url,'app')}
function togglePower(force){const panel=$('power-panel');panel.hidden=typeof force==='boolean'?!force:!panel.hidden;if(!panel.hidden){document.querySelector('.power-item').focus()}else{$('power-toggle').focus()}}
function openConfirm(action){pendingAction=action;priorFocus=document.activeElement; $('confirm').hidden=false;$('confirm-no').focus()}
function closeConfirm(){$('confirm').hidden=true;(priorFocus?.isConnected?priorFocus:$('power-toggle')).focus()}

$('power-toggle').addEventListener('click',()=>togglePower());
$('exit').addEventListener('click',()=>openConfirm('exit'));
$('power-panel').addEventListener('click',e=>{const btn=e.target.closest('[data-power]');if(btn)openConfirm(btn.dataset.power)});
$('confirm-no').addEventListener('click',closeConfirm);
$('confirm-yes').addEventListener('click',async()=>{
  const action=pendingAction;closeConfirm();
  if(action!=='exit'){await request('/api/power',{action});return}
  closeCurtain();
  if(!REDUCED)await new Promise(r=>setTimeout(r,850));
  if(!await request('/api/exit',{}))openCurtain();
});
$('add-cancel').addEventListener('click',closeAdd);
$('add-form').addEventListener('submit',e=>{
  e.preventDefault();const name=$('shortcut-name').value.trim();let url=$('shortcut-url').value.trim();if(url&&!/^[a-zA-Z]+:\/\//.test(url))url='https://'+url;
  if(!name||name.length>32||!isValidUrl(url)){$('form-error').textContent='Enter a name and an http(s) URL';return}
  if(shortcuts.length>=20){$('form-error').textContent='Maximum of 20 custom shortcuts';return}
  shortcuts.push({id:'user-'+Date.now(),name,url,mode:'app',icon:'custom'});saveShortcuts();render();closeAdd();focusTile(BASE.length+shortcuts.length-1);
});

document.addEventListener('keydown',e=>{
  if(e.key==='Escape'){
    if(!$('add-modal').hidden){closeAdd();e.preventDefault();return}
    if(!$('confirm').hidden){closeConfirm();e.preventDefault();return}
    if(!$('power-panel').hidden){togglePower(false);e.preventDefault();return}
    focusTile(0);return;
  }
  if(!$('add-modal').hidden||!$('confirm').hidden)return;
  if(e.key==='Delete'&&document.activeElement?.classList.contains('tile')){
    const id=document.activeElement.dataset.id;if(id.startsWith('user-')){removeShortcut(id);e.preventDefault();return}
  }
  if(nothingFocused()&&e.key.startsWith('Arrow')){focusTile(selected);e.preventDefault();return}
  const target=document.activeElement;
  const items=navItems();
  const index=items.indexOf(target);
  if(index>=0){
    const group=[...target.parentElement.children];const g=group.indexOf(target);
    if(e.key==='ArrowRight'){focusEl(group[(g+1)%group.length]);e.preventDefault()}
    else if(e.key==='ArrowLeft'){focusEl(group[(g-1+group.length)%group.length]);e.preventDefault()}
    else if(e.key==='ArrowDown'){const next=rowTarget(items,index,1);if(next>=0)focusEl(items[next]);else $('exit').focus();e.preventDefault()}
    else if(e.key==='ArrowUp'){const next=rowTarget(items,index,-1);if(next>=0)focusEl(items[next]);else $('power-toggle').focus();e.preventDefault()}
  }else if(target?.id==='exit'||target?.id==='power-toggle'){
    if(e.key==='ArrowUp'){const last=document.querySelector('.resume')||document.querySelectorAll('.tile')[selected];focusEl(last);e.preventDefault()}
    else if(e.key==='ArrowLeft'){$('power-toggle').focus();e.preventDefault()}
    else if(e.key==='ArrowRight'){$('exit').focus();e.preventDefault()}
  }else if(target?.classList.contains('power-item')){
    const options=[...document.querySelectorAll('.power-item')];const idx=options.indexOf(target);
    if(e.key==='ArrowDown'){options[(idx+1)%options.length].focus();e.preventDefault()}
    else if(e.key==='ArrowUp'){options[(idx+options.length-1)%options.length].focus();e.preventDefault()}
    else if(e.key==='ArrowRight'){togglePower(false);$('exit').focus();e.preventDefault()}
  }
});

function tickClock(){$('clock').textContent=new Date().toLocaleTimeString('cs-CZ',{hour:'2-digit',minute:'2-digit'})}
tickClock();setInterval(tickClock,15000);

shortcuts=loadShortcuts();render();
refreshToken().catch(()=>showToast('Launcher service unavailable'));
loadResume();setInterval(()=>{if(document.visibilityState==='visible')loadResume()},60000);

// Boot: the B lights on the closed curtain, then the curtain parts once the page has painted.
const frames=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
const pageReady=Promise.race([
  Promise.all([document.fonts?.ready,document.readyState==='complete'?null:new Promise(r=>addEventListener('load',r,{once:true}))]),
  new Promise(r=>setTimeout(r,2500))
]);
setTimeout(()=>$('curtain').classList.add('lit'),REDUCED?0:120);
Promise.all([pageReady,new Promise(r=>setTimeout(r,REDUCED?0:700))]).then(frames).then(()=>{
  $('shell').classList.add('play');
  openCurtain();focusTile(0);
  setTimeout(()=>{curtainSettled=true;showPosters()},REDUCED?0:1150);
  setTimeout(()=>$('shell').classList.remove('enter','play'),REDUCED?0:2400);
});
