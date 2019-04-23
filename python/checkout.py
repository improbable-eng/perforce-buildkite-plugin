import argparse

import perforce


def main():
    parser = argparse.ArgumentParser(description='Checkout a perforce repository')
    parser.add_argument('--port', action='store', help='perforce port')
    parser.add_argument('--user', action='store', help='perforce user')
    parser.add_argument('--stream', action='store', help='stream to sync')
    parser.add_argument('--view', nargs='+', action='store', help='workspace mapping to sync (instead of stream). Use the format: "//depot/dev/... dev"')
    parser.add_argument('--root', action='store', help='client workspace root')
    args = parser.parse_args()

    repo = perforce.Repo(root=args.root, stream=args.stream, view=args.view)
    repo.sync()

if __name__ == "__main__":
    main()