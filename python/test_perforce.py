"""
Test perforce module for managing workspaces
"""
from contextlib import closing
from functools import partial
from threading import Thread
import os
import shutil
import socket
import subprocess
import tempfile
import time
import zipfile

import perforce

# Time after which the p4 server will automatically be shut-down.
__P4D_TIMEOUT__ = 30
# __P4D_TIMEOUT__ = None


def find_free_port():
    """Find an open port that we could run a perforce server on"""
    # pylint: disable=no-member
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(('', 0))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return sock.getsockname()[1]


def run_p4d(p4port, from_zip=None):
    """Start a perforce server with the given hostname:port.
       Optionally unzip server state from a file
    """
    prefix = 'bk-p4d-test-'
    parent = tempfile.gettempdir()
    for item in os.listdir(parent):
        if item.startswith(prefix):
            try:
                shutil.rmtree(os.path.join(parent, item))
            except Exception: # pylint: disable=broad-except
                print("Failed to remove", item)

    tmpdir = tempfile.mkdtemp(prefix=prefix)
    if from_zip:
        zip_path = os.path.join(os.path.dirname(__file__), 'fixture', from_zip)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(tmpdir)
    subprocess.run(["p4d", "-r", tmpdir, "-p", str(p4port)],
                   timeout=__P4D_TIMEOUT__)


def setup_server(from_zip=None):
    """Start a p4 server in the background and return the address"""
    port = find_free_port()
    Thread(target=partial(run_p4d, port, from_zip=from_zip), daemon=True).start()
    time.sleep(1)
    p4port = 'localhost:%s' % port
    os.environ['P4PORT'] = p4port
    return p4port


def _test_harness():
    """Check that tests can start and connect to a local perforce server"""
    port = setup_server(from_zip='server.zip')
    repo = perforce.Repo()
    assert repo.info()['serverAddress'] == port

    # There should be a sample file checked into the fixture server
    # Returns [metadata, contents]
    content = repo.perforce.run_print("//depot/file.txt")[1]
    assert content == "Hello World\n"


def test_checkout():
    """Test normal flow of checking out files, running p4 clean"""
    setup_server(from_zip='server.zip')

    with tempfile.TemporaryDirectory(prefix="bk-p4-test-") as client_root:
        repo = perforce.Repo(root=client_root)

        assert os.listdir(client_root) == [], "Workspace should be empty"
        repo.sync()
        assert os.listdir(client_root) == [
            "file.txt"], "Workspace file wasn't synced"

        os.remove(os.path.join(client_root, "file.txt"))
        open(os.path.join(client_root, "added.txt"), 'a').close()
        assert os.listdir(client_root) == [
            "added.txt"], "Workspace files in unexpected state prior to clean"
        repo.clean()
        assert os.listdir(client_root) == [
            "file.txt"], "Failed to restore workspace file"

# def test_bad_configs():
#     perforce.Repo('port', stream='stream', view=['view'])
#     perforce.Repo('port', view=['bad_view'])
