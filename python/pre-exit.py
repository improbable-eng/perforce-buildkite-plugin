"""
Entrypoint for pre-exit hook
"""
import os

from perforce import P4Repo
from buildkite import (get_env, get_config)

def main():
    """Main"""
    os.environ.update(get_env())
    config = get_config()

    repo = P4Repo(**config)
    repo.revert()

if __name__ == "__main__":
    main()
