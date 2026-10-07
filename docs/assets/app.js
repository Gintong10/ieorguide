(() => {
  const q = document.getElementById('q'), jump = document.getElementById('jump'), count = document.getElementById('count'), none = document.getElementById('none');
  const stages = [...document.querySelectorAll('.stage')];
  if (q) {
    const run = () => {
      const t = q.value.trim().toLowerCase(); let shown = 0, hits = 0;
      for (const s of stages) {
        let any = !t;
        for (const li of s.querySelectorAll('.chips li')) { const h = !!t && li.textContent.toLowerCase().includes(t); li.classList.toggle('hit', h); if (h) { any = true; hits++; } }
        if (t && !any) any = [...s.querySelectorAll('.prose, h3')].some(e => e.textContent.toLowerCase().includes(t));
        s.hidden = !any; if (any) shown++;
      }
      for (const h of document.querySelectorAll('h2.era')) { let n = h.nextElementSibling, vis = false; while (n && !n.matches('h2.era')) { if (n.matches('.stage') && !n.hidden) vis = true; n = n.nextElementSibling; } h.hidden = !vis; }
      count.textContent = t ? `${hits} item${hits === 1 ? '' : 's'} in ${shown} stage${shown === 1 ? '' : 's'}` : '';
      none.hidden = !!shown;
    };
    q.addEventListener('input', run);
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
