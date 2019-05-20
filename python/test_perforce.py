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

from perforce import P4Repo

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
    try:
        subprocess.check_output(["p4d", "-r", tmpdir, "-p", str(p4port)],
                                timeout=__P4D_TIMEOUT__)
    except subprocess.TimeoutExpired:
        pass

def setup_server(from_zip=None):
    """Start a p4 server in the background and return the address"""
    port = find_free_port()
    Thread(target=partial(run_p4d, port, from_zip=from_zip), daemon=True).start()
    time.sleep(1)
    p4port = 'localhost:%s' % port
    os.environ['P4PORT'] = p4port
    return p4port

def store_server(repo, to_zip):
    """Zip up a server to use as a unit test fixture"""
    serverRoot = repo.info()['serverRoot']

    zip_path = os.path.join(os.path.dirname(__file__), 'fixture', to_zip)
    with zipfile.ZipFile(zip_path, 'w') as archive:
        for root, _, files in os.walk(serverRoot):
            for filename in files:
                abs_path = os.path.join(root, filename)
                archive.write(abs_path, os.path.relpath(abs_path, serverRoot))

def test_fixture():
    """Check that tests can start and connect to a local perforce server"""
    port = setup_server(from_zip='server.zip')
    repo = P4Repo()
    assert repo.info()['serverAddress'] == port

    # There should be a sample file checked into the fixture server
    # Returns [metadata, contents]
    content = repo.perforce.run_print("//depot/file.txt")[1]
    assert content == "Hello World\n"
    assert repo.head() == "@2", "Unexpected head revision"

    # To change the fixture server, uncomment the next line and put a breakpoint on it.
    # Make changes to the p4 server then check in the new server.zip
    # store_server(repo, 'new_server.zip')

def test_checkout():
    """Test normal flow of checking out files"""
    setup_server(from_zip='server.zip')

    with tempfile.TemporaryDirectory(prefix="bk-p4-test-") as client_root:
        repo = P4Repo(root=client_root)

        assert os.listdir(client_root) == [], "Workspace should be empty"
        repo.sync()
        assert os.listdir(client_root) == [
            "file.txt", "p4config"], "Workspace sync not as expected"
        with open(os.path.join(client_root, "file.txt")) as content:
            assert content.read() == "Hello World\n", "Unexpected content in workspace file"

        repo.sync(revision='@0')
        assert  "file.txt" not in os.listdir(client_root), "Workspace file wasn't de-synced"

        # Validate p4config
        with open(os.path.join(client_root, "p4config")) as content:
            assert "P4PORT=%s\n" % repo.perforce.port in content.readlines(), "Unexpected p4config content"

def test_checkout_stream():
    """Test checking out a stream depot"""
    setup_server(from_zip='server.zip')

    with tempfile.TemporaryDirectory(prefix="bk-p4-test-") as client_root:
        repo = P4Repo(root=client_root, stream='//stream-depot/main')

        assert os.listdir(client_root) == [], "Workspace should be empty"
        repo.sync()
        with open(os.path.join(client_root, "file.txt")) as content:
            assert content.read() == "Hello Stream World\n", "Unexpected content in workspace file"            

def test_workspace_recovery():
    """Test that we can detect and recover from various workspace snafus"""
    setup_server(from_zip='server.zip')

    with tempfile.TemporaryDirectory(prefix="bk-p4-test-") as client_root:
        repo = P4Repo(root=client_root)

        # clobber writeable file
        # partially synced writeable files may be left in the workspace if a machine was shutdown mid-sync
        with open(os.path.join(client_root, "file.txt"), 'w') as depotfile:
            depotfile.write("Overwrite this file")
        repo.sync() # By default, would raise 'cannot clobber writable file'
        with open(os.path.join(client_root, "file.txt")) as content:
            assert content.read() == "Hello World\n", "Unexpected content in workspace file"

        # p4 clean
        os.remove(os.path.join(client_root, "file.txt"))
        open(os.path.join(client_root, "added.txt"), 'a').close()
        repo.clean()
        assert os.listdir(client_root) == [
            "file.txt", "p4config"], "Failed to restore workspace file with repo.clean()"


# def test_bad_configs():
#     P4Repo('port', stream='stream', view=['view'])
#     P4Repo('port', view=['bad_view'])
