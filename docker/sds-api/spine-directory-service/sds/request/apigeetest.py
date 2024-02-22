import json
from request.error_handler import ErrorHandler
import requests
from utilities import timing

class ApigeeTest(ErrorHandler):

    @timing.time_request
    async def get(self):

        url = 'https://internal-dev-sandbox.api.service.nhs.uk/rowan-test-client/Organization/85be7bec-8ec5-11ee-b9d1-0242ac120002'
        
        headers = {
            'Authorization': 'letmein',
            'Content-Type': 'application/json',
            'apikey': 'hA0qKwUDOANnkR1diPorVAnnLdICgIjd',
            'version': '1'
        }
        
        response = requests.get(url, headers=headers)
        
        print('Response Status Code:', response.status_code)
        print('Response Content:', response.text)

        self.write(json.dumps(response, indent=2, sort_keys=False))
