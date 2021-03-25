"""This module contains the client used to make requests to SDS."""

import ast
import asyncio
import random
from typing import Dict, List, Tuple, Optional

import ldap3
import ldap3.core.exceptions as ldap_exceptions

from lookup.sds_exception import SDSException
from utilities import config
from utilities import integration_adaptors_logger as log
from utilities.string_utilities import str2bool

logger = log.IntegrationAdaptorsLogger(__name__)

MHS_OBJECT_CLASS = "nhsMhs"
AS_OBJECT_CLASS = "nhsAs"
MHS_PARTY_KEY = 'nhsMHSPartyKey'
MHS_ASID = 'uniqueIdentifier'

MHS_ATTRIBUTES = [
    'nhsIDCode', 'nhsMhsCPAId', 'nhsMHSEndPoint', 'nhsMhsFQDN',
    'nhsMHsIN', 'nhsMHSPartyKey', 'nhsMHsSN', 'nhsMhsSvcIA',
    'uniqueIdentifier', 'nhsMHSAckRequested', 'nhsMHSDuplicateElimination',
    'nhsMHSPersistDuration', 'nhsMHSRetries', 'nhsMHSRetryInterval', 'nhsMHSSyncReplyMode'
]
AS_ATTRIBUTES = [
    'uniqueIdentifier', 'nhsIdCode', 'nhsAsClient', 'nhsMhsPartyKey', 'nhsAsSvcIA'
]


class SDSClient(object):
    """A client that can be used to query SDS."""

    def __init__(self, sds_connection: ldap3.Connection, search_base: str, timeout: int = 3):
        """
        :param sds_connection: takes an ldap connection to the sds server
        :param search_base: The LDAP location to use as the base of SDS searches. e.g. ou=services,o=nhs.
        :param timeout The amount of time to wait for an LDAP query to complete.
        """
        if not sds_connection:
            raise ValueError('sds_connection must not be null')

        if not search_base:
            raise ValueError('search_base must be specified')

        self.connection = sds_connection
        self.timeout = timeout
        self.search_base = search_base

    @staticmethod
    def _build_search_filter(query_parts):
        search_filter = " ".join(map(lambda kv: f"({kv[0]}={kv[1]})", filter(lambda kv: kv[1] is not None, query_parts)))
        search_filter = f"(&{search_filter})"
        return search_filter

    async def get_mhs_details(self, ods_code: str, interaction_id: str = None, party_key: str = None) -> List[Dict]:
        """
        Returns the mhs details for the given parameters

        :return: Dictionary of the attributes of the mhs associated with the given parameters
        """
        if not ods_code or (not interaction_id and not party_key):
            raise SDSException("org_code and at least one of 'interaction_id' or 'party_key' must be provided")

        query_parts = [
            ("nhsIDCode", ods_code),
            ("objectClass", "nhsMhs"),
            ("nhsMhsSvcIA", interaction_id),
            ("nhsMHSPartyKey", party_key)
        ]
        result = await self._get_ldap_data(query_parts, MHS_ATTRIBUTES)
        return result

    async def get_gpc_structured_details(self, ods_code: str, interaction_id: str = None, party_key: str = None) -> List[Dict]:
        """
        Returns the gpc structured details for the given parameters

        :return: Dictionary of the attributes of the mhs associated with the given parameters
        """
        if not ods_code or (not interaction_id and not party_key):
            raise SDSException("org_code and at least one of 'interaction_id' or 'party_key' must be provided")

        query_parts = [
            ("nhsIDCode", ods_code),
            ("objectClass", "nhsMhs"),
            ("nhsMhsSvcIA", interaction_id),
            ("nhsMHSPartyKey", party_key)
        ]
        result = await self._get_ldap_data(query_parts, MHS_ATTRIBUTES)
        return result

    async def get_as_details(self, ods_code: str, interaction_id: str, managing_organization: str = None, party_key: str = None) -> List[Dict]:
        """
        Returns the device details for the given parameters

        :return: Dictionary of the attributes of the device associated with the given parameters
        """
        if not ods_code or not interaction_id:
            raise SDSException("org_code and interaction_id must be provided")

        query_parts = [
            ("nhsIDCode", ods_code),
            ("objectClass", "nhsAs"),
            ("nhsAsSvcIA", interaction_id),
            ("nhsMhsManufacturerOrg", managing_organization),
            ("nhsMHSPartyKey", party_key)
        ]

        # TODO: can't use atm with Opentest as it lacks required schema attribute
        if str2bool(config.get_config('DISABLE_MANUFACTURER_ORG_SEARCH_PARAM', default=str(False))):
            query_parts.remove(("nhsMhsManufacturerOrg", managing_organization))

        result = await self._get_ldap_data(query_parts, AS_ATTRIBUTES)
        return result

    async def _get_ldap_data(self, query_parts: List[Tuple[str, Optional[str]]], attributes: List[str]) -> List:
        search_filter = self._build_search_filter(query_parts)

        self.connection.bind()
        message_id = self.connection.search(search_base=self.search_base,
                                            search_filter=search_filter,
                                            attributes=attributes)
        logger.info("Received LDAP query {message_id} - for query: {search_filter}",
                    fparams={"message_id": message_id, "search_filter": search_filter})

        response = await self._get_query_result(message_id)
        logger.info("Found LDAP details for {message_id}", fparams={"message_id": message_id})

        attributes_result = [single_result['attributes'] for single_result in response]
        return attributes_result

    async def _get_query_result(self, message_id: int) -> List:
        loop = asyncio.get_event_loop()
        response = []
        try:
            response, result = await loop.run_in_executor(None, self.connection.get_response, message_id, self.timeout)
        except ldap_exceptions.LDAPResponseTimeoutError:
            logger.error("LDAP query timed out for {message_id}", fparams={"message_id": message_id})

        return response


class SDSMockClient:

    def __init__(self):
        self.pause_duration = int(config.get_config('MOCK_LDAP_PAUSE', default="0"))
        self.mode = config.get_config('MOCK_LDAP_MODE', default="STRICT").upper()
        self.mock_mhs_data = None
        self.mock_as_data = None
        self._read_mock_data()

    async def get_mhs_details(self, ods_code: str, interaction_id: str, party_key: str) -> List[Dict]:
        if ods_code is None or interaction_id is None and party_key is None:
            raise ValueError

        if self.pause_duration != 0:
            logger.debug("Sleeping for %sms", self.pause_duration)
            await asyncio.sleep(self.pause_duration / 1000)

        if self.mode == "STRICT":
            return list(filter(lambda x: self._filter_mhs(x, ods_code, interaction_id, party_key), self.mock_mhs_data))
        elif self.mode == "RANDOM":
            return [random.choice(self.mock_mhs_data)]
        elif self.mode == "FIRST":
            return [self.mock_mhs_data[0]]
        else:
            raise ValueError

    async def get_as_details(self, ods_code: str, interaction_id: str, managing_organization: str = None, party_key: str = None) -> List[Dict]:
        if ods_code is None or interaction_id is None:
            raise ValueError

        if self.pause_duration != 0:
            logger.debug("Sleeping for %sms", self.pause_duration)
            await asyncio.sleep(self.pause_duration / 1000)

        if self.mode == "STRICT":
            return list(filter(lambda x: self._filter_as(x, ods_code, interaction_id, managing_organization, party_key), self.mock_as_data))
        elif self.mode == "RANDOM":
            return [random.choice(self.mock_as_data)]
        elif self.mode == "FIRST":
            return [self.mock_as_data[0]]
        else:
            raise ValueError

    async def get_gpc_structured_details(self, ods_code: str, interaction_id: str, managing_organization: str = None, party_key: str = None) -> List[Dict]:
        if ods_code is None or interaction_id is None:
            raise ValueError

        if self.pause_duration != 0:
            logger.debug("Sleeping for %sms", self.pause_duration)
            await asyncio.sleep(self.pause_duration / 1000)

        if self.mode == "STRICT":
            return list(filter(lambda x: self._filter_as(x, ods_code, interaction_id, managing_organization, party_key), self.mock_as_data))
        elif self.mode == "RANDOM":
            return [random.choice(self.mock_gpc_structured_data)]
        elif self.mode == "FIRST":
            return [self.mock_gpc_structured_data[0]]
        else:
            raise ValueError

    @staticmethod
    def _filter_mhs(entry: Dict, ods_code: str, interaction_id: str, party_key: str):
        return entry['nhsIDCode'] == ods_code \
            and (interaction_id is None or entry['nhsMhsSvcIA'] == interaction_id) \
            and (party_key is None or entry['nhsMHSPartyKey'] == party_key)

    @staticmethod
    def _filter_as(entry: Dict, ods_code: str, interaction_id: str, managing_organization: str = None, party_key: str = None):
        return entry['nhsIDCode'] == ods_code \
            and interaction_id in entry['nhsAsSvcIA'] \
            and (party_key is None or entry['nhsMHSPartyKey'] == party_key) \
            and (managing_organization is None or entry['nhsMhsManufacturerOrg'] == managing_organization)

    def _read_mock_data(self):
        with open('./lookup/mock_data/sds_mhs_response.json', 'r') as f:
            data = f.read()
            self.mock_mhs_data = ast.literal_eval(data)

        with open('./lookup/mock_data/sds_as_response.json', 'r') as f:
            data = f.read()
            self.mock_as_data = ast.literal_eval(data)

        with open('./lookup/mock_data/sds_gpc_response.json', 'r') as f:
            data = f.read()
            self.mock_gpc_data = ast.literal_eval(data)

        with open('./lookup/mock_data/sds_gpc_get_structured.json', 'r') as f:
            data = f.read()
            self.mock_gpc_structured_data = ast.literal_eval(data)