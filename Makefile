local_run: vendorize p4d
	rm -f -r p4_workspace
	mkdir local-pipeline -p
	cd local-pipeline && bk local run ../.buildkite/local-pipeline.yml --meta-data "buildkite-perforce-revision=@6"
	$(MAKE) clean_p4d

test:
	python3 -m pip install -r ./ci/requirements.txt
	./ci/test.sh

vendorize:
	mkdir local-pipeline/plugins/perforce -p
	cp hooks python plugin.yml local-pipeline/plugins/perforce/ -rf
	# Checkout hook not available locally, so make a command hook instead
	cp local-pipeline/plugins/perforce/hooks/checkout local-pipeline/plugins/perforce/hooks/command -f

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
