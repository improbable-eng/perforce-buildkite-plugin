#!/bin/bash
set -euo pipefail


# P4 Trigger script that triggers buildkite builds
# Usage:
# my-pipeline change-commit //depot/... "%//depot/scripts/buildkite-trigger.sh% <organisation> <pipeline> %changelist% %user% %email%"

ORG_SLUG=$1
PIPELINE_SLUG=$2

CHANGE=$3
USER=$4
EMAIL=$5

DESCRIPTION=$(p4 -Ztag -F %desc% describe %3)

curl -X POST "https://api.buildkite.com/v2/organizations/${ORG_SLUG}/pipelines/${PIPELINE_SLUG}/builds" \
  -d ‘{
    "commit": "${CHANGELIST}",
    "branch": "master",
    "message": "${DESCRIPTION}",
    "author": {
      "name": "${USER}",
      "email": "${EMAIL}"
    },
  }’