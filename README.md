# Perforce Buildkite Plugin

A [Buildkite plugin](https://buildkite.com/docs/agent/v3/plugins) that lets you check out code from [Perforce Version Control](https://www.perforce.com/products/helix-core)

* Configure by setting env vars in your build environment (e.g. `P4PORT`, `P4USER`) or via plugin config.
* Optionally add workspace mapping.

## Example

steps:
    plugins:
      - ca-johnson/perforce:
          p4port: my-perforce-server:1666