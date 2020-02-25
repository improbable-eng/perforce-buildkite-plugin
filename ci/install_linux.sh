#!/usr/bin/env bash
set -euxo pipefail
sudo apt-get install python-dev build-essential libssl-dev

# Install p4d (perforce server)
wget http://www.perforce.com/downloads/perforce/r18.2/bin.linux26x86_64/p4d
sudo chmod +x p4d
sudo mv p4d /usr/local/bin/p4d

# Build P4Python from source, pip install fails as we cannot connect to ftp.perforce.com from travis agents
wget http://www.perforce.com/downloads/perforce/r18.2/bin.linux26x86_64/p4api.tgz
# Detect concrete version number inside p4api.tgz, changes as new versions are published
P4API_VERSION=$(tar -tf p4api.tgz | head -1 || true)
tar xzf p4api.tgz --directory /tmp/
wget https://files.pythonhosted.org/packages/36/5a/0a1b192cdecd31cb8bc0d0ba39c73ffd84ce823053d0004823a1fdbe1440/p4python-2018.2.1743033.tar.gz
tar xfz p4python-2018.2.1743033.tar.gz --directory /tmp/
pushd /tmp/p4python-2018.2.1743033/
python setup.py install --apidir /tmp/${P4API_VERSION}
popd

# bk cli for integration tests
wget https://github.com/buildkite/cli/releases/download/v1.0.0/bk-linux-amd64-1.0.0 -O bk
sudo chmod +x bk
sudo mv bk /usr/local/bin/
# buildkite-agent for integration tests
echo "deb https://apt.buildkite.com/buildkite-agent stable main" | sudo tee /etc/apt/sources.list.d/buildkite-agent.list
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 32A37959C2FA5C3C99EFBC32A79206696452D198
sudo apt-get update
sudo apt-get install -y buildkite-agent
# Avoids hang when running integration tests (https://github.com/buildkite/cli/issues/72)
sudo chmod a+r /etc/buildkite-agent/buildkite-agent.cfg
