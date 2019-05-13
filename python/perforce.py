"""
Manage a perforce workspace in the context of a build machine
"""
import re
import socket
import logging
import sys

from P4 import P4 # pylint: disable=import-error

class Repo:
    """A class for manipulating perforce workspaces"""
    def __init__(self, root=None, view=None, stream=None):
        """
        root: Directory in which to create the client workspace
        view: Client workspace mapping
        stream: Client workspace stream. Overrides view parameter.
        """
        self.root = root
        self.stream = stream
        self.view = self._localize_view(view or [])

        self.perforce = P4()
        self.perforce.exception_level = 1  # Only errors are raised as exceptions
        logger = logging.getLogger("P4Python")
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter('[%(asctime)s] %(name)s %(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        self.perforce.logger = logger
        self.perforce.connect()
        if self.perforce.port.startswith('ssl'):
            # TODO: Remove this and enforce prior provisioning of trusted fingerprints
            self.perforce.run_trust('-y') 

    def _get_clientname(self):
        clientname = 'bk_p4_%s' % socket.gethostname()
        return re.sub(r'\W', '_', clientname)

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
        clientname = self._get_clientname()
        client = self.perforce.fetch_client(clientname)
        if self.root:
            client._root = self.root
        if self.stream:
            client._stream = self.stream
        if self.view:
            client._view = self.view

        self.perforce.save_client(client)

        self.perforce.client = clientname

    def clean(self):
        """ Perform a p4clean on the workspace to
            remove added and restore deleted files

            Does not detect modified files
        """
        # TODO: Add a fast implementation of p4 clean here
        self._setup_client()
        self.perforce.run_clean(['-a', '-d', '//%s/...' % self._get_clientname()])

    def info(self):
        """Get server info"""
        self._setup_client()
        return self.perforce.run_info()[0]

    def head(self):
        """Get current head revision"""
        return '#%s' % self.perforce.run_counter("maxCommitChange")[0]['value']

    def sync(self, revision=None):
        """Sync the workspace"""
        self._setup_client()
        return self.perforce.run_sync('//...%s' % (revision or ''))
