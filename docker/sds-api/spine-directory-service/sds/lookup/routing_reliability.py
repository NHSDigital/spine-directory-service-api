"""This module defines the component used to look up routing and reliability information for a remote MHS."""

import lookup.mhs_attribute_lookup as mhs_attribute_lookup

ROUTING_AND_RELIABILITY_KEYS = [
    'nhsMhsFQDN',
    'nhsMHSEndPoint',
    'nhsMHSPartyKey',
    'nhsMhsCPAId',
    'uniqueIdentifier',
    'nhsMHSSyncReplyMode',
    'nhsMHSRetryInterval',
    'nhsMHSRetries',
    'nhsMHSPersistDuration',
    'nhsMHSDuplicateElimination',
    'nhsMHSAckRequested'
]


class RoutingAndReliability(object):
    """A tool that allows the routing and reliability information for a remote MHS to be retrieved."""

    def __init__(self, lookup_handler: mhs_attribute_lookup.MHSAttributeLookup):
        if not lookup_handler:
            raise ValueError("MHS Attribute Lookup Handler not found")
        self.lookup = lookup_handler

    async def get_routing_and_reliability(self, org_code, service_id, party_key):
        """Get the endpoint of the MHS registered for the specified org code and service ID.

        :param org_code:
        :param service_id:
        :param party_key:
        :return:
        """
        endpoint_details = await self.lookup.retrieve_mhs_attributes(org_code, service_id, party_key)
        return list(map(self._map_endpoint_details, endpoint_details))

    @staticmethod
    def _map_endpoint_details(endpoint_details):
        return {item: endpoint_details[item] for item in ROUTING_AND_RELIABILITY_KEYS}
