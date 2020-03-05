"""
Interact with buildkite as part of plugin hooks
"""
import os
import sys
import subprocess
import re
from datetime import datetime

__ACCESS_TOKEN__ = os.environ['BUILDKITE_AGENT_ACCESS_TOKEN']
# https://github.com/buildkite/cli/blob/e8aac4bedf34cd8084a3ae7a4ab7812c611d0310/local/run.go#L403
__LOCAL_RUN__ = os.environ['BUILDKITE_AGENT_NAME'] == 'local'

__REVISION_METADATA__ = 'buildkite-perforce-revision'
__REVISION_METADATA_DEPRECATED__ = 'buildkite:perforce:revision' # old metadata key, incompatible with `bk local run`
__SHELVED_METADATA__ = 'buildkite-perforce-shelved'
__SHELVED_ANNOTATION__ = "Saved shelved change {original} as {copy}"

def get_env():
    """Get env vars passed in via plugin config"""
    env = {
        'P4PORT': os.environ.get('P4PORT') or os.environ.get('BUILDKITE_REPO')
    }
    for p4var in ['P4PORT', 'P4USER', 'P4TICKETS', 'P4TRUST']:
        plugin_value = os.environ.get('BUILDKITE_PLUGIN_PERFORCE_%s' % p4var)
        if plugin_value:
            env[p4var] = plugin_value
    return env

def get_config():
    """Get configuration which will be passed directly to perforce.P4Repo as kwargs"""
    conf = {}
    conf['view'] = os.environ.get('BUILDKITE_PLUGIN_PERFORCE_VIEW') or '//... ...'
    conf['stream'] = os.environ.get('BUILDKITE_PLUGIN_PERFORCE_STREAM')
    conf['sync'] = os.environ.get('BUILDKITE_PLUGIN_PERFORCE_SYNC')
    conf['parallel'] = os.environ.get('BUILDKITE_PLUGIN_PERFORCE_PARALLEL') or 0
    conf['client_opts'] = os.environ.get('BUILDKITE_PLUGIN_PERFORCE_CLIENT_OPTIONS')

    if 'BUILDKITE_PLUGIN_PERFORCE_ROOT' in os.environ and not __LOCAL_RUN__:
        raise Exception("Custom P4 root is for use in unit tests only")
    conf['root'] = os.environ.get('BUILDKITE_PLUGIN_PERFORCE_ROOT') or os.environ.get('BUILDKITE_BUILD_CHECKOUT_PATH')


    # Coerce view into pairs of [depot client] paths
    view_parts = conf['view'].split(' ')
    assert (len(view_parts) % 2) == 0, "Invalid view format"
    view_iter = iter(view_parts)
    conf['view'] = ['%s %s' % (v, next(view_iter)) for v in view_iter]
    return conf

def should_backup_changelists():
    return os.environ.get('BUILDKITE_PLUGIN_PERFORCE_BACKUP_CHANGELISTS', 'false') == 'true'

def get_metadata(key):
    """If it exists, retrieve metadata from buildkite for a given key"""
    if not __ACCESS_TOKEN__:
        # Cannot get metadata outside of buildkite context
        return None

    if subprocess.call(['buildkite-agent', 'meta-data', 'exists', key]) == 0:
        return subprocess.check_output(['buildkite-agent', 'meta-data', 'get',  key]).decode(sys.stdout.encoding)

def set_metadata(key, value, overwrite=False):
    """ Set metadata in buildkite for a given key. Optionally overwrite existing data.
        Returns true if data was written
    """
    if not __ACCESS_TOKEN__ or __LOCAL_RUN__:
        # Cannot set metadata outside of buildkite context, including `bk local run`
        return False

    if overwrite or subprocess.call(['buildkite-agent', 'meta-data', 'exists', key]) == 100:
        subprocess.call(['buildkite-agent', 'meta-data', 'set',  key, value])
        return True

def get_users_changelist():
    """Get the shelved changelist supplied by the user, if applicable"""
    branch = os.environ.get('BUILDKITE_BRANCH', '')
    if branch.isdigit():
        return branch

def get_build_changelist():
    """Get a saved version of the users originally supplied changelist, if available"""
    return get_metadata(__SHELVED_METADATA__)

def set_build_changelist(changelist):
    """Set a shelved change that should be used instead of the user-supplied one"""
    if set_metadata(__SHELVED_METADATA__, changelist) and should_backup_changelists():
        subprocess.call([
            'buildkite-agent', 'annotate', 
            __SHELVED_ANNOTATION__.format(**{
                'original': get_users_changelist(),
                'copy': changelist,
            }),
            '--context', __SHELVED_METADATA__,
            '--style', 'info',
        ])

def get_build_revision():
    """Get a p4 revision for the build from buildkite context"""
    revision = get_metadata(__REVISION_METADATA__) or \
        get_metadata(__REVISION_METADATA_DEPRECATED__) or \
        os.environ['BUILDKITE_COMMIT']  # HEAD, user-defined revision or git-sha

    # Convert bare changelist number to revision specifier
    # Note: Theoretically, its possible for all 40 characters of a git sha to be digits.
    #       In practice, the inconvenience of forcing users to always include '@' outweighs this risk (~1 in 7 billion)
    if revision.isdigit():
        revision = '@%s' % revision
    # Filter to only valid revision specifiers
    if revision.startswith('@') or revision.startswith('#'):
        return revision
    # Unable to establish a concrete revision for the build
    return None 

def set_build_revision(revision):
    """Set the p4 revision for following jobs in this build"""
    set_metadata(__REVISION_METADATA__, revision)
    set_metadata(__REVISION_METADATA_DEPRECATED__, revision)

def set_build_info(revision, description):
    """Set the description and commit number in the UI for this build by mimicking a git repo"""
    revision = revision.lstrip('@#') # revision must look like a git sha for buildkite to accept it
    set_metadata('buildkite:git:commit', 'commit %s\n\n\t%s' % (revision, description))
