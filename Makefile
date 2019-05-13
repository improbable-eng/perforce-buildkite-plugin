local_run: vendorize p4d
	rm -f -r p4_workspace
	bk local run .buildkite/local-pipeline.yml
	$(MAKE) clean_p4d

test:
	python3 -m pip install -r ./ci/requirements.txt
	./ci/test.sh

vendorize:
	mkdir .buildkite/plugins/perforce -p
	cp hooks python plugin.yml .buildkite/plugins/perforce/ -rf
	# Checkout hook not available locally, so make a command hook instead
	cp .buildkite/plugins/perforce/hooks/checkout .buildkite/plugins/perforce/hooks/command -f

# p4d: export P4SSLDIR=sslkeys
p4d: clean_p4d
	unzip python/fixture/server.zip	-d python/fixture/server/
	# mkdir python/fixture/server/sslkeys
	# chmod 700 python/fixture/server/sslkeys
	# p4d -r python/fixture/server -Gc
	# p4d -r python/fixture/server -Gf
	p4d -r python/fixture/server -p 1666 &

clean_p4d:
	killall -9 p4d || true
	rm -f -r python/fixture/server
