"""
Manage a perforce workspace in the context of a build machine
"""

from P4 import P4, P4Exception
import socket
import re


class Repo():
    """A class for manipulating perforce workspaces"""
    def __init__(self, root=None, view=None, stream=None):
        self.root = root
        assert not (view and stream), "Stream implies view, cannot use both"
        self.stream = stream
        self.view = self._localize_view(view or [])

        self.p4 = P4()
        self.p4.exception_level = 1  # Only errors are raised as exceptions
        self.p4.connect()

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

        def inject_client(mapping):
            depot, local = mapping.split(' ')
            return '%s //%s/%s' % (depot, clientname, local)
        return [inject_client(mapping) for mapping in view]

    def _setup_client(self):
        """Creates or re-uses the client workspace for this machine"""
        clientname = self._get_clientname()
        client = self.p4.fetch_client(clientname)
        if self.root:
            client._root = self.root
        if self.stream:
            client._stream = self.stream
        if self.view:
            client._view = self.view

        self.p4.save_client(client)

        self.p4.client = clientname

    def clean(self):
        """ Perform a p4clean on the workspace to
            remove added and restore deleted files

            Does not detect modified files
        """
        # todo: Fast implementation of p4 clean
        self._setup_client()
        self.p4.run_clean(['-a', '-d', '//%s/...' % self._get_clientname()])

    def info(self):
        self._setup_client()
        return self.p4.run_info()[0]

    def sync(self):
        self._setup_client()
        return self.p4.run_sync()
