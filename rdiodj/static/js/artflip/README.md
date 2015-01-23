artflip
=======

It's like the iTunes album art screensaver, but for Rdio.

Try it out
----------

artflip is running on github at [http://endenizen.net/artflip](http://endenizen.net/artflip)

Screensaver
-----------

You may be thinking, "of course, this is all fine but it's not much of a screensaver!" Alas, you are correct, for this is a mere web app that runs in a mere web browser. So I have created a companion project, [ArtFlipSaver](https://github.com/endenizen/ArtFlipSaver) which loads the hosted version of this app in a webview. It also includes some handy options like customizing the number of rows, delay, and album art source (collection, heavy rotation, etc).

Install the screensaver here: [https://dl.dropbox.com/u/120686/ArtFlipSaver.saver.zip](https://dl.dropbox.com/u/120686/ArtFlipSaver.saver.zip)

How does it work?
-----------------

The app is written almost entirely in javascript which requests the data, arranges the images and juggles css classes which perform the actual flipping using webkit css transitions. The 'options' from the screensaver are passed in the url like so:

    http://endenizen.net/artflip/#user=endenizen;type=top;rows=3;delay=3

Installation
------------

artflip has no requirements. You can serve it on any webserver that serves static files, like github! When developing, I use something like the following:

    python -m SimpleHTTPServer 5000

Which will make the app available on:

    http://localhost:5000

