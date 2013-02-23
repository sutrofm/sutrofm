# Rdio DJ

Shared listening rooms with via Rdio.

## Develop

Create a `.env` file with the following defined:

    AWS_ACCESS_KEY_ID=
    AWS_SECRET_ACCESS_KEY=
    DJANGO_DEBUG=true
    DJANGO_SECRET_KEY=
    RDIO_OAUTH2_KEY=
    RDIO_OAUTH2_SECRET=

Setup and run locally:

    $ pip install -r requirements.txt
    $ foreman run python manage.py syncdb
    $ foreman run python manage.py runserver

## Deploy

Before first deploy:

    $ heroku apps:create <app_name>
    $ heroku addons:add heroku-postgresql:dev
    $ heroku config:set <contents of .env>

First deploy:

    $ git push heroku master
    $ heroku run python manage.py syncdb
    $ heroku ps:scale web=1

For each deployment thereafter:

    $ foreman run python manage.py collectstatic
    $ git push heroku master
