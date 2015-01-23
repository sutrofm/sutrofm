(function() {
  var DEFAULT_LIFETIME = 60000;
  // TODO: when this is updated, add the old version to a list that is checked and expunged if that storage bin exists locally.
  var CACHE_VERSION = 1.0;

  var Cache = function() {
    // Check sanity of cache (create bin if necessary)
    // Set up interval to clear old items
    this._bin = 'af_' + CACHE_VERSION;
  };

  // Get an item from the cache and return it. If it's older than it's lifetime, return undefined.
  Cache.prototype.get = function(key) {
    if (!window.localStorage || !window.localStorage[this._bin]) {
      return;
    }

    var bin;
    try {
      bin = JSON.parse(window.localStorage[this._bin]);
    } catch(e) {
      return;
    }

    var cacheItem = bin[key];
    if (cacheItem) {
      var curTime = (new Date()).getTime();
      if (cacheItem.t + cacheItem.l > curTime) {
        return cacheItem.v;
      }
    }
  };

  // Add an item to the cache which will expire in "lifetime" milliseconds
  Cache.prototype.put = function(key, value, lifetime) {
    lifetime = lifetime || DEFAULT_LIFETIME;
    if (!window.localStorage) {
      return;
    }

    var bin = window.localStorage[this._bin];
    if (!bin) {
      bin = {};
    } else {
      try {
        // TODO: Fix this, it has side-effects
        // if the item can be parsed, but is not a dictionary, the following code will work fine but it will stringify without any of the values you want to save!
        bin = JSON.parse(window.localStorage[this._bin]);
      } catch(e) {
        // fatal error, kill storage and start over
        console.error('local storage problem, killing cache');
        bin = {};
      }
    }

    var newItem = {
      v: value,
      l: lifetime,
      t: (new Date()).getTime()
    };

    bin[key] = newItem;

    window.localStorage[this._bin] = JSON.stringify(bin);
  };

  window.Cache = new Cache();
})();
