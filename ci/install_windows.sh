#!/usr/bin/env bash
set -euxo pipefail

# Install p4d (perforce server)
wget -q http://www.perforce.com/downloads/perforce/r18.2/bin.ntx64/p4d.exe
mv p4d.exe /c/Windows/System32/

# make for integration tests
choco install make
# bk cli for integration tests
wget -q https://github.com/buildkite/cli/releases/download/v1.1.0/bk-windows-amd64-1.1.0.exe -O bk.exe
mv bk.exe /c/Windows/System32/
# buildkite-agent for integration tests
wget -q https://github.com/buildkite/agent/releases/download/v3.25.0/buildkite-agent-windows-amd64-3.25.0.zip -O buildkite-agent.zip
unzip buildkite-agent.zip
mv buildkite-agent.exe /c/Windows/System32/
mv buildkite-agent.cfg /c/Windows/System32/

# Avoids hang when running integration tests (https://github.com/buildkite/cli/issues/72)
chmod a+r /c/Windows/System32/buildkite-agent.cfg
