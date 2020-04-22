# Perforce Buildkite Plugin [![Build Status](https://travis-ci.com/improbable-eng/perforce-buildkite-plugin.svg?branch=master)](https://travis-ci.com/improbable-eng/perforce-buildkite-plugin)

A [Buildkite plugin](https://buildkite.com/docs/agent/v3/plugins) that lets you check out code from [Perforce Version Control](https://www.perforce.com/products/helix-core)

1. Configure at least P4PORT and P4USER (see examples below)
2. Provision with credentials - a P4TICKETS file is recommended
3. Optionally customise workspace mapping.

The P4CLIENT, P4USER and P4PORT used by the plugin are written to a [P4CONFIG](https://www.perforce.com/manuals/v16.2/cmdref/P4CONFIG.html) file at the workspace root and the P4CONFIG env var is set, so build scripts are able to automatically pick up configuration for any further interactions with Perforce.

## Examples

### Configuration via env vars:

```yaml
env:
  P4PORT: perforce:1666
  P4USER: username

steps:
  plugins:
    - improbable-eng/perforce: ~
```

### Configuration via the plugin:

```yaml
steps:
  plugins:
    - improbable-eng/perforce:
      p4port: perforce:1666
      p4user: username
```

`P4PORT` may also be configured by setting `BUILDKITE_REPO` for your pipeline.

### Custom workspace view:

Note that this must consist of real depot paths like a regular worspace view. You cannot combine streams.

```yaml
steps:
  plugins:
    - improbable-eng/perforce:
      view: >-
        //dev/project/... project/...
        //dev/vendor/... vendor/...
```

### Workspace view via a p4 stream:

```yaml
steps:
    plugins:
      - improbable-eng/perforce:
          stream: //dev/minimal
```

### Partial sync of a stream

```yaml
steps:
    plugins:
      - improbable-eng/perforce:
          stream: //dev/minimal
          sync: //dev/minimal/.buildkite/...
```

### Enable parallel sync

```yaml
steps:
    plugins:
      - improbable-eng/perforce:
          parallel: 16
```

### Share a stream workspace between pipelines

Useful to avoid syncing duplicate data with large workspaces.
Only allowed when there is a single buildkite agent running on the machine.

```yaml
steps:
    plugins:
      - improbable-eng/perforce:
          stream: //dev/buildkite
           # Sync each stream once
          share_workspace: true
          # Sync once and switch streams in-place (requires share_workspace: true)
          stream_switching: true
```

## Triggering Builds

There are a few options for triggering builds that use this plugin, in this order from least valuable but most convenient to most valuable but least convenient.

### Manual

Relies on people within your team manually clicking `New Build` within the BuildKite UI.

* To build current head revision on the server - accept the defaults.
* To build a specific revision - paste the revision number into the `Commit` textbox.
  * Note you can also use more abstract p4 revision specifiers such as `@labelname` or `@datespec`
* To build a shelved changelist - paste your changelist number into the `Branch` textbox.

### Schedule

Schedule builds with a cron in buildkite - this requires no additional setup, but provides the worst response time as changes are made

### Polling

A service polls your perforce for the current head revision and POSTs to the Buildkite API to trigger builds for any new changes. Note that you will need to store state to avoid duplicate and skipped builds.

### `p4 trigger`

Set up a `p4 trigger` which POSTs to the buildkite API to trigger a build. See [p4 triggers](https://www.perforce.com/manuals/v18.1/cmdref/Content/CmdRef/p4_triggers.html) for more information. Note that this will require admin access to the Perforce server.

## Contributing

### OSX

Run `dev/setup_env_osx.sh`

Python [virtualenv](https://docs.python.org/3/tutorial/venv.html) `.dev-venv` for running tests will be created at repo root.

Run the `test_fixture` unit test to check everything is setup correctly:

```
source .dev-venv/bin/activate
pytest python/test_perforce.py -k test_fixture
```

### Linux/Windows

TBC, feedback welcome

### Suggested workflow

Making changes to `python/`

* Read implementation of `test_fixture` in `test_perforce.py`
* Write unit test in `test_perforce.py`, optionally making changes to the test fixture if required
* Implement new functionality
* Iterate via unit test

Making changes to `hooks/` and scripts called by hooks

* Add entries to local-pipeline.yml to test new behaviour, if relevant
* `make` to start p4d on localhost:1666, vendor the plugin, run the pipeline and kill p4d.
