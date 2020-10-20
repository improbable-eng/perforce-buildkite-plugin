"""
Entrypoint for checkout hook
"""
import os
import argparse
import subprocess

from perforce import P4Repo
from buildkite import (get_env, get_config, get_build_revision, set_build_revision,
    get_users_changelist, set_build_info)

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
        repo.p4print_unshelve(user_changelist)

    description = repo.description(
        # Prefer users change description over latest submitted change
        user_changelist or repo.head_at_revision(revision)
    )
    set_build_info(revision, description)


if __name__ == "__main__":
    main()
