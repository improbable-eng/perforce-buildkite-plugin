#!/usr/bin/env bash
set -euxo pipefail
sudo apt-get install python-dev build-essential libssl-dev

# Install p4d (perforce server)
wget http://www.perforce.com/downloads/perforce/r18.2/bin.linux26x86_64/p4d
sudo chmod +x p4d
sudo mv p4d /usr/local/bin/p4d

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
