SHELL=/bin/bash -euo pipefail

install: install-node install-python install-hooks

install-python:
	poetry install

install-node:
	npm install
	# cd sandbox && npm install

install-hooks:
	cp scripts/pre-commit .git/hooks/pre-commit

lint:
	# npm run lint
	# cd docker/sandbox && npm run lint && cd ..
	# cd docker/adaptor && npm run lint && cd ..
	# poetry run flake8 **/*.py
	# find -name '*.sh' | grep -v node_modules | xargs shellcheck

clean:
	rm -rf build
	rm -rf dist

publish: clean
	mkdir -p build
	npm run publish

serve:
	npm run serve

generate-examples: publish clean
	mkdir -p build/examples
	poetry run python scripts/generate_examples.py build/spine-directory.json build/examples
	scripts/duplicate_examples.sh

update-examples: generate-examples
	scripts/update_examples.sh
	make publish

check-licenses:
	npm run check-licenses
	scripts/check_python_licenses.sh

deploy-proxy:
	scripts/deploy_proxy.sh

deploy-spec:
	scripts/deploy_spec.sh

format:
	poetry run black **/*.py

sandbox:
	cd sandbox && npm run start

build-proxy:
	scripts/build_proxy.sh

release: clean publish build-proxy
	mkdir -p dist
	cp -r build/. dist
	cp ecs-proxies-deploy.yml dist/ecs-deploy-internal-dev.yml
	cp ecs-proxies-deploy.yml dist/ecs-deploy-internal-qa.yml
	cp ecs-proxies-deploy-sandbox.yml dist/ecs-deploy-internal-qa-sandbox.yml
	cp ecs-proxies-deploy-sandbox.yml dist/ecs-deploy-sandbox.yml
	cp ecs-proxies-deploy.yml dist/ecs-deploy-int.yml
	cp ecs-proxies-deploy.yml dist/ecs-deploy-ref.yml
#	cp ecs-proxies-deploy.yml dist/ecs-deploy-prod.yml

test:
	echo "TODO: add tests"
