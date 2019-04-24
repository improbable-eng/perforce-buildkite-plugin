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

## Contributing

Making changes to python/
* Write unit tests
* Implement new functionality
* Iterate via unit tests

Making changes to hooks/ and scripts called by hooks
* Add entries to local-pipeline.yml to test new behaviour
* Run a perforce server on localhost
* Run `make` at repo root
* This vendors the plugin and runs the pipeline locally