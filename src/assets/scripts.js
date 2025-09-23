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
