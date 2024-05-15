SHELL=/bin/bash -euo pipefail

guard-%:
	@ if [ "${${*}}" = "" ]; then \
		echo "Environment variable $* not set"; \
		exit 1; \
	fi

install: install-node install-python install-hooks

install-python:
	poetry install

install-node:
	npm install

install-hooks:
	cp scripts/pre-commit .git/hooks/pre-commit

lint:
	# npm run lint
	# cd docker/adaptor && npm run lint && cd ..
	# poetry run flake8 **/*.py
	# find -name '*.sh' | grep -v node_modules | xargs shellcheck

clean:
	rm -rf build
	rm -rf dist

publish: clean
	mkdir -p build
	npm run publish 2> /dev/null

serve:
	npm run serve

generate-examples: publish clean
	mkdir -p build/examples
	poetry run python scripts/generate_examples.py build/spine-directory-service.json build/examples
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

build-proxy:
	scripts/build_proxy.sh

_dist_include="pytest.ini poetry.lock poetry.toml pyproject.toml Makefile build/. tests"

release: clean publish build-proxy
	mkdir -p dist
	for f in $(_dist_include); do cp -r $$f dist; done
	cp ecs-proxies-deploy-internal-dev.yml dist/ecs-deploy-internal-dev.yml
	cp ecs-proxies-deploy-internal-qa.yml dist/ecs-deploy-internal-qa.yml
	cp ecs-proxies-deploy-int.yml dist/ecs-deploy-int.yml
	cp ecs-proxies-deploy-ref.yml dist/ecs-deploy-ref.yml
	cp ecs-proxies-deploy-dep.yml dist/ecs-deploy-dev.yml
	cp ecs-proxies-deploy-prod.yml dist/ecs-deploy-prod.yml
	cp ecs-proxies-deploy-internal-qa-sandbox.yml dist/ecs-deploy-internal-qa-sandbox.yml
	cp ecs-proxies-deploy-sandbox.yml dist/ecs-deploy-sandbox.yml
	cp ecs-proxies-deploy-internal-dev-sandbox.yml dist/ecs-deploy-internal-dev-sandbox.yml

dist: release

#################
# Test commands #
#################

TEST_CMD := @APIGEE_ACCESS_TOKEN=$(APIGEE_ACCESS_TOKEN) \
		poetry run pytest -v \
		--color=yes \
		--api-name=spine-directory-service \
		--proxy-name=$(PROXY_NAME) \
		-s

PROD_TEST_CMD := $(TEST_CMD) \
		--apigee-app-id=$(APIGEE_APP_ID) \
		--apigee-organization=nhsd-prod \
		--status-endpoint-api-key=$(STATUS_ENDPOINT_API_KEY)

#Command to run end-to-end smoketests post-deployment to verify the environment is working
test:
	$(TEST_CMD) \
	--junitxml=test-report.xml \

smoketest:
	$(TEST_CMD) \
	--junitxml=smoketest-report.xml \
	-m smoketest

e2etest:
	$(TEST_CMD) \
	--junitxml=test-report.xml \
	-m e2e

securitytest:
	$(TEST_CMD) \
	--junitxml=test-report.xml \
	-m securitytest

test-prod:
	$(PROD_CMD) \
	--junitxml=test-report.xml \

smoketest-prod:
	$(PROD_TEST_CMD) \
	--junitxml=smoketest-report.xml \
	-m smoketest

e2etest-prod:
	$(PROD_CMD) \
	--junitxml=test-report.xml \
	-m e2e

securitytest-prod:
	$(PROD_CMD) \
	--junitxml=test-report.xml \
	-m securitytest
