(() => {
  const nav = document.querySelector('.reading-nav');
  if (!nav) return;
  const toggle = nav.querySelector('.nav-toggle');
  const status = nav.querySelector('.nav-status');
  const links = Array.from(nav.querySelectorAll('.nav-links a'));
  const sections = links.map(link => document.querySelector(link.getAttribute('href')));
  function close() {
    nav.classList.remove('is-open');
    toggle.setAttribute('aria-expanded', 'false');
    toggle.setAttribute('aria-label', '展开章节目录');
    toggle.textContent = '目录';
  }
  toggle.addEventListener('click', () => {
    const open = nav.classList.toggle('is-open');
    toggle.setAttribute('aria-expanded', String(open));
    toggle.setAttribute('aria-label', open ? '收起章节目录' : '展开章节目录');
    toggle.textContent = open ? '收起目录' : '目录';
  });
  links.forEach(link => link.addEventListener('click', close));
  document.addEventListener('click', event => { if (!nav.contains(event.target)) close(); });
  document.addEventListener('keydown', event => { if (event.key === 'Escape') close(); });
  let scheduled = false;
  function update() {
    const marker = window.scrollY + Math.min(200, window.innerHeight * .35);
    let active = 0;
    sections.forEach((section, index) => {
      if (section && section.getBoundingClientRect().top + window.scrollY <= marker) active = index;
    });
    if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 8) {
      active = sections.length - 1;
    }
    links.forEach((link, index) => {
      link.classList.toggle('is-active', index === active);
      link.classList.toggle('is-passed', index < active);
      if (index === active) link.setAttribute('aria-current', 'location');
      else link.removeAttribute('aria-current');
    });
    status.textContent = `${active + 1} / ${sections.length}`;
    status.setAttribute('aria-label', `当前阅读第 ${active + 1} 节，共 ${sections.length} 节`);
    scheduled = false;
  }
  function schedule() {
    if (scheduled) return;
    scheduled = true;
    requestAnimationFrame(update);
  }
  window.addEventListener('scroll', schedule, { passive: true });
  window.addEventListener('resize', schedule);
  schedule();
})();
