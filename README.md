# Perforce Buildkite Plugin [![Build Status](https://travis-ci.com/ca-johnson/perforce-buildkite-plugin.svg?branch=master)](https://travis-ci.com/ca-johnson/perforce-buildkite-plugin)

A [Buildkite plugin](https://buildkite.com/docs/agent/v3/plugins) that lets you check out code from [Perforce Version Control](https://www.perforce.com/products/helix-core)

1. Configure at least P4PORT and P4USER (see examples below)
2. Provision with credentials - a P4TICKETS file is recommended
3. Optionally customise workspace mapping.

The P4CLIENT, P4USER and P4PORT used by the plugin are written to a [P4CONFIG](https://www.perforce.com/manuals/v16.2/cmdref/P4CONFIG.html) file at the workspace root and the P4CONFIG env var is set, so build scripts are able to automatically pick up configuration for any further interactions with Perforce.

## Examples

Configuration via env vars:

```yaml
env:
  P4PORT: perforce:1666
  P4USER: username

steps:
  plugins:
    - ca-johnson/perforce: ~
```

Configuration via the plugin:

```yaml
steps:
  plugins:
    - ca-johnson/perforce:
      p4port: perforce:1666
      p4user: username
```

`P4PORT` may also be configured by setting `BUILDKITE_REPO` for your pipeline.

Custom workspace view:

```yaml
steps:
  plugins:
    - ca-johnson/perforce:
      view: >-
        //dev/project/... project/...
        //dev/vendor/... vendor/...
```

Workspace view via a p4 stream:

```yaml
steps:
    plugins:
      - ca-johnson/perforce:
          stream: //dev/minimal
```

Partial sync of a stream

```yaml
steps:
    plugins:
      - ca-johnson/perforce:
          stream: //dev/minimal
          sync: //dev/minimal/.buildkite/...
```

Enable parallel sync

```yaml
steps:
    plugins:
      - ca-johnson/perforce:
          parallel: 16
```

Share a stream workspace between pipelines. Useful to avoid syncing duplicate data with large workspaces.
Only allowed when there is a single buildkite agent running on the machine.

```yaml
steps:
    plugins:
      - ca-johnson/perforce:
          stream: //dev/buildkite
          share_workspace: true
```

## Triggering Builds

There are a few options for triggering builds that use this plugin, in this order from least valuable but most convenient to most valuable but least convenient.

### Manual

Relies on people within your team manually clicking `New Build` within the BuildKite UI.

* To build current head of the stream - accept the defaults.
* To build a specific revision - paste the revision number into the `Revision` textbox.
* To build a Shelf Set (pending Change List) - paste your revision to the `Branch` textbox.

### Schedule

Schedule builds with a cron in buildkite - this requires no additional setup, but provides the worst reponse time as changes are made

### Polling

A service polls your perforce for the current head revision and POSTs to the Buildkite API to trigger builds for any new changes. Note that you will need to store state to avoid duplicate and skipped builds.

### `p4 trigger`

Set up a `p4 trigger` which POSTs to the buildkite API to trigger a build. See [p4 triggers](https://www.perforce.com/manuals/v18.1/cmdref/Content/CmdRef/p4_triggers.html) for more information. Note that this will require admin access to the Perforce server.

## Contributing

1. Install python/requirements.txt
2. Make sure `p4d` is in your `PATH`
3. Make sure your version of `bk` supports `bk local run`

Making changes to `python/`
* Write unit tests
* Implement new functionality
* Iterate via python unit tests

Making changes to `hooks/` and scripts called by hooks
* Add entries to local-pipeline.yml to test new behaviour, if relevant.
* `make` to start p4d on localhost:1666, vendor the plugin, run the pipeline and kill p4d.
