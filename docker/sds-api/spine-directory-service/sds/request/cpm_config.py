import os
CPM_FILTER = "use_cpm"
CPM_FILTER_IDENTIFIER = "iwanttogetdatafromcpm"


def is_cpm_query(cpm_filter: str) -> bool:
    if os.environ.get("USE_CPM") == "1":
        return True
    return cpm_filter == CPM_FILTER_IDENTIFIER

DEVICE_FILTER_MAP = {
    "org_code": "nhs_id_code",
    "interaction_id": "nhs_as_svc_ia",
    "manufacturing_organization": "nhs_mhs_manufacturer_org",
    "party_key": "nhs_mhs_party_key"
}

ENDPOINT_FILTER_MAP = {
    "org_code": "nhs_id_code",
    "interaction_id": "nhs_mhs_svc_ia",
    "party_key": "nhs_mhs_party_key"
}

DEVICE_DATA_MAP = dict(
    nhs_as_svc_ia = "nhsAsSvcIA",
    nhs_mhs_manufacturer_org = "nhsMhsManufacturerOrg",
    nhs_mhs_party_key = "nhsMhsPartyKey",
    nhs_as_client = "nhsAsClient",
    nhs_id_code = "nhsIdCode",
    unique_identifier = "uniqueIdentifier"
)

ENDPOINT_DATA_MAP = dict(
    nhs_id_code = "nhsIDCode",
    nhs_mhs_ack_requested = "nhsMHSAckRequested",
    nhs_mhs_actor = "nhsMhsActor",
    nhs_mhs_cpa_id = "nhsMhsCPAId",
    nhs_mhs_duplicate_elimination = "nhsMHSDuplicateElimination",
    nhs_mhs_end_point = "nhsMHSEndPoint",
    nhs_mhs_fqdn = "nhsMhsFQDN",
    nhs_mhs_in = "nhsMHsIN",
    nhs_mhs_sn = "nhsMHsSN",
    nhs_mhs_svc_ia = "nhsMhsSvcIA",
    nhs_mhs_party_key = "nhsMHSPartyKey",
    nhs_mhs_persist_duration = "nhsMHSPersistDuration",
    nhs_mhs_retries = "nhsMHSRetries",
    nhs_mhs_retry_interval = "nhsMHSRetryInterval",
    nhs_mhs_sync_reply_mode = "nhsMHSSyncReplyMode",
    unique_identifier = "uniqueIdentifier"
)

DEFAULT_DEVICE_DICT = dict(
    nhsAsClient = [],
    nhsAsSvcIA = [],
    nhsMhsManufacturerOrg = "",
    nhsMhsPartyKey = "",
    nhsIdCode = "",
    uniqueIdentifier = []
)

DEFAULT_ENDPOINT_DICT = dict(
    nhsIDCode = "",
    nhsMHSAckRequested = "",
    nhsMhsActor = [],
    nhsMhsCPAId = "",
    nhsMHSDuplicateElimination = "",
    nhsMHSEndPoint = [],
    nhsMhsFQDN = "",
    nhsMHsIN ="",
    nhsMHSPartyKey = "",
    nhsMHSPersistDuration = "",
    nhsMHSRetries = 0,
    nhsMHSRetryInterval = "",
    nhsMHsSN = "",
    nhsMhsSvcIA = "",
    nhsMHSSyncReplyMode = "",
    uniqueIdentifier = []
)