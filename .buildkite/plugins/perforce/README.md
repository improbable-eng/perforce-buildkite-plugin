# Perforce for Buildkite

This plugin allows checking out code from perforce instead of git, by overriding the default behaviour with a `checkout` hook.

You can configure it by either:
    - Configuring port/username etc on the plugin its self (see plugin.yml for configurable fields)
    - Adding the standard P4PORT, P4USER and P4TICKETS env vars to your build environment

By default, it will sync the entire repo.

If you want to use a custom workspace mapping, configure this as part of the plugin. Same syntax as normal perforce workspace mapping.
