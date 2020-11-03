"""This module defines the component used to orchestrate the retrieval and caching of routing and reliability
information for a remote MHS."""

from typing import Dict

from utilities import integration_adaptors_logger as log

import lookup.sds_client as sds_client

logger = log.IntegrationAdaptorsLogger(__name__)


class MHSAttributeLookup(object):
    """A tool that allows the routing and reliability information for a remote MHS to be retrieved."""

    def __init__(self, client: sds_client.SDSClient):
        """
        :param client The SDS client to use when retrieving remote MHS details.
        """
        if not client:
            raise ValueError('sds client required')
        self.sds_client = client

    async def retrieve_mhs_attributes(self, ods_code, interaction_id) -> Dict:
        """Obtains the attributes of the MHS registered for the given ODS code and interaction ID.
        :param ods_code:
        :param interaction_id:
        :return:
        """
        endpoint_details = await self.sds_client.get_mhs_details(ods_code, interaction_id)
        logger.info('MHS details obtained from sds for {ods_code} & {interaction_id}',
                    fparams={'ods_code': ods_code, 'interaction_id': interaction_id})

        return endpoint_details
