import urllib3
import json, time
from threading import Timer

class Request(object):
    '''

    Simple http/https request class
    in case that we will need to you more clients that have api
    AWS and etc

    '''
    def __init__(self, api_url = 'https://localhost/api/v1',
            user = None, password = None,
            headers = None, cert = None):

        self._headers = headers if headers else {}
        if user and password:
            self._headers.update(urllib3.util.make_headers(basic_auth=':'.join([user, password])))

        self._api_url = api_url
        if api_url.startswith('https://'):
            # TODO: check cert
            self._urlpool = urllib3.PoolManager(cert_reqs='CERT_REQUIRED' if cert else 'CERT_NONE', ca_certs=None)
        else:
            self._urlpool = urllib3.PoolManager()

    def json(self, json_string):
        '''

        Parse json & return dict
        json_string - a regular string that need to be converted to json type

        '''
        try:
            return json.loads(json_string)
        except ValueError:
            raise Exception({'message': 'Response parsing error: %s' % json_string})

    @property
    def api(self):
        return self._api_url

    def setHeaders(self, headers):
        self._headers = headers

    def get(self, request, data = None, api_url = None):
        '''

        Do GET request to api

        '''
        response = self._urlpool.request('GET', '%s/%s' % (
            api_url if api_url else self._api_url,
            request), headers = self._headers)
        if( response.status != 200 ):
            raise Exception({'message': 'Got status error: %d, %s (%s)' % (response.status, response.data, request)})

        return response.data

    def post(self, request, data = None, api_url = None, content_type = 'application/json'):
        '''

        Do POST request to api

        '''
        newheaders = {'Content-Type': content_type, 'Content-Length': len(data) if data else 0}
        newheaders.update(self._headers)
        response = self._urlpool.urlopen('POST', '%s/%s' % (
            api_url if api_url else self._api_url,
            request), body=data, headers=newheaders)
        if( response.status != 200 ):
            raise Exception({'message': 'Got status error: %d, %s (%s)' % (response.status, response.data, request)})

        return response.data