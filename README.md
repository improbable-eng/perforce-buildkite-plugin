A [Buildkite plugin](https://buildkite.com/docs/agent/v3/plugins) that lets you check out code from [Perforce Version Control](https://www.perforce.com/products/helix-core) on Windows, Linux and macOS platforms.

1. Configure at least `P4PORT` and `P4USER` (see examples below)
2. Provision with credentials - a `P4TICKETS` file is recommended
3. Optionally customise workspace mapping with `stream`, `sync` or `view` settings.

The `P4CLIENT`, `P4USER` and `P4PORT` used by the plugin are written to a [`P4CONFIG`](https://www.perforce.com/manuals/v16.2/cmdref/P4CONFIG.html) file at the workspace root and the `P4CONFIG` env var is set, so build scripts are able to automatically pick up configuration for any further interactions with Perforce.

## Examples

### Configuration via env vars

```yaml
env:
  P4PORT: perforce:1666
  P4USER: username

steps:
  plugins:
    - inflexiongames/perforce: ~
```

### Configuration via plugin

```yaml
steps:
  plugins:
    - inflexiongames/perforce:
      p4port: perforce:1666
      p4user: username
```

`P4PORT` may also be configured by setting `BUILDKITE_REPO` for your pipeline.

## Configuration

### Basic

#### `p4user/p4port/p4tickets/p4trust` (optional, string)

Override configuration at the User Environment level. May be overridden by P4CONFIG or P4ENVIRO files.

See [p4 set](https://www.perforce.com/manuals/cmdref/Content/CmdRef/p4_set.html?Highlight=precedence) for more on system variables and precedence.

#### `fingerprint` (optional, string)

Supply a trusted p4 server fingerprint to ensure the server the client connects to has not been MITM'd.

#### `stream` (optional, string)

Which p4 stream to sync, e.g. `//dev/minimal`. Can be overridden by `view`.

#### `sync` (optional, []string)

List of paths to sync, useful when only a subset of files in the clients view are required.

```yaml
sync:
  - //dev/minimal/.buildkite/...
  - //dev/minimal/scripts/...
```

#### `view` (optional, string)

Custom workspace view. Must consist of concrete depot paths. Overrides `stream`.

```yaml
view: >-
  //dev/project/... project/...
  //dev/vendor/... vendor/...
```

### Advanced

#### `client_options` (optional, string)

Default: `clobber`.

Additional options for the client workspace, see [Options field](https://www.perforce.com/manuals/cmdref/Content/CmdRef/p4_client.html?#Options2).

```yaml
client_options: noclobber nowriteall
```

#### `client_type` (optional, string)

Default: `writeable`.

`readonly` and `partitioned` client workspaces can be used to reduce impact of automated build systems on Perforce server performance.
See related article [Readonly and Partitioned Client Workspaces](https://community.perforce.com/s/article/15372).

Note that `writeable` client workspaces must be deleted and re-created to change to `readonly` or `partitioned` and vice versa.

Note that `readonly` or `partitioned` workspaces do not appear in the `db.have` table, which prevents them from being used as a revision specifier.

This adds a caveat if you wish to re-use workspace data across different machines: the original client which populated that workspace must have been `writeable`.

(e.g. If a disk with existing workspace data is attached to a new machine, the plugin will create a new client, read the old workspace name from P4CONFIG and `p4 flush //...@<old-workspace>`. The flush command fails if the old workspace was not of type `writeable`)

#### `parallel` (optional, string)

Default: `0` (no parallelism)

Number of threads to use for parallel sync operations. High values may affect Perforce server performance.

#### `share_workspace` (optional, bool)

Default: `no`

Allow multiple Buildkite pipelines to share each stream-specific client workspace.

Useful to avoid syncing duplicate data for large workspaces.

Can only be used with stream workspaces and when no more than one buildkite-agent process is running on that machine.

#### `stream_switching` (optional, bool)

Default: `no`

Allows multiple Buildkite pipelines to share a single client workspace, switching streams as required.

Must have `share_workspace: yes` to take effect.

## Triggering Builds

There are a few options for triggering builds that use this plugin, in this order from least valuable but most convenient to most valuable but least convenient.

### Manual

Relies on people within your team manually clicking `New Build` within the BuildKite UI.

* To build current head revision on the server - accept the defaults.
* To build a specific revision - paste the revision number into the `Commit` textbox.
  * Note you can also use more abstract p4 revision specifiers such as `@labelname` or `@datespec`
* To build a shelved changelist - paste your changelist number into the `Branch` textbox.

### Schedule

[Scheduled builds](https://buildkite.com/docs/pipelines/scheduled-builds) with a cron in buildkite - this requires no additional setup, but provides the slowest response time between a change being made and a build triggered.

### Polling

A service polls your perforce for the current head revision and POSTs to the Buildkite API to trigger builds for any new changes. Note that you will need to store state to avoid duplicate and skipped builds.

### P4 Trigger

Set up a `p4 trigger` which POSTs to the buildkite API to trigger a build. See [p4 triggers](https://www.perforce.com/manuals/v18.1/cmdref/Content/CmdRef/p4_triggers.html) for more information. Note that this will require admin access to the Perforce server.

See [examples](./examples) for sample p4 trigger scripts.

## Contributing

### OSX

Run `dev/setup_env_osx.sh`

Python [virtualenv](https://docs.python.org/3/tutorial/venv.html) `.dev-venv` for running tests will be created at repo root.

Run the `test_server_fixture` unit test to check everything is setup correctly:

```bash
source .dev-venv/bin/activate
pytest python/test_perforce.py -k test_server_fixture
```

### Linux/Windows

TBC, feedback welcome.

### Suggested workflow

Making changes to `python/`

* Read implementation of `test_server_fixture` in `test_perforce.py`
* Write unit test in `test_perforce.py`, optionally making changes to the test fixture if required
* Implement new functionality
* Iterate via unit test

Making changes to `hooks/` and scripts called by hooks

* Add entries to local-pipeline.yml to test new behaviour, if relevant
* `make` to start p4d on localhost:1666, vendor the plugin, run the pipeline and kill p4d.
