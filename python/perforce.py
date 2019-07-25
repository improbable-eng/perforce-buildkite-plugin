"""
Manage a perforce workspace in the context of a build machine
"""
import os
import re
import socket
import logging
import sys


# Recommended reference: https://www.perforce.com/manuals/p4python/p4python.pdf
from P4 import P4, P4Exception, Progress  # pylint: disable=import-error

class P4Repo:
    """A class for manipulating perforce workspaces"""
    def __init__(self, root=None, view=None, stream=None,
                 sync=None, client_opts=None, parallel=0):
        """
        root: Directory in which to create the client workspace
        view: Client workspace mapping
        stream: Client workspace stream. Overrides view parameter.
        """
        self.root = os.path.abspath(root or '')
        self.stream = stream
        self.view = self._localize_view(view or [])
        self.sync_paths = sync or '//...'
        self.client_opts = client_opts or ''
        self.parallel = parallel

        self.created_client = False

        self.perforce = P4()
        self.perforce.exception_level = 1  # Only errors are raised as exceptions
        logger = logging.getLogger("p4python")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s %(name)s %(levelname)s: %(message)s',
            '%H:%M:%S',
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        self.perforce.logger = logger
        self.perforce.connect()
        if self.perforce.port.startswith('ssl'):
            # TODO: Remove this and enforce prior provisioning of trusted fingerprints
            self.perforce.run_trust('-y')

    def __del__(self):
        self.perforce.disconnect()

    def _get_clientname(self):
        clientname = 'bk-p4-%s' % os.environ.get('BUILDKITE_AGENT_NAME', socket.gethostname())
        return re.sub(r'\W', '-', clientname)

    def _localize_view(self, view):
        """Convert path mapping to be a client workspace view"""
        if not isinstance(view, list):
            view = [view]
        clientname = self._get_clientname()

        def insert_clientname(mapping):
            """Insert client name into path mapping"""
            depot, local = mapping.split(' ')
            return '%s //%s/%s' % (depot, clientname, local)
        return [insert_clientname(mapping) for mapping in view]

    def _setup_client(self):
        """Creates or re-uses the client workspace for this machine"""
        # pylint: disable=protected-access
        if self.created_client:
            return
        clientname = self._get_clientname()
        client = self.perforce.fetch_client(clientname)
        if self.root:
            client._root = self.root
        if self.stream:
            client._stream = self.stream
        if self.view:
            client._view = self.view

        # unless overidden, overwrite writeable-but-unopened files
        # (e.g. interrupted syncs, artefacts that have been checked-in)
        client._options = self.client_opts + ' clobber'

        if not os.path.isfile(os.path.join(self.root, "p4config")):
            self.perforce.logger.warn("p4config was missing, creating a fresh workspace")
            try:
                self.perforce.delete_client(clientname)
            except P4Exception as exc:
                # Suppress 'Client doesn't exist' messages
                if not "doesn't exist" in str(exc):
                    raise

        self.perforce.save_client(client)

        self.perforce.client = clientname
        self._write_p4config()
        self.created_client = True

    def _write_p4config(self):
        """Writes a p4config at the workspace root"""
        config = {
            'P4CLIENT': self.perforce.client,
            'P4USER': self.perforce.user,
            'P4PORT': self.perforce.port
        }
        if not os.path.exists(self.root):
            os.makedirs(self.root)
        with open(os.path.join(self.root, "p4config"), 'w') as p4config:
            p4config.writelines(["%s=%s\n" % (k, v) for k, v in config.items()])

    def clean(self):
        """ Perform a p4clean on the workspace to
            remove added and restore deleted files

            Does not detect modified files
        """
        self._setup_client()
        # TODO: Add a fast implementation of p4 clean here
        self.perforce.run_clean(['-a', '-d', '//%s/...' % self._get_clientname()])
        self._write_p4config()

    def info(self):
        """Get server info"""
        return self.perforce.run_info()[0]

    def head(self):
        """Get current head revision"""
        return self.perforce.run_counter("maxCommitChange")[0]['value']

    def description(self, changelist):
        """Get description of a given changelist"""
        return self.perforce.run_describe(str(changelist))[0]['desc']

    def sync(self, revision=None):
        """Sync the workspace"""
        self._setup_client()
        self.revert()
        result = self.perforce.run_sync(
            '-q', '--parallel=threads=%s' % self.parallel,
            '%s%s' % (self.sync_paths, revision or ''),
            progress=SyncProgress(self.perforce.logger))
        if result:
            self.perforce.logger.info("Synced %s files (%s)" % (
                result[0]['totalFileCount'], sizeof_fmt(int(result[0]['totalFileSize']))))
        return result

    def revert(self):
        """Revert any pending changes in the workspace"""
        self._setup_client()
        self.perforce.run_revert('//...')

    def unshelve(self, changelist):
        """Unshelve a pending change"""
        self._setup_client()
        self.perforce.run_unshelve('-s', changelist)

    def backup(self, changelist):
        """Make a copy of a shelved change"""
        self.revert()
        self.unshelve(changelist)
        # Make pending CL from default CL
        unshelved = self.perforce.fetch_change()
        unshelved._description = 'Backup of %s for precommit testing in Buildkite' % changelist
        self.perforce.save_change(unshelved)
        backup_change_info = self.perforce.run_changes('-c', self.perforce.client, '-s', 'pending', '-m', '1')
        backup_cl = backup_change_info[0]['change']
        self.perforce.run_shelve('-c', backup_cl)
        return backup_cl


class SyncProgress(Progress):
    """Log the number of synced files periodically"""
    def __init__(self, logger):
        Progress.__init__(self)
        self.logger = logger
    
    def init(self, type):
        Progress.init(self, type)
    
    def setDescription(self, description, units):
        Progress.setDescription(self, description, units)
    
    def setTotal(self, total):
        Progress.setTotal(self, total)
    
    def update(self, position):
        Progress.update(self, position)
        self.logger.info('Syncing file #%s...' % position)
    
    def done(self, fail):
        Progress.done(self, fail)

def sizeof_fmt(num, suffix='B'):
    """Format bytes to human readable value"""
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Pi', suffix)