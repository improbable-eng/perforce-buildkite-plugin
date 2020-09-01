"""
Manage a perforce workspace in the context of a build machine
"""
import os
import re
import socket
import logging
import sys
import stat
import json


# Recommended reference: https://www.perforce.com/manuals/p4python/p4python.pdf
from P4 import P4, P4Exception, OutputHandler # pylint: disable=import-error

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
        self.patchfile = os.path.join(self.root, 'patched.json')
        self.p4config = os.path.join(self.root, 'p4config')

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
        """Get unique clientname for this host and location on disk"""
        clientname = 'bk-p4-%s-%s' % (os.environ.get('BUILDKITE_AGENT_NAME', socket.gethostname()), os.path.basename(self.root))
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
        # must be set prior to running any commands to avoid issues with default client names
        self.perforce.client = clientname
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

        self.perforce.save_client(client)

        if not os.path.isfile(self.p4config):
            self.perforce.logger.warning("p4config missing, flushing workspace to revision zero")
            self.perforce.run_flush(['//...@0'])
        else:
            with open(self.p4config) as infile:
                prev_clientname = next(line.split('=', 1)[-1]
                    for line in infile.read().splitlines() # removes \n
                    if line.startswith('P4CLIENT='))
                if prev_clientname != clientname:
                    self.perforce.logger.warning("p4config last client was %s, flushing workspace to match" % prev_clientname)
                    self.perforce.run_flush(['//...@%s' % prev_clientname])

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
        with open(self.p4config, 'w') as p4config:
            p4config.writelines(["%s=%s\n" % (k, v) for k, v in config.items()])

    def _read_patched(self):
        """Read a marker to find which files have been modified in the workspace"""
        if not os.path.exists(self.patchfile):
            return []
        with open(self.patchfile, 'r') as infile:
            return json.load(infile)

    def _write_patched(self, files):
        """Write a marker to track which files have been modified in the workspace"""
        content = list(set(files + self._read_patched())) # Combine and deduplicate
        with open(self.patchfile, 'w') as outfile:
            json.dump(content, outfile)

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
        self._setup_client()
        # Get head based on client view (e.g. within the stream)
        client_head = self.head_at_revision('//%s/...' % self._get_clientname())
        if client_head:
            return '@' + client_head
        # Fallback for when client view has no submitted changes, global head revision
        return '@' + self.perforce.run_counter("maxCommitChange")[0]['value']

    def head_at_revision(self, revision):
        """Get head submitted changelist at revision specifier"""
        # Resolve revision specifier like "@labelname" to a concrete submitted change
        result = self.perforce.run_changes([
            '-m', '1', '-s', 'submitted', revision
        ])
        if not result:
            return None # Revision spec had no submitted changes
        return result[0]['change']

    def description(self, changelist):
        """Get description of a given changelist number"""
        return self.perforce.run_describe(str(changelist))[0]['desc']

    def sync(self, revision=None):
        """Sync the workspace"""
        self._setup_client()
        self.revert()
        result = self.perforce.run_sync(
            '--parallel=threads=%s' % self.parallel,
            '%s%s' % (self.sync_paths, revision or ''),
            handler=SyncOutput(self.perforce.logger),
        )
        if result:
            self.perforce.logger.info("Synced %s files (%s)" % (
                result[0]['totalFileCount'], sizeof_fmt(int(result[0]['totalFileSize']))))
        return result

    def revert(self):
        """Revert any pending changes in the workspace"""
        self._setup_client()
        self.perforce.run_revert('-w', '//...')
        patched = self._read_patched()
        if patched:
            self.perforce.run_clean(patched)
            os.remove(self.patchfile)

    def unshelve(self, changelist):
        """Unshelve a pending change"""
        self._setup_client()

        changeinfo = self.perforce.run_describe('-S', changelist)
        if not changeinfo:
            raise Exception('Changelist %s does not contain any shelved files.' % changelist)
        changeinfo = changeinfo[0]

        # Reject exclusive lock files for now
        modifiers = [filetype.split('+')[1]
                     for filetype in changeinfo['type']
                     if '+' in filetype]
        if any('l' in modifier for modifier in modifiers):
            raise Exception(
                'You cannot run a presubmit test with exclusive lock files (+l) at this time\n'
                'See https://github.com/ca-johnson/perforce-buildkite-plugin/issues/102 for latest status\n')


        self.perforce.run_unshelve('-s', changelist)

    def run_parallel_cmds(self, cmds, max_parallel=20):
        def run(*args):
            """Acquire new connection and run p4 cmd"""
            perforce = P4()
            perforce.exception_level = self.perforce.exception_level
            perforce.logger = self.perforce.logger
            perforce.connect()
            perforce.run(*args)

        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=max_parallel) as executor:
            executor.map(run, cmds)

    def p4print_unshelve(self, changelist):
        """Unshelve a pending change by p4printing the contents into a file"""
        self._setup_client()

        changeinfo = self.perforce.run_describe('-S', changelist)
        if not changeinfo:
            raise Exception('Changelist %s does not contain any shelved files.' % changelist)
        changeinfo = changeinfo[0]

        depotfiles = changeinfo['depotFile']

        whereinfo = self.perforce.run_where(depotfiles)
        depot_to_local = {item['depotFile']: item['path'] for item in whereinfo}
        
        # Flag these files as modified
        self._write_patched(list(depot_to_local.values()))

        # Turn sync spec info a prefix to filter out unwanted files
        # e.g. //my-depot/dir/... => //my-depot/dir/
        sync_prefix = self.sync_paths.rstrip('.')

        cmds = []
        for depotfile, localfile in depot_to_local.items():
            if os.path.isfile(localfile):
                os.chmod(localfile, stat.S_IWRITE)
                os.unlink(localfile)
            if depotfile.startswith(sync_prefix):
                cmds.append(('print', '-o', localfile, '%s@=%s' % (depotfile, changelist)))

        self.run_parallel_cmds(cmds)

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


class SyncOutput(OutputHandler):
    """Log each synced file"""
    def __init__(self, logger):
        OutputHandler.__init__(self)
        self.logger = logger
        self.sync_count = 0
    
    def outputStat(self, stat):
        if 'depotFile' in stat:
            self.sync_count  += 1
            if self.sync_count < 1000:
                # Normal, verbose logging of synced file
                self.logger.info("%(depotFile)s#%(rev)s %(action)s" % stat)
            elif self.sync_count % 1000 == 0:
                # Syncing many files, print one message for every 1000 files to reduce log spam
                self.logger.info("Synced %d files..." % self.sync_count)
        return OutputHandler.REPORT


def sizeof_fmt(num, suffix='B'):
    """Format bytes to human readable value"""
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Pi', suffix)
