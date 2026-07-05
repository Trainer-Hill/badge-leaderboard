if (!window.dash_clientside) {
  window.dash_clientside = {};
}

window.dash_clientside.clientside = {
  toggleWithButton: function (clicks, isOpen) {
    if (clicks > 0) {
      return !isOpen;
    }
    return isOpen;
  },

  updatePageFluidity: function (path) {
    return path === '/badges';
  },

  navigateSeason: function (value) {
    if (value === undefined || value === null) {
      return window.dash_clientside.no_update;
    }
    const url = new URL(window.location.href);
    if (String(url.searchParams.get('season')) === String(value)) {
      return window.dash_clientside.no_update;
    }
    url.searchParams.set('season', value);
    window.location.assign(url.href);
    return window.dash_clientside.no_update;
  },

  initSeasonSelect: function (pathname) {
    const season = new URL(window.location.href).searchParams.get('season');
    if (!season) {
      return window.dash_clientside.no_update;
    }
    return season === 'overall' ? 'overall' : Number(season);
  },

  // Carry the active ?season= across internal navigation. A single delegated
  // capture-phase click listener rewrites internal link hrefs to include the
  // current season, so buttons/links don't reset the season to the default.
  installSeasonLinkPersistence: function (pathname) {
    if (window.__seasonLinkPersistence) {
      return window.dash_clientside.no_update;
    }
    window.__seasonLinkPersistence = true;
    document.addEventListener('click', function (e) {
      const anchor = e.target.closest && e.target.closest('a[href]');
      if (!anchor) { return; }
      const href = anchor.getAttribute('href');
      // Skip in-page anchors (e.g. "#season") so hash jumps don't reload.
      if (!href || href.charAt(0) === '#') { return; }
      // Skip links opening in a new tab/window.
      const target = anchor.getAttribute('target');
      if (target && target !== '_self') { return; }
      const current = new URL(window.location.href).searchParams.get('season');
      if (!current) { return; }
      let url;
      try { url = new URL(href, window.location.origin); } catch (err) { return; }
      if (url.origin !== window.location.origin) { return; }  // external
      if (url.searchParams.has('season')) { return; }         // already scoped
      url.searchParams.set('season', current);
      anchor.setAttribute('href', url.pathname + url.search + url.hash);
    }, true);
    return window.dash_clientside.no_update;
  },

  customRadioEnableAdd: function (input, options) {
    if (input === undefined) { console.log('returning'); return true; }
    if (input.length === 0) { return true; }
    return options.includes(input);
  },

  addToOptionsAndSelect: function (clicks, input, options) {
    if (clicks > 0) {
      const newOptions = options.concat(input);
      return [newOptions, input];
    }
    return [window.dash_clientside.no_update, window.dash_clientside.no_update];
  },

  disableAddButton: function (trainer, pronoun, deck, store, date, color, background, tier, format) {
    if (!trainer || !pronoun || !deck || !store || !date || (color === '#ffffff') || !background || !tier || !format) {
      return true;
    }
    return false;
  },

  disableDeckAdd: function(name, icons, store) {
    if (!name || !icons || icons.length === 0) {
      return true;
    }
    if (name.toLowerCase().replace(/ /g, '') in store) {
      return true;
    }
    return false;
  },

  downloadDomAsImage: async function (clicks, id) {
    const today = new Date();
    const dateString = today.toISOString().substring(0, 10);
    const fileName = `trainerhill-${id}-${dateString}.png`;
    if (!clicks || clicks == 0) { return window.dash_clientside.no_update; };
    const isIOS = /iP(ad|hone|od)/i.test(window.navigator.userAgent);
    let newWindow = null;
    if (isIOS) {
      // Pre-open a blank tab during the user-initiated event to avoid popup blockers
      newWindow = window.open('', '_blank');
    }
    html2canvas(document.getElementById(id), { useCORS: true }).then(function (canvas) {
      const imgData = canvas.toDataURL('image/png');
      if (isIOS && newWindow) {
        const img = newWindow.document.createElement('img');
        img.src = imgData;
        img.alt = fileName;
        newWindow.document.body.style.margin = '0';
        newWindow.document.body.appendChild(img);
      } else {
        var anchorTag = document.createElement('a');
        anchorTag.download = fileName;
        anchorTag.href = imgData;
        anchorTag.target = '_blank';
        document.body.appendChild(anchorTag);
        anchorTag.click();
        document.body.removeChild(anchorTag);
      }
    })
  },
}
