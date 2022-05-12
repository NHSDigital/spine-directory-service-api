# Integration tests

Integration tests are sending predefined HTTP requests for all available actions:
* /Endpoint
to a running SDS instance running at `http://localhost:9000/`

Tests assume that target server is connected to test LDAP that supports `YES` organization code
and `urn:nhs:names:services:psis:REPC_IN150016UK05` service id.

Please ensure you are connected to the correct VPN to access the target server.

## Environment variables

Target SDS server url can be changed using `SDS_ADDRESS` environment variable

## Running tests

Assuming virtual environment has been created using `pipenv install --dev` command,
test can be run by executing `pipenv run inttests`

## BIG NOTE

When running against INT, you will get an error relating to "invalid attribute type nhsMhsManufacturerOrg" for some tests.
This is because the field is not present in the schema visible to the SDSAPI.  If you run from the shell , it will be visible, which will cause some confusion.....

The error is generated when search() in connection.py throws its toys out of the pram when nhsMhsManufacturerOrg is not found in self.server.schema.attribute_types .
