"""
Test perforce module for managing workspaces
"""
from contextlib import closing, contextmanager
from functools import partial
from threading import Thread
import os
import shutil
import socket
import subprocess
import tempfile
import time
import zipfile
import pytest

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

@contextmanager
def setup_server_and_client(from_zip='server.zip'):
    """Start server from a fixture and create a client workspace tmp dir"""
    setup_server(from_zip)
    with tempfile.TemporaryDirectory(prefix="bk-p4-test-") as client_root:
        yield client_root


def store_server(repo, to_zip):
    """Zip up a server to use as a unit test fixture"""
    serverRoot = repo.info()['serverRoot']

    zip_path = os.path.join(os.path.dirname(__file__), 'fixture', to_zip)
    with zipfile.ZipFile(zip_path, 'w') as archive:
        for root, _, files in os.walk(serverRoot):
            for filename in files:
                abs_path = os.path.join(root, filename)
                archive.write(abs_path, os.path.relpath(abs_path, serverRoot))

def test_fixture(capsys):
    """Check that tests can start and connect to a local perforce server"""
    port = setup_server(from_zip='server.zip')
    with capsys.disabled():
        print('port:', port, 'user: carl')
    repo = P4Repo()
    assert repo.info()['serverAddress'] == port

    # To change the fixture server, uncomment the line below with 'store_server' and put a breakpoint on it
    # Run unit tests in the debugger and hit the breakpoint
    # Log in using details printed to stdout (port/user) via p4v or the command line
    # Make changes to the p4 server
    # Continue execution so that the 'store_server' line executes
    # Replace server.zip with new_server.zip
    # Update validation code below to document the new server contents

    # store_server(repo, 'new_server.zip')
    
    # Validate contents of server fixture @HEAD
    depotfiles = [info['depotFile'] for info in repo.perforce.run_files('//...')]
    depotfile_to_content = {depotfile: repo.perforce.run_print(depotfile)[1] for depotfile in depotfiles}
    assert depotfile_to_content == {
        "//depot/file.txt": "Hello World\n",
        "//stream-depot/main/file.txt": "Hello Stream World\n"
    }

    # Check submitted changes
    submitted_changes = [change for change in repo.perforce.run_changes('-s', 'submitted')]
    submitted_changeinfo = {change["change"]: repo.perforce.run_describe(change["change"])[0] for change in submitted_changes}
    # Filter info to only contain relevant keys for submitted changes
    submitted_changeinfo = {
        change: {key: info.get(key) 
                 for key in ['depotFile', 'desc', 'action']} 
                 for change, info in submitted_changeinfo.items()
    }
    assert submitted_changeinfo == {
        '1' :{
            'action': ['add'],
            'depotFile': ['//depot/file.txt'],
            'desc': 'Initial Commit'
        },
        '2' :{
            'action': ['add'],
            'depotFile': ['//stream-depot/main/file.txt'],
            'desc': 'Initial Commit to Stream\n'
        },
        '6' :{
            'action': ['edit'],
            'depotFile': ['//depot/file.txt'],
            'desc': 'modify //depot/file.txt\n'
        },
    }

    # Check shelved changes
    shelved_changes = [change for change in repo.perforce.run_changes('-s', 'pending')]
    shelved_changeinfo = {change["change"]: repo.perforce.run_describe('-S', change["change"])[0] for change in shelved_changes}
    # Filter info to only contain relevant keys for submitted changes
    shelved_changeinfo = {
        change: {key: info.get(key) 
                 for key in ['depotFile', 'desc', 'action']} 
                 for change, info in shelved_changeinfo.items()
    }
    assert shelved_changeinfo == {
        '3' :{
            'action': ['edit'],
            'depotFile': ['//depot/file.txt'],
            'desc': 'Modify file in shelved change\n',
            # Change content from 'Hello World\n' to 'Goodbye World\n'
        },
        '4' :{
            'action': ['delete'],
            'depotFile': ['//depot/file.txt'],
            'desc': 'Delete file in shelved change\n',
        },
        '5' :{
            'action': ['add'],
            'depotFile': ['//depot/newfile.txt'],
            'desc': 'Add file in shelved change\n',
        },
    }

def test_head():
    """Test resolve of HEAD changelist"""
    setup_server(from_zip='server.zip')

    repo = P4Repo()
    assert repo.head() == "6", "Unexpected global HEAD revision"

    repo = P4Repo(stream='//stream-depot/main')
    assert repo.head() == "2", "Unexpected HEAD revision for stream"

    repo = P4Repo(stream='//stream-depot/idontexist')
    with pytest.raises(Exception, match=r"Stream '//stream-depot/idontexist' doesn't exist."):
        repo.head()

def test_checkout():
    """Test normal flow of checking out files"""
    with setup_server_and_client() as client_root:
        repo = P4Repo(root=client_root)

        assert os.listdir(client_root) == [], "Workspace should be empty"
        repo.sync()
        assert sorted(os.listdir(client_root)) == sorted([
            "file.txt", "p4config"]), "Workspace sync not as expected"
        with open(os.path.join(client_root, "file.txt")) as content:
            assert content.read() == "Hello World\n", "Unexpected content in workspace file"

        repo.sync(revision='@0')
        assert "file.txt" not in os.listdir(client_root), "Workspace file wasn't de-synced"

        # Validate p4config
        with open(os.path.join(client_root, "p4config")) as content:
            assert "P4PORT=%s\n" % repo.perforce.port in content.readlines(), "Unexpected p4config content"

def test_checkout_stream():
    """Test checking out a stream depot"""
    with setup_server_and_client() as client_root:
        repo = P4Repo(root=client_root, stream='//stream-depot/main')

        assert os.listdir(client_root) == [], "Workspace should be empty"
        repo.sync()
        with open(os.path.join(client_root, "file.txt")) as content:
            assert content.read() == "Hello Stream World\n", "Unexpected content in workspace file"            

def test_workspace_recovery():
    """Test that we can detect and recover from various workspace snafus"""
    with setup_server_and_client() as client_root:
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
        assert sorted(os.listdir(client_root)) == sorted([
            "file.txt", "p4config"]), "Failed to restore workspace file with repo.clean()"

        os.remove(os.path.join(client_root, "file.txt"))
        os.remove(os.path.join(client_root, "p4config"))
        repo = P4Repo(root=client_root) # Open a fresh client, as if this was a different job
        repo.sync() # Normally: "You already have file.txt", but since p4config is missing it will restore the workspace
        assert sorted(os.listdir(client_root)) == sorted([
            "file.txt", "p4config"]), "Failed to restore corrupt workspace due to missing p4config"

def test_unshelve():
    """Test unshelving a pending changelist"""
    with setup_server_and_client() as client_root:
        repo = P4Repo(root=client_root)
        repo.sync()
        with open(os.path.join(client_root, "file.txt")) as content:
            assert content.read() == "Hello World\n", "Unexpected content in workspace file"

        repo.unshelve('3')
        with open(os.path.join(client_root, "file.txt")) as content:
            assert content.read() == "Goodbye World\n", "Unexpected content in workspace file"

        with pytest.raises(Exception, match=r'Changelist 999 does not contain any shelved files.'):
            repo.unshelve('999')

        # Unshelved changes are removed in following syncs
        repo.sync()
        with open(os.path.join(client_root, "file.txt")) as content:
            assert content.read() == "Hello World\n", "Unexpected content in workspace file"

def test_p4print_unshelve():
    """Test unshelving a pending changelist by p4printing content into a file"""
    with setup_server_and_client() as client_root:
        repo = P4Repo(root=client_root)
        repo.sync()
        with open(os.path.join(client_root, "file.txt")) as content:
            assert content.read() == "Hello World\n", "Unexpected content in workspace file"

        repo.p4print_unshelve('3') # Modify a file
        with open(os.path.join(client_root, "file.txt")) as content:
            assert content.read() == "Goodbye World\n", "Unexpected content in workspace file"

        repo.p4print_unshelve('4') # Delete a file
        assert not os.path.exists(os.path.join(client_root, "file.txt"))

        repo.p4print_unshelve('5') # Add a file
        assert os.path.exists(os.path.join(client_root, "newfile.txt"))

        with pytest.raises(Exception, match=r'Changelist 999 does not contain any shelved files.'):
            repo.p4print_unshelve('999')

        assert len(repo._read_patched()) == 2 # changes to file.txt and newfile.txt

        # Unshelved changes are removed in following syncs
        repo.sync()
        with open(os.path.join(client_root, "file.txt")) as content:
            assert content.read() == "Hello World\n", "Unexpected content in workspace file"
        assert not os.path.exists(os.path.join(client_root, "newfile.txt"))

        # Shelved changes containing files not mapped into this workspace do not throw an exception
        repo = P4Repo(root=client_root, stream='//stream-depot/main')
        repo.p4print_unshelve('3') # Modify a file

def test_backup_shelve():
    """Test making a copy of a shelved changelist"""
    with setup_server_and_client() as client_root:
        repo = P4Repo(root=client_root)

        backup_changelist = repo.backup('3')
        assert backup_changelist != '3', "Backup changelist number must be new"
        repo.revert()
        repo.unshelve(backup_changelist)
        with open(os.path.join(client_root, "file.txt")) as content:
            assert content.read() == "Goodbye World\n", "Unexpected content in workspace file"


def copytree(src, dst):
    """Shim to get around shutil.copytree requiring root dir to not exist"""
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)

def test_client_migration():
    """Test re-use of workspace data when moved to another host"""
    with setup_server_and_client() as client_root:
        repo = P4Repo(root=client_root)

        assert os.listdir(client_root) == [], "Workspace should be empty"
        synced = repo.sync()
        assert len(synced) > 0, "Didn't sync any files"

        with tempfile.TemporaryDirectory(prefix="bk-p4-test-") as second_client_root:
            copytree(client_root, second_client_root)
            repo = P4Repo(root=second_client_root)
            synced = repo.sync() # Flushes to match previous client, since p4config is there on disk
            assert synced == [], "Should not have synced any files in second client"


# def test_live_server():
#     """Reproduce production issues quickly by writing tests which run against a real server"""
#     os.environ["P4USER"] = "carljohnson"
#     os.environ["P4PORT"] = "ssl:live-server:1666"
#     root = "/Users/carl/p4-test-client"
#     repo = P4Repo(root=root)
#     repo.p4print_unshelve("28859")
