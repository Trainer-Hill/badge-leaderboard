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
    fileName = `trainerhill-${id}-${dateString}.png`;
    if (!clicks || clicks == 0) { return window.dash_clientside.no_update; };

    html2canvas(document.getElementById(id), { useCORS: true }).then(function (canvas) {
      var anchorTag = document.createElement('a');
      anchorTag.download = fileName;
      anchorTag.href = canvas.toDataURL('image/png');
      anchorTag.target = '_blank';
      document.body.appendChild(anchorTag);
      anchorTag.click();
      document.body.removeChild(anchorTag);
    })
  },
}
