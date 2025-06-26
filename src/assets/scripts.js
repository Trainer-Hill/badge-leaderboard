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
  }
}  