(() => {
  // iPhone/iPad: Safari opens a .vcf served as text/vcard straight into the
  // "Create New Contact" sheet. The download attribute would instead send it to
  // the Downloads list, so drop it there. Android and desktop keep it.
  const isIOS = /iP(hone|od|ad)/.test(navigator.userAgent) ||
    (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1);
  if (isIOS) document.querySelectorAll('a[download]').forEach(a => a.removeAttribute('download'));

  const toast = document.querySelector('.toast');
  let timer;
  const say = msg => {
    toast.textContent = msg;
    toast.classList.add('show');
    clearTimeout(timer);
    timer = setTimeout(() => toast.classList.remove('show'), 2200);
  };

  const copy = async text => {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      const field = document.createElement('textarea');
      field.value = text;
      field.setAttribute('readonly', '');
      field.style.cssText = 'position:fixed;opacity:0';
      document.body.append(field);
      field.select();
      const ok = document.execCommand('copy');
      field.remove();
      return ok;
    }
  };

  document.querySelector('[data-share]')?.addEventListener('click', async () => {
    const data = {
      title: 'Naveena Neerada Dasa · World Food Movement & The Akshaya Patra Foundation',
      text: 'Naveena Neerada Dasa, Executive Director. Tap to save my contact.',
      url: location.href.split('#')[0],
    };
    if (navigator.share) {
      try { await navigator.share(data); return; }
      catch (err) { if (err.name === 'AbortError') return; }
    }
    say(await copy(data.url) ? 'Link copied' : 'Copy failed. Please copy the address bar.');
  });
})();
