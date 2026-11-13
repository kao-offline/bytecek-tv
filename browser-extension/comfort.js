// A temporary dark canvas while markup arrives; do not recolor finished sites.
const loadingStyle=document.createElement('style');
loadingStyle.textContent='html{background:#242424!important;color-scheme:dark}';
function attach(){if(document.documentElement){document.documentElement.append(loadingStyle);return true}return false}
if(!attach()){
  const observer=new MutationObserver(()=>{if(attach())observer.disconnect()});
  observer.observe(document,{childList:true,subtree:true});
}
document.addEventListener('DOMContentLoaded',()=>loadingStyle.remove(),{once:true});
// Keep Spilled's imagery and video; avoid continuous animations and costly blur.
if(location.hostname==='spilled.kaooffline.top'){
  const style=document.createElement('style');
  style.textContent='*,*::before,*::after{backdrop-filter:none!important;animation-duration:0.01ms!important;animation-iteration-count:1!important;transition-duration:80ms!important;scroll-behavior:auto!important}';
  const apply=()=>document.documentElement?.append(style);
  if(document.documentElement)apply();else document.addEventListener('DOMContentLoaded',apply,{once:true});
}
