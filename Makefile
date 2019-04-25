local_run: vendorize p4d
	bk local run .buildkite/local-pipeline.yml
	$(MAKE) clean_p4d

vendorize:
	mkdir .buildkite/plugins/perforce -p
	cp hooks python plugin.yml .buildkite/plugins/perforce/ -r
	# Checkout hook not available locally, so make a command hook instead
	cp .buildkite/plugins/perforce/hooks/checkout .buildkite/plugins/perforce/hooks/command 

p4d: clean_p4d
	unzip python/fixture/server.zip	-d python/fixture/server/
	p4d -r python/fixture/server &

clean_p4d:
	killall -9 p4d || true
	rm -f -r python/fixture/server
