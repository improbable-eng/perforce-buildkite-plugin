"""
Entrypoint for buildkite checkout hook
"""
import os
import argparse
import subprocess

from perforce import P4Repo
from buildkite import (get_env, get_config, get_build_revision, set_build_revision,
    get_users_changelist, get_build_changelist, set_build_changelist, set_build_commit)

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

    changelist = get_build_changelist()
    if not changelist:
        user_changelist = get_users_changelist()
        if user_changelist:
            # Make a copy of the users changelist for use in this build
            changelist = repo.backup(user_changelist)
            set_build_changelist(changelist)            

    if changelist:
        repo.unshelve(changelist)


if __name__ == "__main__":
    main()
