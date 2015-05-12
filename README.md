# Rdio Party

Shared listening rooms powered by [Rdio](http://www.rdio.com/).

## Develop

Create a `.env` file with the following defined:

    AWS_ACCESS_KEY_ID=
    AWS_SECRET_ACCESS_KEY=
    DJANGO_DEBUG=true
    DJANGO_SECRET_KEY=
    FIREBASE_TOKEN=
    RDIO_OAUTH2_KEY=
    RDIO_OAUTH2_SECRET=
    SENTRY_DSN=
    TEST_DB=

Setup and run locally:

    $ pip install -r requirements.txt
    $ mkdir webassets
    $ foreman run python manage.py collectstatic
    $ foreman run python manage.py syncdb
    $ foreman run python manage.py runserver

## Deploy

Before first deploy:

    $ heroku apps:create <app_name>
    $ heroku addons:add heroku-postgresql:dev
    $ heroku addons:add sentry:developer
    $ heroku config:set <contents of .env>

First deploy:

    $ foreman run python manage.py collectstatic
    $ git push heroku master
    $ heroku run python manage.py syncdb
    $ heroku ps:scale web=1

For each deployment thereafter:

    $ foreman run python manage.py collectstatic
    $ git push heroku master

## First-time users

Have no idea what all this means? Don't worry. I'm going to run you through the process I used to get this set up for the first time on OS X.

You will be getting Python, Django, Postgres, and some Heroku tools set up during this process. 

Before you get started, you will need to set up some additional services. 

__Rdio js API__

This is different from the web services API. You will need to request access. Once you've been granted access, go create an app at http://www.rdio.com/developers/ and add `RDIO_OAUTH2_KEY` and `RDIO_OAUTH2_SECRET` to your `.env` file.

__FireBase__

Go create an account (free) at https://www.firebase.com/. This will be your realtime service. Once you've logged in, go to your app (https://[name]-[id].firebaseio.com/) and select "secrets". Add your firebase secret to `FIREBASE_TOKEN` in the `.env` file.

__Django Secret__

Go create your django secret key here: http://www.miniwebtool.com/django-secret-key-generator/ and add it to `DJANGO_SECRET_KEY` in the `.env` file.

__Python__

Let's get pip set up first. This is your package manager for python

    $ sudo easy_install pip

__Postgres__

Install Postgres. I downloaded the PostGres app from http://postgresapp.com/

Don't forget to add the correct postgres path to $PATH. For example:

    $ PATH=$PATH:/Applications/Postgres.app/Contents/Versions/[version number]/bin/

For TEST_DB you will need to get access to a postgres database set up. Open Postgres.app.

    $ CREATE DATABASE rdio_party;
    $ CREATE USER rp_user;
    $ ALTER USER rp_user WITH PASSWORD '1234';
    -- Check to make sure you user exists
    $ \du
    -- Quit
    $ \q

Add the following to `TEST_DB`: `'postgres://rp_user:1234@localhost/rdio_party'` in your `.env` file.

__Requirements__

Now you're ready to pick up the requirements install

    $ sudo pip install -r requirements.txt

Go download and install the Heroku toolkit. https://devcenter.heroku.com/articles/getting-started-with-python#set-up
This will give you access to Foreman for the next couple steps.

A few modifications to `settings.py` are required to get things set up locally. 

* Add `127.0.0.1` to `ALLOWED_HOSTS`.
* Change `FIREBASE_URL` to use your new firebase instance.

__The Environment__

Now you're ready to start where this tutorial began! 

    $ mkdir webassets
    $ sudo foreman run python manage.py collectstatic
    $ sudo foreman run python manage.py syncdb
    $ sudo foreman run python manage.py runserver
    
All done. Access your server from http://127.0.0.1:8000/
