"""
Interact with buildkite as part of plugin hooks
"""
import os
import subprocess

__ACCESS_TOKEN__ = os.environ['BUILDKITE_AGENT_ACCESS_TOKEN']
# https://github.com/buildkite/cli/blob/e8aac4bedf34cd8084a3ae7a4ab7812c611d0310/local/run.go#L403
__LOCAL_RUN__ = os.environ['BUILDKITE_AGENT_NAME'] == 'local'
__REVISION_METADATA__ = 'buildkite:perforce:revision'
__REVISION_ANNOTATION__ = "Revision: %s"


def get_build_revision():
    if not __ACCESS_TOKEN__ or __LOCAL_RUN__:
        return 'HEAD'
    # Exitcode 0 if exists, 100 if not
    if subprocess.call(['buildkite-agent', 'meta-data', 'exists', __REVISION_METADATA__]) == 0:
        return subprocess.check_output(['buildkite-agent', 'meta-data', 'get',  __REVISION_METADATA__])

    return os.environ['BUILDKITE_COMMIT'] # HEAD or user-defined value

def set_build_revision(revision):
    if not __ACCESS_TOKEN__:
        return
    # Exitcode 0 if exists, 100 if not
    if subprocess.call(['buildkite-agent', 'meta-data', 'exists', __REVISION_METADATA__]) == 100:
        subprocess.call(['buildkite-agent', 'meta-data', 'set',  __REVISION_METADATA__, revision])
        subprocess.call(['buildkite-agent', 'annotate', __REVISION_ANNOTATION__ % revision, '--context', __REVISION_METADATA__])
