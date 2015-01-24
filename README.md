# Rdio DJ

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
