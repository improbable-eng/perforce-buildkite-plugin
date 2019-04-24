"""
Manage a perforce workspace in the context of a build machine
"""
import re
import socket

from P4 import P4

class Repo:
    """A class for manipulating perforce workspaces"""
    def __init__(self, root=None, view=None, stream=None):
        self.root = root
        assert not (view and stream), "Stream implies view, cannot use both"
        self.stream = stream
        self.view = self._localize_view(view or [])

        self.perforce = P4()
        self.perforce.exception_level = 1  # Only errors are raised as exceptions
        self.perforce.connect()

    def _get_clientname(self):
        if self.stream:
            clientname = 'bk_%s_%s' % (socket.gethostname(), self.stream)
        else:
            clientname = 'bk_%s' % socket.gethostname()
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
        # Add a fast implementation of p4 clean here
        self._setup_client()
        self.perforce.run_clean(['-a', '-d', '//%s/...' % self._get_clientname()])

    def info(self):
        """Get server info"""
        self._setup_client()
        return self.perforce.run_info()[0]

    def sync(self):
        """Sync the workspace"""
        self._setup_client()
        return self.perforce.run_sync()
