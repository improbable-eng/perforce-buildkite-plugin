"""
Entrypoint for buildkite checkout hook
"""
import os
import argparse
import subprocess

from perforce import P4Repo
from buildkite import (get_env, get_config, get_build_revision, set_build_revision,
    get_saved_shelved_change, get_users_shelved_change, set_saved_shelved_change)

def main():
    """Main"""
    os.environ.update(get_env())
    config = get_config()

    repo = P4Repo(**config)

    revision = get_build_revision()
    if revision == 'HEAD':
        # Resolve HEAD to a concrete revision
        revision = repo.head()
        set_build_revision(revision)

    repo.sync(revision=revision)

    if os.environ.get('BUILDKITE_CLEAN_CHECKOUT'):
        repo.clean()

    changelist = get_saved_shelved_change()
    if not changelist:
        changelist = get_users_shelved_change()
        if changelist:
            # Save a copy of the current shelved content
            # This avoids jobs syncing to different versions of the same shelf
            changelist = repo.backup(changelist)
            set_saved_shelved_change(changelist)

    if changelist:
        repo.unshelve(changelist)


if __name__ == "__main__":
    main()
