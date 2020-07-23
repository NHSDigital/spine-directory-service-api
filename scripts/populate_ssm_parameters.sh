#!/bin/bash
set -euo pipefail

function copy-secret {
    secretValue="$(
        aws secretsmanager get-secret-value \
        --profile build-sds-coordinator \
        --secret-id "$1" \
        --query SecretString \
        --output text
    )"

    aws ssm put-parameter \
        --profile build-sds-coordinator \
        --name "$2" \
        --value "$secretValue" \
        --type SecureString \
        --overwrite
}

function copy-parameter {
    secretValue="$(
        aws ssm get-parameter \
        --profile build-sds-coordinator \
        --name "$1" \
        --query Parameter.Value \
        --output text
    )"

    aws ssm put-parameter \
        --profile build-sds-coordinator \
        --name "$2" \
        --value "$secretValue" \
        --type String \
        --overwrite
}

copy-secret "ptl/cis/ldap.nis1.national.ncrs.nhs.uk/key" "/ptl/api-deployment/sds/ldap/private-key"
copy-secret "ptl/cis/ldap.nis1.national.ncrs.nhs.uk/crt" "/ptl/api-deployment/sds/ldap/client-cert"
copy-secret "ptl/veit07.devspineservices.nhs.uk/root-ca/crt" "/ptl/api-deployment/sds/ldap/ca-certs"
