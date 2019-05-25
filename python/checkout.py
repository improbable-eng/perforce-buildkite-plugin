"""
Entrypoint for buildkite checkout hook
"""
import os
import argparse
import subprocess

from perforce import P4Repo
from buildkite import get_env, get_config, get_build_revision, set_build_revision


def main():
    """Main"""
    os.environ.update(get_env())
    config = get_config()

    repo = P4Repo(**config)

    revision = get_build_revision()
    if revision == 'HEAD':
        revision = repo.head()
        set_build_revision(revision)

    repo.sync(revision=revision)


if __name__ == "__main__":
    main()
