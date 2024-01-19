# Spine Directory Service

![Build](https://github.com/NHSDigital/spine-directory-service-api/workflows/Build/badge.svg?branch=master)

This is a RESTful HL7® FHIR® API specification for the *Spine Directory Service API*.

* `specification/` This [Open API Specification](https://swagger.io/docs/specification/about/) describes the endpoints, methods and messages exchanged by the API. Use it to generate interactive documentation; the contract between the API and its consumers.
* `docker/sds-api/` This implements a mock implementation of the service. Use it as a back-end service to the interactive documentation to illustrate interactions and concepts. It is not intended to provide an exhaustive/faithful environment suitable for full development and testing.
* `scripts/` Utilities helpful to developers of this specification.
* `proxies/` Live (connecting to another service) and sandbox (using the sandbox container) Apigee API Proxy definitions.

Consumers of the API will find developer documentation on the [NHS Digital Developer Hub](https://portal.developer.nhs.uk/docs/spine-directory-service-int/1/overview).

## Contributing
Contributions to this project are welcome from anyone, providing that they conform to the [guidelines for contribution](https://github.com/NHSDigital/spine-directory/blob/master/CONTRIBUTING.md) and the [community code of conduct](https://github.com/NHSDigital/spine-directory/blob/master/CODE_OF_CONDUCT.md).

### Licensing
This code is dual licensed under the MIT license and the OGL (Open Government License). Any new work added to this repository must conform to the conditions of these licenses. In particular this means that this project may not depend on GPL-licensed or AGPL-licensed libraries, as these would violate the terms of those libraries' licenses.

The contents of this repository are protected by Crown Copyright (C).

## Development

### Requirements
* make
* nodejs + npm/yarn
* [poetry](https://github.com/python-poetry/poetry)


### Install
```
$ make install
```

### Local Install
<<<<<<< HEAD
```sh
cd docker/sds-api/spine-directory-service/sds
=======
```
cd docker/sda-api/spine-directory-service/sds
>>>>>>> a120cd6 (Bypass LDAP lookup)
python3 -m venv .venv
pipenv install
source .venv/bin/activate
```
Make sure VSCode is using the correct interpreter inside your .venv folder
Then you can run the VSCode debugger.

### Local Docker Install
Make sure you have docker buildx on your system.

```sh
cd docker/sds-api/spine-directory-service/sds
python3 -m venv .venv
pipenv install
You need to have pem and key files under data/certs, you may need to run a local copy to get these.
cd ../..
export BUILD_TAG='latest'
./buildx.sh
```
Connect to the VPN,

You may have issues with the container connecting via the VPN. If so please look at the answer given here https://superuser.com/questions/1579858/docker-bridge-network-sporadically-loosing-packets/1580017?_gl=1*wyte41*_ga*MjgwODQyNzEwLjE3MDYwMDMwNzQ.*_ga_S812YQPLT2*MTcwNjE5MjIyOC4yLjAuMTcwNjE5MjIyOC4wLjAuMA..#1580017 using `docker network create --subnet=172.20.0.0/24 --gateway=172.20.0.1 docker20`

Finally run
```sh
docker-compose up
```

#### Updating hooks
You can install some pre-commit hooks to ensure you can't commit invalid spec changes by accident. These are also run
in CI, but it's useful to run them locally too.

```
$ make install-hooks
```

### Environment Variables
Various scripts and commands rely on environment variables being set. These are documented with the commands.

:bulb: Consider using [direnv](https://direnv.net/) to manage your environment variables during development and maintaining your own `.envrc` file - the values of these variables will be specific to you and/or sensitive.

### Make commands
There are `make` commands that alias some of this functionality:
 * `lint` -- Lints the spec and code
 * `publish` -- Outputs the specification as a **single file** into the `build/` directory
 * `serve` -- Serves a preview of the specification in human-readable format

### Testing
Each API and team is unique. We encourage you to use a `test/` folder in the root of the project, and use whatever testing frameworks or apps your team feels comfortable with. It is important that the URL your test points to be configurable. We have included some stubs in the Makefile for running tests.

### VS Code Plugins

 * [openapi-lint](https://marketplace.visualstudio.com/items?itemName=mermade.openapi-lint) resolves links and validates entire spec with the 'OpenAPI Resolve and Validate' command
 * [OpenAPI (Swagger) Editor](https://marketplace.visualstudio.com/items?itemName=42Crunch.vscode-openapi) provides sidebar navigation


### Emacs Plugins

 * [**openapi-yaml-mode**](https://github.com/esc-emacs/openapi-yaml-mode) provides syntax highlighting, completion, and path help

### Speccy

> [Speccy](http://speccy.io/) *A handy toolkit for OpenAPI, with a linter to enforce quality rules, documentation rendering, and resolution.*

Speccy does the lifting for the following npm scripts:

 * `test` -- Lints the definition
 * `publish` -- Outputs the specification as a **single file** into the `build/` directory
 * `serve` -- Serves a preview of the specification in human-readable format

(Workflow detailed in a [post](https://developerjack.com/blog/2018/maintaining-large-design-first-api-specs/) on the *developerjack* blog.)

:bulb: The `publish` command is useful when uploading to Apigee which requires the spec as a single file.

### Caveats

#### Swagger UI
Swagger UI unfortunately doesn't correctly render `$ref`s in examples, so use `speccy serve` instead.

#### Apigee Portal
The Apigee portal will not automatically pull examples from schemas, you must specify them manually.

## Deployment

### Specification
Update the API Specification and derived documentation in the Portal.

`make deploy-spec` with environment variables:

* `APIGEE_USERNAME`
* `APIGEE_PASSWORD`
* `APIGEE_SPEC_ID`
* `APIGEE_PORTAL_API_ID`

### API Proxy & Sandbox Service
Redeploy the API Proxy and hosted Sandbox service.

`make deploy-proxy` with environment variables:

* `APIGEE_USERNAME`
* `APIGEE_PASSWORD`
* `APIGEE_ORGANIZATION`
* `APIGEE_ENVIRONMENTS` - Comma-separated list of environments to deploy to (e.g. `test,prod`)
* `APIGEE_APIPROXY` - Name of the API Proxy for deployment
* `APIGEE_BASE_PATH` - The proxy's base path (must be unique)

:bulb: Specify your own API Proxy (with base path) for use during development.

#### Platform setup

Successful deployment of the API Proxy requires:

 1. A *Target Server* named `spine-directory-target`

:bulb: For Sandbox-running environments (`test`) these need to be present for successful deployment but can be set to empty/dummy values.

### Sandbox

Sandbox environment mimics real service behaviour - both correct HTTP 200 and client error responses 4xx codes.
Both /Endpoint and /Device has built in one response with data that can be fetched using query parameters specified below. All other combinations result with empty FHIR bundle simulating no result found.

1. `/Endpoint`
- `organization=https://fhir.nhs.uk/Id/ods-organization-code|YES`
- `identifier=https://fhir.nhs.uk/Id/nhsEndpointServiceId|urn:nhs:names:services:psis:REPC_IN150016UK05`
- `identifier=https://fhir.nhs.uk/Id/nhsMhsPartyKey|YES-0000806`

Query parametere `organization` is mandatory. At least one `identifier` must be present.

Example: `/Endpoint?organization=https://fhir.nhs.uk/Id/ods-organization-code|YES&identifier=https://fhir.nhs.uk/Id/nhsEndpointServiceId|urn:nhs:names:services:psis:REPC_IN150016UK05&identifier=https://fhir.nhs.uk/Id/nhsMhsPartyKey|YES-0000806`

2. `/Device`
- `organization=https://fhir.nhs.uk/Id/ods-organization-code|YES`
- `identifier=https://fhir.nhs.uk/Id/nhsEndpointServiceId|urn:nhs:names:services:psis:REPC_IN150016UK05`
- `identifier=https://fhir.nhs.uk/Id/nhsMhsPartyKey|YES-0000806`
- `manufacturing-organization=https://fhir.nhs.uk/Id/ods-organization-code|YES`

Query parameters `organization` and `identifier(https://fhir.nhs.uk/Id/nhsEndpointServiceId)` are mandatory. One or both `identifier(https://fhir.nhs.uk/Id/nhsMhsPartyKey)` and `manufacturing-organization` can be supplied.

Example: `/Device?organization=https://fhir.nhs.uk/Id/ods-organization-code|YES&identifier=https://fhir.nhs.uk/Id/nhsEndpointServiceId|urn:nhs:names:services:psis:REPC_IN150016UK05&identifier=https://fhir.nhs.uk/Id/nhsMhsPartyKey|YES-0000806&manufacturing-organization=https://fhir.nhs.uk/Id/ods-organization-code|YES`
