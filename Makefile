local_run: vendorize
	bk local run .buildkite/local-pipeline.yml

vendorize:
	mkdir .buildkite/plugins/perforce -p
	cp hooks python plugin.yml .buildkite/plugins/perforce/ -r
	# Checkout hook not available locally, so make a command hook instead
	cp .buildkite/plugins/perforce/hooks/checkout .buildkite/plugins/perforce/hooks/command 
	