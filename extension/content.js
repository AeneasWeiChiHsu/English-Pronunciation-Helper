(async function(){
  const DICT_URL = chrome.runtime.getURL('base-dict.json');
  let DICT = null;
  let density = 'off';
  let observer = null;

  const st = await chrome.storage.local.get(['density']);
  density = st.density || 'off';

  async function loadDict(){
    if (DICT) return DICT;
    const r = await fetch(DICT_URL);
    DICT = (await r.json()).words;
    return DICT;
  }

  const SKIP = new Set(['SCRIPT','STYLE','NOSCRIPT','TEXTAREA','INPUT','CODE','PRE','SELECT','OPTION','KBD','SAMP']);
  function skip(node){
    let p = node.parentElement;
    while (p){
      if (SKIP.has(p.tagName)) return true;
      if (p.isContentEditable) return true;
      if (p.classList && p.classList.contains('epl-word')) return true;
      p = p.parentElement;
    }
    return false;
  }

  function form(word){
    const lo = word.toLowerCase();
    const e = DICT[lo];
    if (!e) return null;
    let m = (density === 'full') ? e.f : e.a;
    if (!m || m === lo) return null;
    if (word[0] !== word[0].toLowerCase()){          // preserve leading capital
      m = m.charAt(0).toUpperCase() + m.slice(1);
    }
    return m;
  }

  const WORD_RE = /[A-Za-z]+(?:'[A-Za-z]+)?/g;

  function processTextNode(tn){
    const text = tn.nodeValue;
    if (!text || !/[A-Za-z]/.test(text)) return;
    let m, last = 0, frag = null;
    WORD_RE.lastIndex = 0;
    while ((m = WORD_RE.exec(text))){
      const w = m[0];
      if (w.length > 1 && w === w.toUpperCase()) continue;   // skip ALL-CAPS acronyms
      const marked = form(w);
      if (!marked) continue;
      if (!frag) frag = document.createDocumentFragment();
      if (m.index > last) frag.appendChild(document.createTextNode(text.slice(last, m.index)));
      const sp = document.createElement('span');
      sp.className = 'epl-word';
      sp.title = w;                      // hover -> original spelling (peelability)
      sp.dataset.orig = w;
      sp.textContent = marked;
      frag.appendChild(sp);
      last = m.index + w.length;
    }
    if (frag){
      if (last < text.length) frag.appendChild(document.createTextNode(text.slice(last)));
      tn.parentNode.replaceChild(frag, tn);
    }
  }

  function walk(root){
    if (!root || root.nodeType !== 1) return;
    const tw = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode(n){
        return (n.nodeValue && /[A-Za-z]/.test(n.nodeValue) && !skip(n))
          ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
      }
    });
    const nodes = []; let n;
    while ((n = tw.nextNode())) nodes.push(n);
    nodes.forEach(processTextNode);
  }

  function restore(){
    document.querySelectorAll('span.epl-word').forEach(sp=>{
      sp.replaceWith(document.createTextNode(sp.dataset.orig));
    });
  }
  function rerenderExisting(){
    document.querySelectorAll('span.epl-word').forEach(sp=>{
      const w = sp.dataset.orig;
      sp.textContent = form(w) || w;
    });
  }

  function startObserver(){
    if (observer) return;
    observer = new MutationObserver(muts=>{
      for (const mu of muts){
        mu.addedNodes.forEach(node=>{
          if (node.nodeType === 1) walk(node);
          else if (node.nodeType === 3 && !skip(node)) processTextNode(node);
        });
      }
    });
    observer.observe(document.body, {childList:true, subtree:true});
  }

  async function apply(){
    if (density === 'off'){
      restore();
      if (observer){ observer.disconnect(); observer = null; }
      return;
    }
    await loadDict();
    if (document.querySelector('span.epl-word')) rerenderExisting();
    walk(document.body);
    startObserver();
  }

  chrome.storage.onChanged.addListener((ch, area)=>{
    if (area === 'local' && ch.density){ density = ch.density.newValue; apply(); }
  });

  // Alt+click a word -> log it for review (outlier crowdsourcing by the user)
  document.addEventListener('click', async (e)=>{
    if (!e.altKey) return;
    const sel = (window.getSelection().toString() || '').trim();
    const word = sel || (e.target && e.target.dataset && e.target.dataset.orig) || '';
    if (!word) return;
    const r = await chrome.storage.local.get(['reports']);
    const reports = r.reports || [];
    reports.push({word, url: location.href, t: Date.now()});
    await chrome.storage.local.set({reports});
    e.preventDefault();
  }, true);

  if (density !== 'off') apply();
})();
