from typing import List

async def get_device_from_cpm(ods_code: str, interaction_id: str, manufacturing_organization: str = None, party_key: str = None) -> List:
    return [
        {
            "ods-code": ods_code,
            "interaction_id": interaction_id,
            "manufacturing_organisation": manufacturing_organization,
            "party_key": party_key
        }
    ]

async def get_endpoint_from_cpm(ods_code: str, interaction_id: str = None, party_key: str = None) -> List:
    return [
        {
            "ods-code": ods_code,
            "interaction_id": interaction_id,
            "party_key": party_key
        }
    ]