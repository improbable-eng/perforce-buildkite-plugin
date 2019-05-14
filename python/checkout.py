"""
Entrypoint for buildkite checkout hook
"""
import os
import argparse
import subprocess

import perforce

__ACCESS_TOKEN__ = os.environ['BUILDKITE_AGENT_ACCESS_TOKEN']
__REVISION_METADATA__ = 'buildkite:perforce:revision'
__REVISION_ANNOTATION__ = "Revision: %s"

def get_build_revision():
    if not __ACCESS_TOKEN__:
        return None
    # Exitcode 0 if exists, 100 if not
    if subprocess.call(['buildkite-agent', 'meta-data', 'exists', __REVISION_METADATA__]) == 0:
        return subprocess.check_output(['buildkite-agent', 'meta-data', 'get',  __REVISION_METADATA__])
    return None

def set_build_revision(revision):
    if not __ACCESS_TOKEN__:
        return
    # Exitcode 0 if exists, 100 if not
    if subprocess.call(['buildkite-agent', 'meta-data', 'exists', __REVISION_METADATA__]) == 100:
        subprocess.call(['buildkite-agent', 'meta-data', 'set',  __REVISION_METADATA__, revision])
        subprocess.call(['buildkite-agent', 'annotate', __REVISION_ANNOTATION__ % revision, '--context', __REVISION_METADATA__])

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

    repo = perforce.Repo(root=args.root, stream=args.stream, view=view)

    revision = get_build_revision()
    if not revision: # No revision set, must be our responsibility.
        if os.environ['BUILDKITE_COMMIT'] == 'HEAD':
            revision = repo.head()
        else:
            revision = os.environ['BUILDKITE_COMMIT']
        set_build_revision(revision)

    repo.sync(revision=revision)

if __name__ == "__main__":
    main()
