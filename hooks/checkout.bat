@echo off

rem Required to prevent global post-checkout hook from failing
rem TODO: Skip if relevant phases missing from BUILDKITE_PHASES
git init 

if defined BUILDKITE_PLUGIN_PERFORCE_P4PORT (
    set "P4PORT=%BUILDKITE_PLUGIN_PERFORCE_P4PORT%"
)
if defined BUILDKITE_PLUGIN_PERFORCE_P4USER (
    set "P4USER=%BUILDKITE_PLUGIN_PERFORCE_P4USER%"
)
if defined BUILDKITE_PLUGIN_PERFORCE_P4TICKETS (
    set "P4TICKETS=%BUILDKITE_PLUGIN_PERFORCE_P4TICKETS%"
)
if defined BUILDKITE_PLUGIN_PERFORCE_P4TRUST (
    set "P4TRUST=%BUILDKITE_PLUGIN_PERFORCE_P4TRUST%"
)

if defined BUILDKITE_PLUGIN_PERFORCE_ROOT (
    set "ROOT=%BUILDKITE_PLUGIN_PERFORCE_ROOT%"
) else (
    set "ROOT=%BUILDKITE_BUILD_CHECKOUT_PATH%"
)

if defined BUILDKITE_PLUGIN_PERFORCE_VIEW (
    set "VIEW=%BUILDKITE_PLUGIN_PERFORCE_VIEW%"
) else (
    set "VIEW=//... ..."
)

if defined BUILDKITE_PLUGIN_PERFORCE_STREAM (
    set "STREAM=%BUILDKITE_PLUGIN_PERFORCE_STREAM%"
) else (
    set "STREAM="
)

python -m pip install -r "%~dp0../python/requirements.txt"
python "%~dp0../python/checkout.py" --root "%ROOT%" --stream "%STREAM%" --view %VIEW%
