# P4 Trigger script that triggers buildkite builds
# Usage:
# my-pipeline change-commit //depot/... "python %//depot/scripts/buildkite-trigger.py% <pipeline> %changelist% %user%"
import sys
import subprocess

try:
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request
import json

__BUILDKITE_TOKEN__ = "<your_token>"

__ORG_SLUG__ = "<your_org>"
pipeline_slug = sys.argv[1]
changelist = sys.argv[2]
user = sys.argv[3]

description = subprocess.check_output(
    ["p4", "-Ztag", "-F", "%desc%", "describe", changelist]
)

headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer %s' % __BUILDKITE_TOKEN__,
}
payload = {
    'commit': '@' + changelist,
    'branch': 'master',
    'message': description,
    'author': {'name': user},
}
url = "https://api.buildkite.com/v2/organizations/%s/pipelines/%s/builds" % (
    __ORG_SLUG__,
    pipeline_slug,
)

params = json.dumps(payload).encode('utf8')
req = Request(url, data=params, headers=headers)
response = urlopen(req)
# print(response.read())
