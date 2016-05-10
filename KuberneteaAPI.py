import urllib3
import json, time
from threading import Timer

import Request

class KubernetesApi(object):
    '''

    Provides access to Kubernetes API

    '''
    def __init__(self, request_obj):
        self._req = request_obj

    def getNodes(self):
        '''

        Get current nodes list

        '''
        return self._req.json(self._req.get('nodes'))

    def getPods(self):
        '''

        Get current pods list

        '''
        return self._req.json(self._req.get('pods'))