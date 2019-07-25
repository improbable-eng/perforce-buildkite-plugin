"""
Entrypoint for buildkite checkout hook
"""
import os
import argparse
import subprocess

from perforce import P4Repo
from buildkite import (get_env, get_config, get_build_revision, set_build_revision,
    get_users_changelist, get_build_changelist, set_build_changelist, set_build_info)

def main():
    """Main"""
    os.environ.update(get_env())
    config = get_config()

    repo = P4Repo(**config)

    revision = get_build_revision()
    if revision == 'HEAD':
        # Resolve HEAD to a concrete revision
        head = repo.head()
        revision = '@%s' % head
        set_build_revision(revision)

    repo.sync(revision=revision)

    if os.environ.get('BUILDKITE_CLEAN_CHECKOUT'):
        repo.clean()

    user_changelist = get_users_changelist()
    if user_changelist:
        # Use existing or make a copy of the users changelist for this build
        changelist = get_build_changelist()
        if not changelist:
            changelist = repo.backup(user_changelist)
            set_build_changelist(changelist)

        repo.unshelve(changelist)

    description = repo.description(get_users_changelist() or head)
    set_build_info(head, description)


if __name__ == "__main__":
    main()
