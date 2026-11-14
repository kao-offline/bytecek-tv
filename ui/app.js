'use strict';

const BASE = [
  {id:'spilled',name:'Spilled',url:'https://spilled.kaooffline.top/',mode:'app',icon:'spilled'},
  {id:'ct24',name:'ČT24',url:'https://ct24.ceskatelevize.cz/video/zive-vysilani',mode:'app',icon:'ct24'},
  {id:'chrome',name:'Chrome',url:'https://www.google.com/',mode:'browser',icon:'chrome'}
];
const STORAGE_KEY = 'bytecek-shortcuts-v1';
const $ = (id) => document.getElementById(id);
let apiToken = '';
let shortcuts = [];
let selected = 0;
let pendingAction = '';
let priorFocus = null;
let toastTimer;

const ICONS = {
  spilled: '<img class="app-icon" src="/icons/spilled.png" alt="">',
  ct24: '<img class="app-icon" src="/icons/ct24.svg" alt="">',
  chrome: '<img class="app-icon" src="/icons/chrome.svg" alt="">',
  add: `<svg viewBox="0 0 100 100" aria-hidden="true"><path stroke="#292929" stroke-linecap="round" stroke-width="11" d="M50 15v70M15 50h70"/></svg>`,
  custom: `<svg viewBox="0 0 100 100" aria-hidden="true"><circle cx="50" cy="50" r="34" stroke="#303030" stroke-width="7" fill="none"/><path d="M16 50h68M50 16a52 52 0 0 1 0 68M50 16a52 52 0 0 0 0 68" fill="none" stroke="#303030" stroke-width="5"/></svg>`
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
function rowTarget(tiles,index,direction){
  const current=tiles[index].getBoundingClientRect();
  const candidates=tiles.map((tile,i)=>({i,r:tile.getBoundingClientRect()})).filter(x=>direction*(x.r.top-current.top)>10);
  if(!candidates.length)return -1;
  const row=Math.min(...candidates.map(x=>Math.abs(x.r.top-current.top)));
  return candidates.filter(x=>Math.abs(Math.abs(x.r.top-current.top)-row)<5).sort((a,b)=>Math.abs(a.r.left-current.left)-Math.abs(b.r.left-current.left))[0].i;
}
function render(){
  const entries=[...BASE,...shortcuts,{id:'add',name:'Add Shortcut',icon:'add'}];
  const root=$('shortcuts');root.style.setProperty('--columns',Math.min(6,entries.length));root.innerHTML=entries.map((item,index)=>`<button class="tile ${escapeText(item.icon||'custom')}" data-index="${index}" data-id="${escapeText(item.id)}" aria-label="${escapeText(item.name)}" title="${escapeText(item.name)}${item.icon==='custom'?' (Delete to remove)':''}"><span class="tile-square">${tileIcon(item)}</span><span class="tile-label">${escapeText(item.name)}</span></button>`).join('');
  root.querySelectorAll('.tile').forEach(tile=>{
    tile.addEventListener('click',()=>activateTile(Number(tile.dataset.index)));
    tile.addEventListener('focus',()=>{selected=Number(tile.dataset.index)});
    tile.addEventListener('contextmenu',e=>{const x=entries[Number(tile.dataset.index)];if(x.icon!=='custom')return;e.preventDefault();removeShortcut(x.id)})
  });
  root.querySelectorAll('.site-icon').forEach(img=>{
    img.addEventListener('load',()=>img.previousElementSibling.hidden=true);
    img.addEventListener('error',()=>img.remove());
  });
  selected=Math.min(selected,entries.length-1);
}

function focusTile(index){const tiles=[...document.querySelectorAll('.tile')];selected=Math.max(0,Math.min(index,tiles.length-1));tiles[selected]?.focus();tiles[selected]?.scrollIntoView({block:'nearest',inline:'nearest',behavior:'smooth'})}
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
function openAdd(){priorFocus=document.activeElement;$('add-form').reset();$('form-error').textContent='';$('add-modal').hidden=false;$('shortcut-name').focus()}
function closeAdd(){$('add-modal').hidden=true;(priorFocus&&priorFocus.isConnected?priorFocus:document.querySelector('.tile.add'))?.focus()}
function removeShortcut(id){const s=shortcuts.find(s=>s.id===id);if(!s)return; if(!window.confirm(`Remove ${s.name}?`))return;shortcuts=shortcuts.filter(x=>x.id!==id);saveShortcuts();render();focusTile(0)}
let launching=false;
async function activateTile(index){const items=[...BASE,...shortcuts,{id:'add'}];const item=items[index];if(!item)return;if(item.id==='add'){openAdd();return}if(launching)return;launching=true;
$('launch-label').textContent='Opening '+item.name;$('launching').hidden=false;
await request('/api/launch',{url:item.url,mode:item.mode||'app'});
setTimeout(()=>{$('launching').hidden=true;launching=false},900)}
function togglePower(force){const panel=$('power-panel');panel.hidden=typeof force==='boolean'?!force:!panel.hidden;if(!panel.hidden){document.querySelector('.power-item').focus()}else{$('power-toggle').focus()}}
function openConfirm(action){pendingAction=action;priorFocus=document.activeElement; $('confirm').hidden=false;$('confirm-no').focus()}
function closeConfirm(){$('confirm').hidden=true;(priorFocus?.isConnected?priorFocus:$('power-toggle')).focus()}
function onPower(action){openConfirm(action)}

$('power-toggle').addEventListener('click',()=>togglePower());
$('exit').addEventListener('click',()=>openConfirm('exit'));
$('power-panel').addEventListener('click',e=>{const btn=e.target.closest('[data-power]');if(btn)onPower(btn.dataset.power)});
$('confirm-no').addEventListener('click',closeConfirm);
$('confirm-yes').addEventListener('click',async()=>{const action=pendingAction;closeConfirm();if(action==='exit')await request('/api/exit',{});else await request('/api/power',{action})});
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
  const target=document.activeElement;
  const tiles=[...document.querySelectorAll('.tile')];
  if(target?.classList.contains('tile')){
    if(e.key==='ArrowRight'){focusTile((selected+1)%tiles.length);e.preventDefault()}
    else if(e.key==='ArrowLeft'){focusTile((selected-1+tiles.length)%tiles.length);e.preventDefault()}
    else if(e.key==='ArrowDown'){const next=rowTarget(tiles,selected,1);if(next>=0)focusTile(next);else $('exit').focus();e.preventDefault()}
    else if(e.key==='ArrowUp'){const next=rowTarget(tiles,selected,-1);if(next>=0)focusTile(next);else $('power-toggle').focus();e.preventDefault()}
  }else if(target?.id==='exit'||target?.id==='power-toggle'){
    if(e.key==='ArrowUp'){focusTile(selected);e.preventDefault()}
    else if(e.key==='ArrowLeft'){$('power-toggle').focus();e.preventDefault()}
    else if(e.key==='ArrowRight'){$('exit').focus();e.preventDefault()}
  }else if(target?.classList.contains('power-item')){
    const options=[...document.querySelectorAll('.power-item')];const idx=options.indexOf(target);
    if(e.key==='ArrowDown'){options[(idx+1)%options.length].focus();e.preventDefault()}
    else if(e.key==='ArrowUp'){options[(idx+options.length-1)%options.length].focus();e.preventDefault()}
    else if(e.key==='ArrowRight'){togglePower(false);$('exit').focus();e.preventDefault()}
  }
});

shortcuts=loadShortcuts();render();
refreshToken().catch(()=>showToast('Launcher service unavailable'));
setTimeout(()=>{$('splash').classList.add('done');setTimeout(()=>{$('splash').remove();focusTile(0)},480)},900);
