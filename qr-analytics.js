// Generated from qr/registry.json. No individual tracking or storage.
(() => {
  const allowed = {"ad": "paid", "card": "print", "fair": "offline", "manual": "print", "pkg": "print"};
  window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };
  window.va('beforeSend', (event) => {
    try {
      const url = new URL(event.url);
      if (url.origin !== 'https://grovillant.com' || url.pathname !== '/') return null;
      const campaign = url.searchParams.get('utm_campaign');
      const medium = url.searchParams.get('utm_medium');
      const valid = url.searchParams.get('utm_source') === 'qr' &&
        Object.prototype.hasOwnProperty.call(allowed, campaign) && allowed[campaign] === medium &&
        ['utm_source', 'utm_medium', 'utm_campaign'].every(k => url.searchParams.getAll(k).length === 1);
      url.search = ''; url.hash = '';
      if (valid) {
        url.searchParams.set('utm_source', 'qr');
        url.searchParams.set('utm_medium', medium);
        url.searchParams.set('utm_campaign', campaign);
      }
      return { ...event, url: url.toString() };
    } catch (_) { return null; }
  });
})();
