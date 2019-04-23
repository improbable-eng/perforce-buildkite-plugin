import os
from threading import Thread
import tempfile
import subprocess
import time

import perforce

from functools import partial

import socket
from contextlib import closing

# Time after which the p4 server will be shut-down.
__P4D_TIMEOUT__ = 30

def find_free_port():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        return s.getsockname()[1]

def run_p4d(port):
    prefix = 'bk-p4d-test-'
    parent = tempfile.gettempdir()
    for d in os.listdir(parent):
        if d.startswith(prefix):
            try:
                os.remove(os.path.join(parent, d))
            except:
                print("Failed to remove", d)
        
    tmpdir = tempfile.mkdtemp(prefix=prefix)
    subprocess.run(["p4d", "-r", tmpdir, "-p", str(port)], timeout=__P4D_TIMEOUT__)


def start_server():
    """Start a p4 server in the background and return the address"""
    port = find_free_port()
    Thread(target=partial(run_p4d, port), daemon=True).start()
    time.sleep(3)
    return 'localhost:%s' % port

def test_harness():
    """Check that tests can start and connect to a local perforce server"""
    port = start_server()
    repo = perforce.Repo(port)
    assert(repo.info()['serverAddress'] == port)

# def test_checkout():
#     port = start_server()
#     repo = perforce.Repo(port)

#     repo.info()