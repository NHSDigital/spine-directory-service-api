import asyncio
import json
from typing import Dict, Optional

import redis
from utilities import integration_adaptors_logger as log, timing

from lookup import cache_adaptor

logger = log.IntegrationAdaptorsLogger(__name__)


class NoCacheCache(cache_adaptor.CacheAdaptor):

    @timing.time_function
    async def retrieve_mhs_attributes_value(self, ods_code: str, interaction_id: str) -> Optional[Dict]:
        """
        Returns  None every time to bypass cache

        :param ods_code: The ODS code the value belongs to. Used to construct the Redis key.
        :param interaction_id: The interaction ID code the value belongs to. Used to construct the Redis key.
        :return None
        """
        return None

    @timing.time_function
    async def add_cache_value(self, ods_code: str, interaction_id: str, value: Dict) -> None:
        """
        Adds a value to the cache. Does not raise any exceptions if errors are encountered.

        :param ods_code: The ODS code the value belongs to. Used to construct the Redis key.
        :param interaction_id: The interaction ID code the value belongs to. Used to construct the Redis key.
        :param value: The value to be cached.
        """
        return

    @staticmethod
    def _generate_key(ods_code: str, interaction_id: str) -> str:
        return ods_code + '-' + interaction_id
