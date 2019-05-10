#!/usr/bin/env bash
set -ex
sudo apt-get install python-dev build-essential libssl-dev

wget http://www.perforce.com/downloads/perforce/r18.2/bin.linux26x86_64/p4d && sudo chmod +x p4d && sudo mv p4d /usr/local/bin/p4d

# Build P4Python from source, pip install fails as we cannot connect to ftp.perforce.com from travis agents
wget http://www.perforce.com/downloads/perforce/r18.2/bin.linux26x86_64/p4api.tgz
tar xzf p4api.tgz --directory /tmp/
wget https://files.pythonhosted.org/packages/36/5a/0a1b192cdecd31cb8bc0d0ba39c73ffd84ce823053d0004823a1fdbe1440/p4python-2018.2.1743033.tar.gz
tar xfz p4python-2018.2.1743033.tar.gz --directory /tmp/
pushd /tmp/p4python-2018.2.1743033/ && python setup.py install --apidir /tmp/p4api-2018.2.1751184 && popd