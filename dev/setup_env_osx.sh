#!/bin/bash
set -eo pipefail

command -v "python3" >/dev/null 2>&1 || {
  echo >&2 "I require python3 but it's not installed. Officially supported version is 3.7.5"
  exit 1
}

readonly root="${BASH_SOURCE%/*}/.."

# Setup python virtualenv for running tests
readonly venv_dir="${root}/.dev-venv"

python3 -m pip install virtualenv
python3 -m virtualenv "${venv_dir}"

platform=$(python3 -c "import platform; print(platform.system())")
if [[ "${platform}" == "Windows" ]]; then
  venv_bin="${venv_dir}/Scripts"
else
  venv_bin="${venv_dir}/bin"
fi

"${venv_bin}/python" -m pip install -r "${root}/python/requirements.txt"
"${venv_bin}/python" -m pip install -r "${root}/ci/requirements.txt"

# Install p4d binary if missing
if ! [[ -x "$(command -v p4d)" ]]; then
  wget http://www.perforce.com/downloads/perforce/r18.2/bin.macosx1010x86_64/p4d && sudo chmod +x p4d && sudo mv p4d /usr/local/bin/p4d
fi

if ! p4d -V | grep '2018.2'; then
  echo "WARNING: Version r18.2 (2018.2) of p4d is recommended for running tests. This version may not be compatible with existing server fixture."
fi

if ! [[ -x "$(command -v bk)" ]]; then
  echo "WARNING: 'bk' cli is not installed. https://github.com/buildkite/cli"
fi
