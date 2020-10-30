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

def find_free_port():
    """Find an open port that we could run a perforce server on"""
    # pylint: disable=no-member
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(('', 0))
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return sock.getsockname()[1]

@contextmanager
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

    p4ssldir = os.path.join(tmpdir, 'ssl')
    shutil.copytree(os.path.join(os.path.dirname(__file__), 'fixture', 'insecure-ssl'), p4ssldir)
    # Like a beautifully crafted work of art, p4d fails to start if permissions on the secrets are too open.
    # https://www.perforce.com/manuals/v18.1/cmdref/Content/CmdRef/P4SSLDIR.html
    os.chmod(p4ssldir, 0o700)
    os.chmod(os.path.join(p4ssldir, 'privatekey.txt'), 0o600)
    os.chmod(os.path.join(p4ssldir, 'certificate.txt'), 0o600)
    os.environ['P4SSLDIR'] = p4ssldir

    yield subprocess.Popen(['p4d', '-r', tmpdir, '-p', p4port])

@pytest.fixture(scope='package')
def server():
    """Start a p4 server in the background and return the address"""
    port = find_free_port()
    p4port = 'ssl:localhost:%s' % port
    os.environ['P4PORT'] = p4port
    with run_p4d(p4port, from_zip='server.zip'):
        time.sleep(1)
        yield p4port

def store_server(repo, to_zip):
    """Zip up a server to use as a unit test fixture"""
    serverRoot = repo.info()['serverRoot']

    zip_path = os.path.join(os.path.dirname(__file__), 'fixture', to_zip)
    with zipfile.ZipFile(zip_path, 'w') as archive:
        for root, _, files in os.walk(serverRoot):
            for filename in files:
                abs_path = os.path.join(root, filename)
                archive.write(abs_path, os.path.relpath(abs_path, serverRoot))

def test_server_fixture(capsys, server):
    """Check that tests can start and connect to a local perforce server"""
    with capsys.disabled():
        print('port:', server, 'user: carl')
    repo = P4Repo()

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
        "//stream-depot/main/file.txt": "Hello Stream World\n",
        "//stream-depot/main/file_2.txt": "file_2\n",
        "//stream-depot/dev/file.txt": "Hello Stream World (dev)\n",
    }

    # Check submitted changes
    submitted_changes = repo.perforce.run_changes('-s', 'submitted')
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
        '7': {
            'action': ['branch'],
            'depotFile': ['//stream-depot/dev/file.txt'],
            'desc': 'Copy files from //stream-depot/main to //stream-depot/dev\n'
        },
        '8': {
            'action': ['edit'],
            'depotFile': ['//stream-depot/dev/file.txt'],
            'desc': 'Update contents of //stream-depot/dev/file.txt\n'
        },
        '9': {
            'action': ['add'],
            'depotFile': ['//stream-depot/main/file_2.txt'],
            'desc': 'file_2.txt - exists in main but not dev\n'
        }
    }

    # Check shelved changes
    shelved_changes = repo.perforce.run_changes('-s', 'pending')
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

    labels = repo.perforce.run_labels()
    # Filter info to only contain relevant keys
    labelinfo = {
        label.get('label'): {key: label.get(key)
                             for key in ['Revision']
                            }
        for label in labels
    }
    assert labelinfo == {
        'my-label': {'Revision': '@2'}
    }

def test_head(server, tmpdir):
    """Test resolve of HEAD changelist"""
    # workspace with no changes in view defaults to global view
    repo = P4Repo(root=tmpdir, view="//depot/empty_dir/... empty_dir/...")
    assert repo.head() == "@9", "Unexpected global HEAD revision"

    repo = P4Repo(root=tmpdir, stream='//stream-depot/dev')
    assert repo.head() == "@8", "Unexpected HEAD revision for stream"

    repo = P4Repo(root=tmpdir, stream='//stream-depot/idontexist')
    with pytest.raises(Exception, match=r"Stream '//stream-depot/idontexist' doesn't exist."):
        repo.head()

    assert repo.head_at_revision("@my-label") == "2", "Unexpected HEAD revision for label"

def test_checkout(server, tmpdir):
    """Test normal flow of checking out files"""
    repo = P4Repo(root=tmpdir)

    assert os.listdir(tmpdir) == [], "Workspace should be empty"
    repo.sync()
    assert sorted(os.listdir(tmpdir)) == sorted([
        "file.txt", "p4config"]), "Workspace sync not as expected"
    with open(os.path.join(tmpdir, "file.txt")) as content:
        assert content.read() == "Hello World\n", "Unexpected content in workspace file"

    repo.sync(revision='@0')
    assert "file.txt" not in os.listdir(tmpdir), "Workspace file wasn't de-synced"

    # Validate p4config
    with open(os.path.join(tmpdir, "p4config")) as content:
        assert "P4PORT=%s\n" % repo.perforce.port in content.readlines(), "Unexpected p4config content"

def test_checkout_partial_path(server, tmpdir):
    """Test checking out a subset of view with one path"""
    repo = P4Repo(root=tmpdir, sync=['//depot/file.txt'])
    repo.sync()
    assert 'file.txt' in os.listdir(tmpdir)

def test_checkout_partial_dir(server, tmpdir):
    """Test checking out a subset of view with one directory"""
    repo = P4Repo(root=tmpdir, sync=['//depot/...'])
    repo.sync()
    assert 'file.txt' in os.listdir(tmpdir)

def test_checkout_partial_multiple(server, tmpdir):
    """Test checking out a subset of view with multiple paths"""
    repo = P4Repo(root=tmpdir, sync=['//depot/fake-dir/...', '//depot/file.txt'])
    repo.sync()
    assert 'file.txt' in os.listdir(tmpdir)

def test_checkout_stream(server, tmpdir):
    """Test checking out a stream depot"""
    repo = P4Repo(root=tmpdir, stream='//stream-depot/main')

    assert os.listdir(tmpdir) == [], "Workspace should be empty"
    repo.sync()
    with open(os.path.join(tmpdir, "file.txt")) as content:
        assert content.read() == "Hello Stream World\n", "Unexpected content in workspace file"

def test_checkout_label(server, tmpdir):
    """Test checking out at a specific label"""
    repo = P4Repo(root=tmpdir)

    with pytest.raises(Exception, match=r'Invalid changelist/client/label/date'):
        repo.sync(revision="@nonexistent-label")

    repo.sync(revision="@my-label")
    with open(os.path.join(tmpdir, "file.txt")) as content:
        assert content.read() == "Hello World\n", "Unexpected content in workspace file"

def test_readonly_client(server, tmpdir):
    """Test creation of a readonly client"""
    repo = P4Repo(root=tmpdir, client_type='readonly')
    repo.sync()
    assert "file.txt" in os.listdir(tmpdir), "Workspace file was not synced"

def test_partitioned_client(server, tmpdir):
    """Test creation of a partitioned client"""
    repo = P4Repo(root=tmpdir, client_type='partitioned')
    repo.sync()
    assert "file.txt" in os.listdir(tmpdir), "Workspace file was not synced"

def test_modify_client_type(server, tmpdir):
    """Test modifying a clients type"""
    repo = P4Repo(root=tmpdir, client_type='writeable')
    repo.sync()

    with pytest.raises(Exception, match=r'Client storage type cannot be changed after client is created'):
        repo = P4Repo(root=tmpdir, client_type='readonly')
        repo.sync()

def test_workspace_recovery(server, tmpdir):
    """Test that we can detect and recover from various workspace snafus"""
    repo = P4Repo(
        root=tmpdir,
        # allow unit test to delete otherwise readonly files from workspace
        client_options='allwrite'
    )

    # clobber writeable file
    # partially synced writeable files may be left in the workspace if a machine was shutdown mid-sync
    with open(os.path.join(tmpdir, "file.txt"), 'w') as depotfile:
        depotfile.write("Overwrite this file")
    repo.sync() # By default, would raise 'cannot clobber writable file'
    with open(os.path.join(tmpdir, "file.txt")) as content:
        assert content.read() == "Hello World\n", "Unexpected content in workspace file"

    # p4 clean
    os.remove(os.path.join(tmpdir, "file.txt"))
    open(os.path.join(tmpdir, "added.txt"), 'a').close()
    repo.clean()
    assert sorted(os.listdir(tmpdir)) == sorted([
        "file.txt", "p4config"]), "Failed to restore workspace file with repo.clean()"

    os.remove(os.path.join(tmpdir, "file.txt"))
    os.remove(os.path.join(tmpdir, "p4config"))
    repo = P4Repo(root=tmpdir) # Open a fresh tmpdir, as if this was a different job
    repo.sync() # Normally: "You already have file.txt", but since p4config is missing it will restore the workspace
    assert sorted(os.listdir(tmpdir)) == sorted([
        "file.txt", "p4config"]), "Failed to restore corrupt workspace due to missing p4config"

def test_p4print_unshelve(server, tmpdir):
    """Test unshelving a pending changelist by p4printing content into a file"""
    repo = P4Repo(root=tmpdir)
    repo.sync()
    with open(os.path.join(tmpdir, "file.txt")) as content:
        assert content.read() == "Hello World\n", "Unexpected content in workspace file"

    repo.p4print_unshelve('3') # Modify a file
    with open(os.path.join(tmpdir, "file.txt")) as content:
        assert content.read() == "Goodbye World\n", "Unexpected content in workspace file"

    repo.p4print_unshelve('4') # Delete a file
    assert not os.path.exists(os.path.join(tmpdir, "file.txt"))

    repo.p4print_unshelve('5') # Add a file
    assert os.path.exists(os.path.join(tmpdir, "newfile.txt"))

    with pytest.raises(Exception, match=r'Changelist 999 does not contain any shelved files.'):
        repo.p4print_unshelve('999')

    assert len(repo._read_patched()) == 2 # changes to file.txt and newfile.txt

    # Unshelved changes are removed in following syncs
    repo.sync()
    with open(os.path.join(tmpdir, "file.txt")) as content:
        assert content.read() == "Hello World\n", "Unexpected content in workspace file"
    assert not os.path.exists(os.path.join(tmpdir, "newfile.txt")), "File unshelved for add was not deleted"

    # Shelved changes containing files not selected for sync are skipped
    repo = P4Repo(root=tmpdir, sync=['//depot/fake-dir/...'])
    repo.sync()
    repo.p4print_unshelve('3') # Modify file.txt
    assert not os.path.exists(os.path.join(tmpdir, "file.txt"))

    # Shelved changes containing files not mapped into this workspace do not throw an exception
    repo = P4Repo(root=tmpdir, stream='//stream-depot/main')
    repo.p4print_unshelve('3') # Modify a file


def copytree(src, dst):
    """Shim to get around shutil.copytree requiring root dir to not exist"""
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)

def test_client_migration(server, tmpdir):
    """Test re-use of workspace data when moved to another host"""
    repo = P4Repo(root=tmpdir)

    assert os.listdir(tmpdir) == [], "Workspace should be empty"
    synced = repo.sync()
    assert len(synced) > 0, "Didn't sync any files"

    with tempfile.TemporaryDirectory(prefix="bk-p4-test-") as second_client:
        copytree(tmpdir, second_client)
        # Client names include path on disk, so this creates a new unique client
        repo = P4Repo(root=second_client)
        synced = repo.sync() # Flushes to match previous client, since p4config is there on disk
        assert synced == [], "Should not have synced any files in second client"

def test_stream_switching(server, tmpdir):
    """Test stream-switching within the same depot"""
    repo = P4Repo(root=tmpdir, stream='//stream-depot/main')
    synced = repo.sync()
    assert len(synced) > 0, "Didn't sync any files"
    assert set(os.listdir(tmpdir)) == set([
        "file.txt", "file_2.txt", "p4config"])
    with open(os.path.join(tmpdir, "file.txt")) as content:
        assert content.read() == "Hello Stream World\n", "Unexpected content in workspace file"

    # Re-use the same checkout directory, but switch streams
    repo = P4Repo(root=tmpdir, stream='//stream-depot/dev')
    repo.sync()
    assert len(synced) > 0, "Didn't sync any files"
    assert set(os.listdir(tmpdir)) == set([
        "file.txt", "p4config"]) # file_2.txt was de-synced
    with open(os.path.join(tmpdir, "file.txt")) as content:
        assert content.read() == "Hello Stream World (dev)\n", "Unexpected content in workspace file"

def test_stream_switching_migration(server, tmpdir):
    """Test stream-switching and client migration simultaneously"""
    repo = P4Repo(root=tmpdir, stream='//stream-depot/main')
    synced = repo.sync()
    assert len(synced) > 0, "Didn't sync any files"
    assert set(os.listdir(tmpdir)) == set([
        "file.txt", "file_2.txt", "p4config"])
    with open(os.path.join(tmpdir, "file.txt")) as content:
        assert content.read() == "Hello Stream World\n", "Unexpected content in workspace file"

    with tempfile.TemporaryDirectory(prefix="bk-p4-test-") as second_client:
        copytree(tmpdir, second_client)
        # Client names include path on disk, so this creates a new unique client
        # Re-use the same checkout directory and switch streams at the same time
        repo = P4Repo(root=second_client, stream='//stream-depot/dev')
        repo.sync()
        assert len(synced) > 0, "Didn't sync any files"
        assert set(os.listdir(second_client)) == set([
            "file.txt", "p4config"]) # file_2.txt was de-synced
        with open(os.path.join(second_client, "file.txt")) as content:
            assert content.read() == "Hello Stream World (dev)\n", "Unexpected content in workspace file"

# fingerprint here matches to the cert in the test fixture directory, and you can check that with
# P4SSLDIR=$(pwd)/python/fixture/insecure-ssl p4d -Gf
__LEGIT_P4_FINGERPRINT__ = '7A:10:F6:00:95:87:5B:2E:D4:33:AB:44:42:05:85:94:1C:93:2E:A2'

def test_fingerprint_good(server, tmpdir):
    """Test supplying the correct fingerprint"""
    os.environ['P4TRUST'] = os.path.join(tmpdir, 'trust.txt')

    repo = P4Repo(root=tmpdir, fingerprint=__LEGIT_P4_FINGERPRINT__)
    synced = repo.sync()
    assert len(synced) > 0, "Didn't sync any files"

def test_fingerprint_bad(server, tmpdir):
    """Test supplying an incorrect fingerprint"""
    os.environ['P4TRUST'] = os.path.join(tmpdir, 'trust.txt')

    repo = P4Repo(root=tmpdir, fingerprint='FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF')
    with pytest.raises(Exception, match=r"The authenticity of '.+' can't be established"):
        repo.sync()

def test_fingerprint_changed(server, tmpdir):
    """Test updating a fingerprint"""
    os.environ['P4TRUST'] = os.path.join(tmpdir, 'trust.txt')

    repo = P4Repo(root=tmpdir, fingerprint='FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF:FF')
    with pytest.raises(Exception, match=r"The authenticity of '.*' can't be established"):
        repo.sync()   

    repo = P4Repo(root=tmpdir, fingerprint=__LEGIT_P4_FINGERPRINT__)
    synced = repo.sync()
    assert len(synced) > 0, "Didn't sync any files"


# def test_live_server():
#     """Reproduce production issues quickly by writing tests which run against a real server"""
#     os.environ["P4USER"] = "carljohnson"
#     os.environ["P4PORT"] = "ssl:live-server:1666"
#     root = "/Users/carl/p4-test-client"
#     repo = P4Repo(root=root)
#     repo.p4print_unshelve("28859")
