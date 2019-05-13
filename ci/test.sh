#!/usr/bin/env bash
set -ex

python3 -m pylint python --errors-only
python3 -m pytest