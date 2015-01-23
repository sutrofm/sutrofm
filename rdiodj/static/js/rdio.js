// Depends on cache.js
(function() {
  Rdio = {
    // Load cached response or call Rdio api to get new data
    // Caches according to method and content
    get: function(method, content, k) {
      var that = this;

      if (!method) {
        return;
      }

      content = content || {};

      var contentStr = '';
      _.each(_.keys(content).sort(), function(key) {
        contentStr += key + content[key];
      });

      var cacheKey = method + '::' + contentStr;

      var cachedResponse = Cache.get(cacheKey);
      if (cachedResponse) {
        k(cachedResponse);
      } else {
        R.ready(function() {
          R.request({
            method: method,
            content: content,
            success: function(response) {
              Cache.put(cacheKey, response);
              k(response);
            }
          });
        });
      }
    }
  };
})();
