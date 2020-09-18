import unittest

import lookup.mhs_attribute_lookup as mhs_attribute_lookup
import lookup.routing_reliability as rar
import lookup.sds_exception as sds_exception
import lookup.tests.ldap_mocks as mocks
from utilities.test_utilities import async_test

PARTY_KEY = " AP4RTY-K33Y"
INTERACTION_ID = "urn:nhs:names:services:psis:MCCI_IN010000UK13"
ODS_CODE = "ODSCODE1"

EXPECTED_ROUTING_AND_RELIABILITY = {
    'nhsMHSAckRequested': 'always',
    'nhsMHSDuplicateElimination': 'always',
    'nhsMHSEndPoint': ['https://vpn-client-1411.opentest.hscic.gov.uk/'],
    'nhsMHSPartyKey': 'AP4RTY-K33Y',
    'nhsMHSPersistDuration': 'PT5M',
    'nhsMHSRetries': '2',
    'nhsMHSRetryInterval': 'PT1M',
    'nhsMHSSyncReplyMode': 'MSHSignalsOnly',
    'nhsMhsCPAId': 'S918999410559',
    'nhsMhsFQDN': 'vpn-client-1411.opentest.hscic.gov.uk',
    'uniqueIdentifier': ['123456789']
}


class TestRoutingAndReliability(unittest.TestCase):

    @async_test
    async def test_get_routing_and_reliability(self):
        router = self._configure_routing_and_reliability()

        mhs_route_details = await router.get_routing_and_reliability(ODS_CODE, INTERACTION_ID)

        self.assertEqual(mhs_route_details, EXPECTED_ROUTING_AND_RELIABILITY)

    @async_test
    async def test_get_routing_bad_ods_code(self):
        router = self._configure_routing_and_reliability()

        with self.assertRaises(sds_exception.SDSException):
            await router.get_routing_and_reliability("bad code", INTERACTION_ID)

    @async_test
    async def test_get_routing_bad_interaction_id(self):
        router = self._configure_routing_and_reliability()

        with self.assertRaises(sds_exception.SDSException):
            await router.get_routing_and_reliability(ODS_CODE, "bad interaction")

    @staticmethod
    def _configure_routing_and_reliability():
        handler = mhs_attribute_lookup.MHSAttributeLookup(mocks.mocked_sds_client())
        router = rar.RoutingAndReliability(handler)
        return router
