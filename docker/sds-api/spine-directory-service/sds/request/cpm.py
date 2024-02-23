import requests

from typing import List

async def get_device_from_cpm(ods_code: str, interaction_id: str, manufacturing_organization: str = None, party_key: str = None) -> List:
    endpoint = 'Organization/85be7bec-8ec5-11ee-b9d1-0242ac120002'
    #endpoint = '_status'
    result = await request_cpm_data(endpoint=endpoint, params=[])
    return [
        {
            'uniqueIdentifier': [result]
        }
    ]
    # filtered_data = filter_cpm_response(result)
    # transformed_data = transform_to_SDS(data=filtered_data)
    # return transformed_data

async def get_endpoint_from_cpm(ods_code: str, interaction_id: str = None, party_key: str = None) -> List:
    return [
        {
            "ods-code": ods_code,
            "interaction_id": interaction_id,
            "party_key": party_key
        }
    ]

async def request_cpm_data(endpoint: str, params: list) -> dict:
    headers = {
        'version': '1',
        'Authorization': 'letmein',
        'Content-Type': 'application/json',
        'apikey': 'hA0qKwUDOANnkR1diPorVAnnLdICgIjd',
    }
    try:
        result = requests.get(f'https://internal-dev-sandbox.api.service.nhs.uk/rowan-test-client/{endpoint}', headers=headers) #, params=params #)
        return result.status_code
    except requests.exceptions.RequestException as e:
        return "no response"

def filter_cpm_response(data: dict):
    return data

def transform_to_SDS(data: dict) -> List:
    ldap_data = [data]
    # [
    #     {
    #         'nhsAsClient': ['YES'], 
    #         'nhsAsSvcIA': [
    #            'urn:nhs:names:services:psis:REPC_IN150015UK05', 
    #            'urn:nhs:names:services:psis:REPC_IN150016UK05', 
    #            'urn:nhs:names:services:psis:REPC_IN150017UK02', 
    #            'urn:nhs:names:services:psis:REPC_IN150018UK02', 
    #            'urn:nhs:names:services:psis:MCCI_IN010000UK13', 
    #         ], 
    #         'nhsIdCode': 'YES', 
    #         'nhsMhsManufacturerOrg': 'X09001', 
    #         'nhsMhsPartyKey': 'YES-0000806', 
    #         'uniqueIdentifier': ['227319907548']
    #     }
    # ]
    return ldap_data
