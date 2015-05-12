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

Let's get pip set up first. This is your package manager for python

    $ sudo easy_install pip

Install Postgres. I downloaded the PostGres app from http://postgresapp.com/

Don't forget to add the correct postgres path to $PATH. For example:

    $ PATH=$PATH:/Applications/Postgres.app/Contents/Versions/[version number]/bin/

Set up your .env file and define the keys listed above (under Develop). You'll change these later.

For TEST_DB you will need to get access to a postgres database set up. Open Postgres.app.

    $ CREATE DATABASE rdio_party;
    $ CREATE USER rp_user;
    $ ALTER USER rp_user WITH PASSWORD '1234';
    -- Check to make sure you user exists
    $ \du
    -- Quit
    $ \q

Add the following to `TEST_DB`: `'postgres://rp_user:1234@localhost/rdio_party'`

Now you're ready to pick up the requirements install

    $ sudo pip install -r requirements.txt

Go download and install the Heroku toolkit. https://devcenter.heroku.com/articles/getting-started-with-python#set-up
This will give you access to Foreman for the next couple steps.
    
Now you're ready to start where this tutorial began! 

    $ mkdir webassets
    $ sudo foreman run python manage.py collectstatic
    $ sudo foreman run python manage.py syncdb
    $ sudo foreman run python manage.py runserver
    
All done. Access your server from http://127.0.0.1:8000/
