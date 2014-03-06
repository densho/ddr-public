# ddr-public install script

PACKAGE_SERVER=tank.densho.org

BOOTSTRAP=bootstrap-3.0.3.zip
JQUERY=jquery-1.10.2.min.js
ELASTICSEARCH=elasticsearch-1.0.1.deb
ASSETS=ddr-public-assets.tar.gz


# text color variables
txtund=$(tput sgr 0 1)   # underline
txtbld=$(tput bold)      # bold
red=$(tput setaf 1)      # red
grn=$(tput setaf 2)      # green
blu=$(tput setaf 4)      # blue
wht=$(tput setaf 7)      # white
bldred=${txtbld}${red}   # red
bldgrn=${txtbld}${grn}   # green
bldblu=${txtbld}${blu}   # blue
bldwht=${txtbld}${wht}   # white
txtrst=$(tput sgr0)      # reset
info=${bldwht}*${txtrst} # feedback
pass=${bldblu}*${txtrst}
warn=${bldred}*${txtrst}
ques=${bldblu}?${txtrst}


git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit


echo "${bldgrn}Creating ddr user${txtrst}"
adduser ddr
adduser ddr vboxsf


echo "${bldgrn}Package update${txtrst}"
apt-get --assume-yes update


echo "${bldgrn}Installing miscellaneous tools${txtrst}"
apt-get --assume-yes install ack-grep byobu bzip2 curl elinks gdebi-core htop logrotate mg multitail p7zip-full wget


echo "${bldgrn}www server${txtrst}"
apt-get --assume-yes install nginx


echo "${bldgrn}cache server${txtrst}"
apt-get --assume-yes install redis-server


echo "${bldgrn}search engine${txtrst}"
apt-get --assume-yes install openjdk-6-jre
wget -nc -P /tmp/downloads http://$PACKAGE_SERVER/$ELASTICSEARCH
gdebi --non-interactive /tmp/downloads/$ELASTICSEARCH


echo "${bldgrn}ddr-lint${txtrst}"
apt-get --assume-yes install libxml2 libxml2-dev libxslt1-dev
cd /usr/local/src
git clone https://github.com/densho/ddr-lint.git
cd /usr/local/src/ddr-lint/ddrlint
python setup.py install
pip install -r /usr/local/src/ddr-lint/ddrlint/requirements/production.tx
chown -R root.ddr /usr/local/src/ddr-lint


echo "${bldgrn}ddr-cmdln${txtrst}"
apt-get --assume-yes install libxml2-dev libxslt1-dev python-dev python-pip
cd /usr/local/src
git clone https://github.com/densho/ddr-cmdln.git
cd /usr/local/src/ddr-cmdln/ddr
python setup.py install
pip install -r /usr/local/src/ddr-cmdln/ddr/requirements/production.txt
chown -R root.ddr /usr/local/src/ddr-cmdln


echo "${bldgrn}ddr-local${txtrst}"
cd /usr/local/src
git clone https://github.com/densho/ddr-local.git
chown -R root.ddr /usr/local/src/ddr-local


echo "${bldgrn}ddr-public${txtrst}"
apt-get --assume-yes install imagemagick supervisor
cd /usr/local/src
git clone https://github.com/densho/ddr-public.git
cd /usr/local/src/ddr-public/ddrpublic
pip install -U -r /usr/local/src/ddr-public/ddrpublic/requirements/production.txt
chown -R root.ddr /usr/local/src/ddr-public
chmod +x /usr/local/src/ddr-public/ddrpublic/manage.py


echo "${bldgrn}creating directories${txtrst}"
mkdir /etc/ddr
mkdir /var/log/ddr
mkdir /var/lib/ddr
mkdir /var/www
mkdir /var/www/media
mkdir /var/www/media/cache
mkdir /var/www/static
mkdir /var/www/static/js
chown -R ddr /var/log/ddr/
chown -R ddr /var/lib/ddr/
chown -R ddr /var/www/media


echo "${bldgrn}Setting secret key${txtrst}"
python -c 'import random; print "".join([random.choice("abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)") for i in range(50)])' > /etc/ddr/ddrpublic-secret-key.txt
chown ddr.ddr /etc/ddr/ddrpublic-secret-key.txt
chmod 600 /etc/ddr/ddrpublic-secret-key.txt


echo "${bldgrn}Bootstrap${txtrst}"
rm /var/www/static/$BOOTSTRAP*
wget -nc -P /var/www/static http://$PACKAGE_SERVER/$BOOTSTRAP
7z x -y -o/var/www/static /var/www/static/$BOOTSTRAP


echo "${bldgrn}jQuery${txtrst}"
wget -nc -P /var/www/static/js http://$PACKAGE_SERVER/$JQUERY
ln -s /var/www/static/js/$JQUERY /var/www/static/js/jquery.js


echo "${bldgrn}ddr-public assets${txtrst}"
wget -nc -P /tmp http://$PACKAGE_SERVER/$ASSETS
tar xzvf /tmp/ddr-public-assets.tar.gz -C /var/www/


echo "${bldgrn}configuration files${txtrst}"
cp /usr/local/src/ddr-local/debian/conf/ddr.cfg /etc/ddr/
chown root.root /etc/ddr/ddr.cfg
chmod 644 /etc/ddr/ddr.cfg

cp /usr/local/src/ddr-public/debian/conf/elasticsearch.yml /etc/elasticsearch/
chown root.root /etc/elasticsearch/elasticsearch.yml
chmod 644 /etc/elasticsearch/elasticsearch.yml
/etc/init.d/elasticsearch restart

cp /usr/local/src/ddr-public/debian/conf/settings.py /usr/local/src/ddr-public/ddrpublic/ddrpublic/
chown root.root /usr/local/src/ddr-public/ddrpublic/ddrpublic/settings.py
chmod 644 /usr/local/src/ddr-public/ddrpublic/ddrpublic/settings.py

cp /usr/local/src/ddr-public/debian/conf/supervisord.conf /etc/supervisor/
cp /usr/local/src/ddr-public/debian/conf/gunicorn_ddrpublic.conf /etc/supervisor/conf.d/
chown root.root /etc/supervisor/conf.d/gunicorn_ddrpublic.conf
chmod 644 /etc/supervisor/conf.d/gunicorn_ddrpublic.conf
/etc/init.d/supervisor restart

cp /usr/local/src/ddr-public/debian/conf/ddrpublic.conf /etc/nginx/sites-available
rm /etc/nginx/sites-enabled/ddrpublic.conf
ln -s /etc/nginx/sites-available/ddrpublic.conf /etc/nginx/sites-enabled
rm /etc/nginx/sites-enabled/default
/etc/init.d/nginx restart
