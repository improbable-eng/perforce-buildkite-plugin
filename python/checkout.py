"""
Entrypoint for checkout hook
"""
import os
import argparse
import subprocess

from perforce import P4Repo
from buildkite import (get_env, get_config, get_build_revision, set_build_revision,
    get_users_changelist, get_build_changelist, set_build_changelist, set_build_info,
    should_backup_changelists)

def main():
    """Main"""
    os.environ.update(get_env())
    config = get_config()

    repo = P4Repo(**config)

    revision = get_build_revision()
    if revision is None:
        revision = repo.head()
        set_build_revision(revision)

    repo.sync(revision=revision)

    user_changelist = get_users_changelist()
    if user_changelist:
        # Use existing or make a copy of the users changelist for this build
        changelist = get_build_changelist()
        if not changelist:
            changelist = user_changelist
            if should_backup_changelists():
                changelist = repo.backup(user_changelist)
            set_build_changelist(changelist)

        repo.p4print_unshelve(changelist)

    description = repo.description(
        # Prefer users change description over latest submitted change
        get_users_changelist() or repo.head_at_revision(revision)
    )
    set_build_info(revision, description)


if __name__ == "__main__":
    main()
