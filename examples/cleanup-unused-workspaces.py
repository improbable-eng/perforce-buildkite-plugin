import sys
import logging

# Recommended reference: https://www.perforce.com/manuals/p4python/p4python.pdf
from P4 import P4
from datetime import datetime, timedelta
from pprint import pprint

# delete workspaces where last access time > N days ago
__days_unused__ = 30

p4 = P4()
logger = logging.getLogger("p4python")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s %(name)s %(levelname)s: %(message)s',
    '%H:%M:%S',
)
handler.setFormatter(formatter)
logger.addHandler(handler)
p4.logger = logger

p4.connect()

clients = p4.run_clients()

# Filter by basic prefix matching.
# May want to include filtering by user and other fields to avoid false positives.
bk_clients = [
    client for client in clients if client.get('client', '').startswith('bk-p4-')
]

now = datetime.now()
n_days_ago = (now - timedelta(days=__days_unused__)).timestamp()
unused_clients = [
    client for client in bk_clients if int(client.get('Access')) < n_days_ago
]

pprint(unused_clients)
proceed = (
    input(
        "Will delete %d/%d Buildkite clients. Continue? (y/n) "
        % (len(unused_clients), len(bk_clients))
    ).lower()
    == 'y'
)

if proceed:
    for client in unused_clients:
        clientname = client.get('client')
        try:
            p4.run_client('-d', clientname)
        except:
            pass
