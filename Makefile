local_run: vendorize p4d
	rm -rf p4_workspace
	mkdir -p local-pipeline
	cd local-pipeline && bk local run ../.buildkite/local-pipeline.yml --meta-data "buildkite-perforce-revision=@6"
	$(MAKE) clean_p4d

test:
	python3 -m pip install -r ./ci/requirements.txt
	./ci/test.sh

vendorize:
	mkdir -p local-pipeline/plugins/perforce
	cp -rf hooks python plugin.yml local-pipeline/plugins/perforce/
	# Checkout hook not available locally, so make a command hook instead
	cp -f local-pipeline/plugins/perforce/hooks/checkout local-pipeline/plugins/perforce/hooks/command

p4d: clean_p4d
	unzip python/fixture/server.zip	-d python/fixture/server/
	p4d -r python/fixture/server -p 1666 &

clean_p4d:
	# linux/osx
	killall -9 p4d || true
	# windows
	MSYS_NO_PATHCONV=1 taskkill /IM p4d.exe /F || true
	rm -rf python/fixture/server
