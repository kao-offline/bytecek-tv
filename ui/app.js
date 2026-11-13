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
  spilled: `<svg viewBox="0 0 100 100" aria-hidden="true"><path fill="#e12929" d="M30 14c-6-4-13 0-13 8v56c0 8 7 12 13 8l54-28c8-4 8-12 0-16z"/></svg>`,
  ct24: `<svg viewBox="0 0 110 90" aria-hidden="true"><path fill="#101c49" d="M4 31q0-9 9-9h19v12H19v26h13v12H13q-9 0-9-9z"/><path fill="#e12929" d="M35 22h20q8 0 8 9v32q0 9-8 9H35V60h14V34H35z"/><text x="69" y="61" font-family="Arial" font-size="36" font-weight="700" fill="#101c49">24</text></svg>`,
  chrome: `<svg viewBox="0 0 100 100" aria-hidden="true"><clipPath id="c"><circle cx="50" cy="50" r="45"/></clipPath><g clip-path="url(#c)"><circle cx="50" cy="50" r="45" fill="#e43e32"/><path d="M50 50H103L76 98H37z" fill="#f7c52c"/><path d="M50 50 25 6 -8 50 28 105z" fill="#289e51"/><path d="M50 50H101L83 17H30z" fill="#e43e32"/></g><circle cx="50" cy="50" r="23" fill="white"/><circle cx="50" cy="50" r="19" fill="#2384d4"/></svg>`,
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

function render(){
  const entries=[...BASE,...shortcuts,{id:'add',name:'Add Shortcut',icon:'add'}];
  const root=$('shortcuts');root.innerHTML=entries.map((item,index)=>`<button class="tile ${escapeText(item.icon||'custom')}" data-index="${index}" data-id="${escapeText(item.id)}" aria-label="${escapeText(item.name)}" title="${escapeText(item.name)}${item.icon==='custom'?' (Delete to remove)':''}"><span class="tile-square">${ICONS[item.icon]||ICONS.custom}</span><span class="tile-label">${escapeText(item.name)}</span></button>`).join('');
  root.querySelectorAll('.tile').forEach(tile=>{
    tile.addEventListener('click',()=>activateTile(Number(tile.dataset.index)));
    tile.addEventListener('focus',()=>{selected=Number(tile.dataset.index)});
    tile.addEventListener('contextmenu',e=>{const x=entries[Number(tile.dataset.index)];if(x.icon!=='custom')return;e.preventDefault();removeShortcut(x.id)})
  });
  selected=Math.min(selected,entries.length-1);
}

function focusTile(index){const tiles=[...document.querySelectorAll('.tile')];selected=Math.max(0,Math.min(index,tiles.length-1));tiles[selected]?.focus();tiles[selected]?.scrollIntoView({block:'nearest',inline:'nearest',behavior:'smooth'})}
async function request(path,payload){
  if(!apiToken){showToast('Launcher service is unavailable');return null}
  try{
    const res=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json','X-Bytecek-Token':apiToken},body:JSON.stringify(payload)});
    const data=await res.json();if(!res.ok)throw Error(data.error||'Request failed');return data;
  }catch(e){showToast(e.message);return null}
}
function openAdd(){priorFocus=document.activeElement;$('add-form').reset();$('form-error').textContent='';$('add-modal').hidden=false;$('shortcut-name').focus()}
function closeAdd(){$('add-modal').hidden=true;(priorFocus&&priorFocus.isConnected?priorFocus:document.querySelector('.tile.add'))?.focus()}
function removeShortcut(id){const s=shortcuts.find(s=>s.id===id);if(!s)return; if(!window.confirm(`Remove ${s.name}?`))return;shortcuts=shortcuts.filter(x=>x.id!==id);saveShortcuts();render();focusTile(0)}
function activateTile(index){const items=[...BASE,...shortcuts,{id:'add'}];const item=items[index];if(!item)return;if(item.id==='add'){openAdd();return}request('/api/launch',{url:item.url,mode:item.mode||'app'})}
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
    else if(e.key==='ArrowDown'){$('exit').focus();e.preventDefault()}
    else if(e.key==='ArrowUp'){$('power-toggle').focus();e.preventDefault()}
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
fetch('/api/config').then(r=>r.json()).then(data=>{apiToken=data.token}).catch(()=>showToast('Launcher service unavailable'));
setTimeout(()=>{$('splash').classList.add('done');setTimeout(()=>{$('splash').remove();focusTile(0)},480)},900);
