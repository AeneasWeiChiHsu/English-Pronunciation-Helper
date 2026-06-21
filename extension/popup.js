async function refresh(){
  const {density='off', reports=[]} = await chrome.storage.local.get(['density','reports']);
  document.querySelectorAll('button[data-d]').forEach(b=>b.classList.toggle('on', b.dataset.d===density));
  document.getElementById('rc').textContent = `已回報 ${reports.length} 字`;
}
document.querySelectorAll('button[data-d]').forEach(b=>{
  b.addEventListener('click', async ()=>{ await chrome.storage.local.set({density:b.dataset.d}); refresh(); });
});
document.getElementById('exp').addEventListener('click', async ()=>{
  const {reports=[]} = await chrome.storage.local.get(['reports']);
  const blob = new Blob([JSON.stringify(reports,null,2)],{type:'application/json'});
  const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='epl-reports.json'; a.click();
});
fetch(chrome.runtime.getURL('base-dict.json')).then(r=>r.json()).then(j=>{
  document.getElementById('ver').textContent='ruleVersion '+j.version+' · '+j.n+' words';
});
refresh();
