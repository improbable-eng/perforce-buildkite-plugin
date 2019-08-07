"""
Entrypoint for checkout hook
"""
import os
import argparse
import subprocess
import re

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
    if revision == 'HEAD':
        # Resolve HEAD to a concrete revision
        revision = repo.head()
        set_build_revision(revision)

    # Convert changelist number to revision specifier
    if re.match(r'^\d*$', revision):
        revision = '@%s' % revision

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

        repo.unshelve(changelist)

    revision = get_build_revision()
    description = repo.description(get_users_changelist() or revision.strip('@'))
    set_build_info(revision, description)


if __name__ == "__main__":
    main()
