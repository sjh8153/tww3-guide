(() => {
  const root = document.body.dataset.root || '';
  const modal = document.querySelector('[data-search-modal]');
  const input = document.querySelector('[data-search-input]');
  const results = document.querySelector('[data-search-results]');
  let index = [];
  let loaded = false;

  async function ensureIndex(){
    if (loaded) return;
    try { index = await fetch(root + 'search-index.json').then(r=>r.json()); loaded = true; }
    catch(e){ results.innerHTML = '<div class="search-result"><b>검색 색인을 불러오지 못했습니다.</b><span>정적 서버에서 열었는지 확인하세요.</span></div>'; }
  }
  function escapeHtml(s){return s.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]))}
  function search(q){
    q = q.trim().toLowerCase();
    if (!q){ results.innerHTML = '<div class="search-result"><span>검색어를 입력하면 전체 공략에서 찾아드립니다.</span></div>'; return; }
    const terms = q.split(/\s+/);
    const scored = index.map(x=>{
      const hay = `${x.title} ${x.label} ${x.description} ${(x.headings||[]).join(' ')} ${x.content_text}`.toLowerCase();
      let score = 0;
      for (const t of terms){
        if (!hay.includes(t)) return null;
        if (x.title.toLowerCase().includes(t)) score += 8;
        if (x.label.toLowerCase().includes(t)) score += 6;
        if ((x.headings||[]).join(' ').toLowerCase().includes(t)) score += 4;
        score += 1;
      }
      return {x,score};
    }).filter(Boolean).sort((a,b)=>b.score-a.score).slice(0,20);
    results.innerHTML = scored.length ? scored.map(({x})=>`<a class="search-result" href="${root + x.url}"><small>${escapeHtml(x.faction_name)} · ${escapeHtml(x.label)}</small><b>${escapeHtml(x.title)}</b><span>${escapeHtml(x.excerpt)}</span></a>`).join('') : '<div class="search-result"><b>검색 결과 없음</b><span>다른 단어로 검색해보세요.</span></div>';
  }
  async function openSearch(){
    modal.hidden = false; document.body.style.overflow='hidden';
    await ensureIndex(); setTimeout(()=>input.focus(),0); search(input.value);
  }
  function closeSearch(){ modal.hidden=true; document.body.style.overflow=''; }
  document.querySelectorAll('[data-search-open]').forEach(b=>b.addEventListener('click',openSearch));
  document.querySelector('[data-search-close]')?.addEventListener('click',closeSearch);
  input?.addEventListener('input',e=>search(e.target.value));
  modal?.addEventListener('click',e=>{if(e.target===modal)closeSearch()});
  document.addEventListener('keydown',e=>{
    if(e.key==='/' && !['INPUT','TEXTAREA'].includes(document.activeElement.tagName)){e.preventDefault();openSearch()}
    if(e.key==='Escape' && !modal.hidden) closeSearch();
  });
  const nav = document.querySelector('[data-sidebar]');
  document.querySelector('[data-nav-toggle]')?.addEventListener('click',()=>nav.classList.toggle('open'));
})();
