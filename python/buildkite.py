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
__BUILDKITE_AGENT__ = os.environ.get('BUILDKITE_BIN_PATH', 'buildkite-agent')

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
    conf['root'] = os.environ.get('BUILDKITE_PLUGIN_PERFORCE_ROOT') or os.environ.get('BUILDKITE_BUILD_CHECKOUT_PATH')
    conf['view'] = os.environ.get('BUILDKITE_PLUGIN_PERFORCE_VIEW') or '//... ...'
    conf['stream'] = os.environ.get('BUILDKITE_PLUGIN_PERFORCE_STREAM')
    conf['parallel'] = os.environ.get('BUILDKITE_PLUGIN_PERFORCE_PARALLEL') or 0

    # Coerce view into pairs of [depot client] paths
    view_parts = conf['view'].split(' ')
    assert (len(view_parts) % 2) == 0, "Invalid view format"
    view_iter = iter(view_parts)
    conf['view'] = ['%s %s' % (v, next(view_iter)) for v in view_iter]
    return conf

def get_shelved_change():
    """Get a shelved changelist that will be patched into each workspace"""
    branch = os.environ.get('BUILDKITE_BRANCH', '')
    if branch.isdigit():
        return branch
    return None

def get_metadata(key):
    """If it exists, retrieve metadata from buildkite for a given key"""
    if subprocess.call([__BUILDKITE_AGENT__, 'meta-data', 'exists', key]) == 0:
        return subprocess.check_output([__BUILDKITE_AGENT__, 'meta-data', 'get',  key])

def set_metadata(key, value, overwrite=False):
    """ Set metadata in buildkite for a given key. Optionally overwrite existing data.
        Returns true if data was written
    """
    if overwrite or subprocess.call([__BUILDKITE_AGENT__, 'meta-data', 'exists', key]) == 100:
        subprocess.call([__BUILDKITE_AGENT__, 'meta-data', 'set',  key, value])
        return True

def get_build_revision():
    """Get a p4 revision for the build to sync to"""
    if not __ACCESS_TOKEN__ or __LOCAL_RUN__:
        return 'HEAD'

    return get_metadata(__REVISION_METADATA__) or os.environ['BUILDKITE_COMMIT'] # metadata, HEAD or user-defined value

def set_build_revision(revision):
    """Set the p4 revision for following jobs in this build"""
    if not __ACCESS_TOKEN__ or __LOCAL_RUN__:
        return
    if set_metadata(__REVISION_METADATA__, revision):
        subprocess.call([__BUILDKITE_AGENT__, 'annotate', __REVISION_ANNOTATION__ % revision, '--context', __REVISION_METADATA__])
