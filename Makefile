# Checkout hook not available locally, so make a command hook instead for iteration via bk local run.
local:
	cp hooks/checkout hooks/command 
	bk local run .buildkite/pipeline.yml; rm hooks/command
	