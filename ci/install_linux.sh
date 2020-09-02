#!/usr/bin/env bash
set -euxo pipefail
sudo apt-get install python-dev build-essential libssl-dev

# Install p4d (perforce server)
wget http://www.perforce.com/downloads/perforce/r18.2/bin.linux26x86_64/p4d
sudo chmod +x p4d
sudo mv p4d /usr/local/bin/p4d

# Build P4Python from source, pip install fails as we cannot connect to ftp.perforce.com from travis agents
wget http://www.perforce.com/downloads/perforce/r20.1/bin.linux26x86_64/p4api.tgz
# Detect concrete version number inside p4api.tgz, changes as new versions are published
P4API_VERSION=$(tar -tf p4api.tgz | head -1 || true)
tar xzf p4api.tgz --directory /tmp/
# link from https://pypi.org/project/p4python/#files
wget https://files.pythonhosted.org/packages/bb/91/972c574beb614fc6c7666f5a1cb7ffa1deb9ca440382d44c96715f3ebfeb/p4python-2020.1.1983437.tar.gz
tar xfz p4python-2020.1.1983437.tar.gz --directory /tmp/
pushd /tmp/p4python-2020.1.1983437/
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
