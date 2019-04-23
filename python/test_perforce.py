import os
from threading import Thread
import tempfile
import subprocess
import time
import zipfile
import shutil

import perforce

from functools import partial

import socket
from contextlib import closing

# Time after which the p4 server will automatically be shut-down.
__P4D_TIMEOUT__ = 30
# __P4D_TIMEOUT__ = None

def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

def run_p4d(port, from_zip=None):
    prefix = 'bk-p4d-test-'
    parent = tempfile.gettempdir()
    for d in os.listdir(parent):
        if d.startswith(prefix):
            try:
                shutil.rmtree(os.path.join(parent, d))
            except:
                print("Failed to remove", d)

    tmpdir = tempfile.mkdtemp(prefix=prefix)
    if from_zip:
        zip_path = os.path.join(os.path.dirname(__file__), 'fixture', from_zip)
        with zipfile.ZipFile(zip_path) as archive:
            archive.extractall(tmpdir)
    subprocess.run(["p4d", "-r", tmpdir, "-p", str(port)], timeout=__P4D_TIMEOUT__)

def setup_server(from_zip=None):
    """Start a p4 server in the background and return the address"""
    port = find_free_port()
    Thread(target=partial(run_p4d, port, from_zip=from_zip), daemon=True).start()
    time.sleep(5)
    return 'localhost:%s' % port

def test_harness():
    """Check that tests can start and connect to a local perforce server"""
    port = setup_server(from_zip='server.zip')
    repo = perforce.Repo(port)
    assert(repo.info()['serverAddress'] == port)

    # There should be a sample file checked into the fixture server
    content = repo.p4.run_print("//depot/file.txt")[1] # Returns [metadata, contents]
    assert(content == "Hello World\n")


def test_sync():
    port = setup_server(from_zip='server.zip')

    with tempfile.TemporaryDirectory(prefix="bk-p4-test-") as client_root:
        repo = perforce.Repo(port, root=client_root)
        repo.sync()

        with open(os.path.join(client_root, 'file.txt')) as content:
            assert(content.read() == "Hello World\n")

# def test_bad_configs():
#     perforce.Repo('port', stream='stream', view=['view'])
#     perforce.Repo('port', view=['bad_view'])

    