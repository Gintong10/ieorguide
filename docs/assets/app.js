(() => {
  const q = document.getElementById('q'), jump = document.getElementById('jump'), count = document.getElementById('count'), none = document.getElementById('none');
  const stages = [...document.querySelectorAll('.stage')];
  const root = document.documentElement, srcs = document.getElementById('srcs');
  // the filter reads item names only, plus the source lines while those are switched on
  const text = li => { if (!li._n) { const c = li.cloneNode(true); li._a = c.textContent.toLowerCase(); c.querySelectorAll('.src').forEach(e => e.remove()); li._n = c.textContent.toLowerCase(); } return root.classList.contains('show-src') ? li._a : li._n; };
  let rerun = () => {};
  if (srcs) {
    const set = on => { root.classList.toggle('show-src', on); srcs.checked = on; rerun(); };
    let saved = false; try { saved = localStorage.getItem('ieor-src') === '1'; } catch (e) {}
    set(saved || new URLSearchParams(location.search).get('sources') === '1');
    srcs.addEventListener('change', () => { set(srcs.checked); try { localStorage.setItem('ieor-src', srcs.checked ? '1' : '0'); } catch (e) {} });
    const place = it => { const s = it.querySelector('.src'); if (!s || root.classList.contains('show-src')) return; s.style.left = '0px'; const r = it.getBoundingClientRect(), w = s.offsetWidth; if (w) s.style.left = Math.round(Math.min(Math.max(r.left - 10, 8), innerWidth - w - 8) - r.left) + 'px'; };
    document.addEventListener('pointerover', e => { const it = e.target.closest && e.target.closest('.it.has'); if (it) place(it); });
    document.addEventListener('click', e => { const it = e.target.closest('.it.has'); for (const o of document.querySelectorAll('.it.open')) if (o !== it) o.classList.remove('open'); if (it && !e.target.closest('.src')) { it.classList.toggle('open'); place(it); } });
  }
  if (q) {
    const run = () => {
      const t = q.value.trim().toLowerCase(); let shown = 0, hits = 0;
      for (const s of stages) {
        let any = !t;
        for (const li of s.querySelectorAll('.chips li')) { const h = !!t && text(li).includes(t); li.classList.toggle('hit', h); if (h) { any = true; hits++; } }
        if (t && !any) any = [...s.querySelectorAll('.prose, h3')].some(e => e.textContent.toLowerCase().includes(t));
        s.hidden = !any; if (any) shown++;
      }
      for (const h of document.querySelectorAll('h2.era')) { let n = h.nextElementSibling, vis = false; while (n && !n.matches('h2.era')) { if (n.matches('.stage') && !n.hidden) vis = true; n = n.nextElementSibling; } h.hidden = !vis; }
      count.textContent = t ? `${hits} item${hits === 1 ? '' : 's'} in ${shown} stage${shown === 1 ? '' : 's'}` : '';
      none.hidden = !!shown;
    };
    q.addEventListener('input', run); rerun = run;
    const p = new URLSearchParams(location.search).get('q'); if (p) { q.value = p; run(); }
  }
  if (jump) jump.addEventListener('change', () => { if (jump.value) { location.hash = jump.value; jump.value = ''; } });
  const links = [...document.querySelectorAll('.side a.s-stage')];
  if (links.length && 'IntersectionObserver' in window) {
    const byId = Object.fromEntries(links.map(a => [a.hash.slice(1), a]));
    const io = new IntersectionObserver(es => { for (const e of es) if (e.isIntersecting) { links.forEach(a => a.classList.remove('on')); const a = byId[e.target.id]; if (a) { a.classList.add('on'); a.scrollIntoView({ block: 'nearest' }); } } }, { rootMargin: '-80px 0px -70% 0px' });
    stages.forEach(s => io.observe(s));
  }
  const carry = () => { const h = /^#stage-\d+$/.test(location.hash) ? location.hash : ''; for (const a of document.querySelectorAll('.nav a[data-stages]')) a.href = a.dataset.base + h; };
  if (stages.length) { addEventListener('hashchange', carry); carry(); }
})();
