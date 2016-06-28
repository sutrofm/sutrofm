# If we're running in Vagrant, symlink the shared directory to the standard
# sutrofm installation path
if [ -d "/vagrant" ]; then
  ln -s /vagrant /opt/sutrofm
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update --yes

# Install node on Raspbian
# wget http://node-arm.herokuapp.com/node_latest_armhf.deb
# sudo dpkg -i node_latest_armhf.deb

apt-get install curl python python-pip redis-server libmysqlclient-dev postgresql-server-dev-9.3 libpython-dev runit --yes

curl https://apt.mopidy.com/mopidy.gpg 2>/dev/null | sudo apt-key add -
curl https://apt.mopidy.com/mopidy.list 2>/dev/null > /etc/apt/sources.list.d/mopidy.list
apt-get update --yes
apt-get install mopidy mopidy-spotify --yes

cd /opt/sutrofm && ./scripts/build_templates.sh

# We're going to run these via runit, so make sure the stock init doesn't.
service mopidy stop
service redis-server stop
update-rc.d -f mopidy remove
update-rc.d -f redis-server remove

mkdir /var/log/sutrofm

mkdir /var/service
cp -Rp /opt/sutrofm/svc/* /var/service/
chown -R root:root /var/service
ln -s /var/service/* /etc/service/

cd /opt/sutrofm
mkvirtualenv sutrofm
pip install -r requirements.txt
source .env
./manage.py runserver 0.0.0.0
