from unittest import TestCase
from unittest import mock

from utilities import test_utilities
from utilities.test_utilities import async_test

import lookup.mhs_attribute_lookup as mhs_attribute_lookup
import lookup.tests.ldap_mocks as mocks

NHS_SERVICES_BASE = "ou=services, o=nhs"

MHS_OBJECT_CLASS = "nhsMhs"

OPENTEST_LDAP_URL = "192.168.128.11"
PARTY_KEY = " AP4RTY-K33Y"
INTERACTION_ID = "urn:nhs:names:services:psis:MCCI_IN010000UK13"
ODS_CODE = "ODSCODE1"

expected_mhs_attributes = {
    'nhsEPInteractionType': 'HL7',
    'nhsIDCode': 'ODSCODE1',
    'nhsMHSAckRequested': 'always',
    'nhsMHSActor': ['urn:oasis:names:tc:ebxml-msg:actor:toPartyMSH'],
    'nhsMHSDuplicateElimination': 'always',
    'nhsMHSEndPoint': ['https://vpn-client-1411.opentest.hscic.gov.uk/'],
    'nhsMHSIsAuthenticated': 'transient',
    'nhsMHSPartyKey': 'AP4RTY-K33Y',
    'nhsMHSPersistDuration': 'PT5M',
    'nhsMHSRetries': '2',
    'nhsMHSRetryInterval': 'PT1M',
    'nhsMHSSyncReplyMode': 'MSHSignalsOnly',
    'nhsMHsIN': 'MCCI_IN010000UK13',
    'nhsMHsSN': 'urn:nhs:names:services:psis',
    'nhsMhsCPAId': 'S918999410559',
    'nhsMhsFQDN': 'vpn-client-1411.opentest.hscic.gov.uk',
    'nhsMhsSvcIA': 'urn:nhs:names:services:psis:MCCI_IN010000UK13',
    'nhsProductKey': '7374',
    'uniqueIdentifier': ['123456789']
}


class TestMHSAttributeLookup(TestCase):

    @async_test
    async def test_get_endpoint(self):
        handler = mhs_attribute_lookup.MHSAttributeLookup(mocks.mocked_sds_client())

        attributes = await handler.retrieve_mhs_attributes(ODS_CODE, INTERACTION_ID)

        self.assertEqual(expected_mhs_attributes, attributes)

    @async_test
    async def test_no_client(self):
        with self.assertRaises(ValueError):
            mhs_attribute_lookup.MHSAttributeLookup(None)
