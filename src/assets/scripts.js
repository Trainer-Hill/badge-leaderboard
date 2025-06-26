if (!window.dash_clientside) {
  window.dash_clientside = {};
}

window.dash_clientside.clientside = {
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

  disableAddButton: function (trainer, pronoun, deck, store, date) {
    if (!trainer || !pronoun || !deck || !store || !date) {
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
  }
}  