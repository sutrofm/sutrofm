(function() {

var App = function(options) {
  this.options = options;

  _.defaults(this.options, {
    rows: 3,
    delay: 3,
    type: 'top',
    username: null
  });

  // Never load more than this many albums
  this.ALBUM_LIMIT = 500;

  this.albums = [];
  // Album lookup of key -> this.albums index
  this.albumLookup = {};
  this.init();
};

App.prototype.init = function() {
  _.bindAll(this);

  // Setup initial size and bind resize
  $(window).on('resize', this.resize);
  this.resize();

  this.content = $('#contentbkg').find('.containerbkg');

  this.getAlbums(this.startFlip);
};

// Add album to albums array if it doesn't exist already
// Return true if album was added
App.prototype.addAlbum = function(album) {
  if (!this.albumLookup[album.key]) {
    this.albumLookup[album.key] = this.albums.length;
    this.albums.push(album);
    return true;
  }
};

// Get list of albums from `get_albums` api. Keep scraping
// while incrementing `offset` until we get a response with
// no new albums. Call `k` when done loading albums.
App.prototype.getAlbums = function(k) {
  var that = this;
  // Scan collection
  function getChunk() {
    $.ajax({
      url: '/get_albums',
      data: {
        type: that.options.type,
        user: that.options.user,
        offset: that.albums.length
      },
      success: function(result) {
        var albums = result.albums;
        var added = 0;

        _.each(albums, function(album) {
          added += !!that.addAlbum(album) ? 1 : 0;
        });

        // If we added at least one album, we got new data, otherwise, we might be looping! So just get started.
        // Also, don't get more than `ALBUM_LIMIT` albums.
        if (added > 0 && that.albums.length < that.ALBUM_LIMIT) {
          getChunk();
        } else {
          k();
        }
      }
    });
  }

  getChunk();
};

App.prototype.startFlip = function() {
  this.started = true;

  if (this.finishLoadingTimeout) {
    clearTimeout(this.finishLoadingTimeout);
    this.finishLoadingTimeout = null;
  }

  // Clear out existing images
  this.content.find('.album img').unbind('load').remove();

  // Width/height of each image
  this.size = Math.ceil(window.innerHeight / this.options.rows);

  // Exact number of columns we could show
  var colCount = window.innerWidth / this.size;

  // How many columns
  this.cols = Math.round(colCount);

  // If we rounded down, add an extra album on either side
  if (this.cols < colCount) {
    this.cols += 2;
  }

  // Adjust canvas
  var leftover = this.size * (colCount - this.cols + 2);
  var adjust = this.size - Math.floor(leftover / 2);
  this.content.css({
    left: -adjust
  });

  this.grid = [];

  var contentFrag = document.createDocumentFragment();

  for (var i = 0; i < this.options.rows; i++) {
    this.grid[i] = [];
    for (var j = 0; j < this.cols; j++) {
      // Assign random album index to this grid location
      var index = this.randInt(this.albums.length);

      this.grid[i][j] = {
        albumIndex: index,
        image: $('<div class="album"></div>').css({
          top: i * this.size,
          left: j * this.size
        }).append('<img src="' + this.getAlbumArt(index) + '" width="' + this.size + '" height="' + this.size + '" />')
      };

      contentFrag.appendChild(this.grid[i][j].image[0]);
    }
  }

  this.content.html(contentFrag);

  _.bindAll(this, 'finishLoading');

  this.content.hide();

  this.finishedLoading = false;
  this.finishLoadingTimeout = setTimeout(this.finishLoading, 5000);

  // Listen for load events on images
  this.content.find('.album img').load(_.after(this.options.rows * this.cols, this.finishLoading));
};

App.prototype.finishLoading = function() {
  var that = this;

  clearTimeout(this.finishLoadingTimeout);
  this.finishLoadingTimeout = null;
  if (this.finishedLoading) {
    return;
  }
  this.finishedLoading = true;

  // Stop flipping to prevent double-flipping
  if (this.flipTimeout) {
    clearTimeout(this.flipTimeout);
    this.flipTimeout = null;
  }

  // Stop the animation in case multiple calls to startFlip
  // triggered finishLoading more than once
  this.content.stop().hide();

  // Ready to go. Fade in and start flipping.
  this.content.fadeIn(function() {
    // Set opacity to 1 again because there's a bug where
    // fadeIn ends up at a very low opacity. Maybe a race-
    // condition with the call to hide?
    that.content.css('opacity', 1.0);
    that.flipTime();
  });
};

App.prototype.getAlbumArt = function(index) {
  var icon = this.albums[index].icon;
  if (this.size > 600) {
    icon = icon.replace('200', '1200');
  } else if (this.size > 200) {
    icon = icon.replace('200', '600');
  }
  return icon;
};

App.prototype.flipTime = function() {
  var col = this.randInt(this.cols);
  var row = this.randInt(this.options.rows);
  var dir = this.randInt(2) === 1 ? 'l' : 'r';
  var newAlbumIndex = this.randInt(this.albums.length);

  var curImage = this.grid[row][col].image;
  curImage.addClass('flipping' + dir);

  var newImage = $('<div class="album flipped' + dir + '"></div>').css({
    top: row * this.size,
    left: col * this.size
  }).append('<img src="' + this.getAlbumArt(newAlbumIndex) + '" width="' + this.size + '" height="' + this.size + '" />');
  this.content.append(newImage);

  // Set reference to newly created image
  this.grid[row][col].image = newImage;

  this.cleanupTimeout = setTimeout(function() {
    newImage.removeClass('flipped' + dir);
    curImage.remove();
  }, 1000);

  this.flipTimeout = setTimeout(_.bind(this.flipTime, this), this.options.delay * 1000);
};

App.prototype.randInt = function(c) {
  return Math.floor(Math.random() * c);
};

App.prototype.resize = function() {
  var newWidth = window.innerWidth;
  var newHeight = window.innerHeight;

  if (newWidth != this.prevWidth || newHeight != this.prevHeight) {
    this.prevWidth = newWidth;
    this.prevHeight = newHeight;

    // dimensions changed, re-render (only if already rendered once)
    if (this.started) {
      this.startFlip();
    }
  }
};

App.prototype.destroy = function() {
  // coming soon...
  if (this.flipTimeout) {
    clearTimeout(this.flipTimeout);
    this.flipTimeout = null;
  }
  if (this.cleanupTimeout) {
    clearTimeout(this.cleanupTimeout);
    this.cleanupTimeout = null;
  }
  this.content.empty();
};

window.app = null;

function setupApp() {
  if (window.app) {
    window.app.destroy();
    window.app = null;
  }
  var options = {};
  var parts;
  try {
    parts = window.location.hash.substring(1).split(';');
    _.each(parts, function(part) {
      var option = part.split('=');
      options[option[0]] = option[1];
    });
  } catch (e) {
    options = {};
  }
  window.app = new App(options);
}

$(document).ready(function() {
  setupApp();
  $(window).on('hashchange', setupApp);
});

})();
