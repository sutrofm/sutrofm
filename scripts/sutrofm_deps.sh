# If we're running in Vagrant, symlink the shared directory to the standard
# sutrofm installation path
if [ -d "/vagrant" ]; then
  ln -s /vagrant /opt/sutrofm
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update --yes

apt-get install curl python python-pip redis-server libmysqlclient-dev postgresql-server-dev-9.3 libpython-dev runit ruby --yes

curl https://apt.mopidy.com/mopidy.gpg 2>/dev/null | sudo apt-key add -
curl https://apt.mopidy.com/mopidy.list 2>/dev/null > /etc/apt/sources.list.d/mopidy.list
apt-get update --yes
apt-get install mopidy mopidy-spotify --yes

mkdir /var/log/sutrofm

apt-get install ruby
gem install foreman

pip install virtualenvwrapper

mkvirtualenv sutrofm
workon sutrofm
cd /opt/sutrofm

pip install -r requirements.txt
. .env
foreman run ./manage.py runserver 0.0.0.0
