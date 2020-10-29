#!/usr/bin/env bash
set -euxo pipefail

# Install p4d (perforce server)
wget http://www.perforce.com/downloads/perforce/r18.2/bin.macosx1010x86_64/p4d
sudo chmod +x p4d
sudo mv p4d /usr/local/bin/p4d

# bk cli for integration tests
wget https://github.com/buildkite/cli/releases/download/v1.0.0/bk-darwin-amd64-1.0.0 -O bk
sudo chmod +x bk
sudo mv bk /usr/local/bin/
# buildkite-agent for integration tests
brew install buildkite/buildkite/buildkite-agent
# Avoids hang when running integration tests (https://github.com/buildkite/cli/issues/72)
sudo chmod a+r "$(brew --prefix)"/etc/buildkite-agent/buildkite-agent.cfg
