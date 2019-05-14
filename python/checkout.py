"""
Entrypoint for buildkite checkout hook
"""
import os
import argparse
import subprocess

from perforce import P4Repo
from buildkite import get_build_revision, set_build_revision


def main():
    """Main"""
    parser = argparse.ArgumentParser(
        description='Checkout a perforce repository')
    parser.add_argument('--port', action='store', help='perforce port')
    parser.add_argument('--user', action='store', help='perforce user')
    parser.add_argument('--stream', action='store', help='stream to sync')
    parser.add_argument('--view', nargs='+', action='store',
                        help='workspace mapping to sync (instead of stream). '
                             'use the format: "//depot/dev/... dev"')
    parser.add_argument('--root', action='store', help='client workspace root')
    args = parser.parse_args()

    # Coerce view from ['//depot/...', '...'] to ['//depot/... ...']
    assert (len(args.view) % 2) == 0, "Invalid view format"
    view_iter = iter(args.view)
    view = ['%s %s' % (v, next(view_iter)) for v in view_iter]

    repo = P4Repo(root=args.root, stream=args.stream, view=view)

    revision = get_build_revision()
    if revision == 'HEAD':
        revision = repo.head()
        set_build_revision(revision)

    repo.sync(revision=revision)

if __name__ == "__main__":
    main()
