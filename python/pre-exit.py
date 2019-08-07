"""
Entrypoint for pre-exit hook
"""
import os

from perforce import P4Repo
from buildkite import get_env, get_config

def main():
    """Perform any last-second cleanup regardless of success or failure"""
    os.environ.update(get_env())
    config = get_config()

    repo = P4Repo(**config)

    repo.revert()
