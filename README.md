# Perforce Buildkite Plugin

A [Buildkite plugin](https://buildkite.com/docs/agent/v3/plugins) that lets you check out code from [Perforce Version Control](https://www.perforce.com/products/helix-core)

* Configure by setting env vars in your build environment (e.g. `P4PORT`, `P4USER`) or via plugin config.
* Optionally add workspace mapping.

## Example

Assuming everything is configured via env vars and you just want to sync the whole repository:

```yaml
steps:
    plugins:
      - ca-johnson/perforce: ~
```

Doing configuration via the plugin instead:

```yaml
steps:
    plugins:
      - ca-johnson/perforce:
          p4port: my-perforce-server:1666
          p4user: my-username
```

Custom workspace mapping:

```yaml
steps:
    plugins:
      - ca-johnson/perforce:
          mapping: ???
```

Workspace mapping via a p4 stream:

```yaml
steps:
    plugins:
      - ca-johnson/perforce:
          stream: //dev/minimal
```