# Checkout hook not available locally, so make a command hook instead for iteration via bk local run.
local:
	cp .buildkite/plugins/perforce/hooks/checkout .buildkite/plugins/perforce/hooks/command 
	bk local run .buildkite/pipeline.yml; rm .buildkite/plugins/perforce/hooks/command
	