from dataclasses import dataclass


@dataclass
class MatchingDeviceParameters:
    organization: str
    service_id: str
    party_key: str
    managing_organization: str

    def match(self, organization, service_id, party_key, managing_organization):
        return organization == self.organization and service_id == self.service_id \
               and (not party_key and not managing_organization
                    or managing_organization == self.managing_organization and not party_key
                    or not managing_organization and party_key == self.party_key
                    or managing_organization == self.managing_organization and party_key == self.party_key)


@dataclass
class MatchingEndpointParameters:
    organization: str
    service_id: str
    party_key: str

    def match(self, organization, service_id, party_key):
        return organization == self.organization \
               and (service_id == self.service_id and not party_key
                    or not service_id and party_key == self.party_key
                    or service_id == self.service_id and party_key == self.party_key)
