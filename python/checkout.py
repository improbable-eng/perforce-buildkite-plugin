"""
Entrypoint for buildkite checkout hook
"""

import argparse

import perforce


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
    repo.sync()


if __name__ == "__main__":
    main()
