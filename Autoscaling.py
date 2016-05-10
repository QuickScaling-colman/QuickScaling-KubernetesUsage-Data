import urllib3
import json, time
from threading import Timer
from datetime import datetime

from Request import Request
from KuberneteaAPI import KubernetesApi
from MongoDBManager import MongoDBManager

class Autoscalling(object):
    '''

    Provides autoscale daemon functions

    '''
    def __init__(self, options, kube_api_obj):
        self._cfg = {}
        self._overrides = {}
        self._thresholds = {}
        self._parseCfg(options)

        self._kapi = kube_api_obj

        self._running = False
        self._nodes = {}
        self._average = {}
        self._group_status = {}
        self._actions = []

        self._suffixes = {
            'Ki': 2**10, 'Mi': 2**20, 'Gi': 2**30, 'Ti': 2**40, 'Pi': 2**50, 'Ei': 2**60,
            'n': 10**-9, 'u': 10**-6, 'm': 10**-3, 'k': 10**3, 'M': 10**6, 'G': 10**9, 'T': 10**12, 'P': 10**15, 'E': 10**18
        }

    def _parseCfg(self, cfg):
        self._cfg = cfg
        self._thresholds = {
            'create': {},
            'delete': {}
        }

        for key in self._cfg:
            if cfg[key] != None:
                keys = key.split('/', 1)
                if keys[0] == 'override':
                    self._overrides[keys[1]] = cfg[key]
                elif keys[0] in self._thresholds:
                    self._thresholds[keys[0]][keys[1]] = cfg[key]

    def _suffix(self, value):
        '''

        Convert value with suffix to numeric value

        '''
        if not value[-1].isdigit():
            if not value[-2].isdigit():
                value, suffix = int(value[0:-2]), value[-2:]
            else:
                value, suffix = int(value[0:-1]), value[-1:]
            value *= self._suffixes[suffix]
        else:
            value = int(value)

        return value

    def _getStatusAverage(self, status):
        l = [ self._nodes[p]['status'][status] for p in self._nodes ]
        m = [ self._nodes[p]['status']['%s_max' % status] for p in self._nodes ]
        return float(sum(l))/(sum(m)) if len(l) > 0 else 0

    def _node(self, data=None):
        if (data == None):
            data = {}
        return {
            'data': data,
            'pods': [],
            'status': {
                'pods_max': 0,
                'pods': 0,
                'cpu_max': 0,
                'cpu': 0,
                'memory_max': 0,
                'memory': 0
            },
            'state': None,
            'action': None
        }

    def updateInfo(self):
        new_nodes = {}

        # TODO: use streams to retreive updated data online
        pods = self._kapi.getPods()['items']
        nodes = self._kapi.getNodes()['items']

        for node in nodes:
            new_nodes[node['metadata']['name']] = self._node(node)

        for pod in pods:
            node = pod['spec']['nodeName'] if 'nodeName' in pod['spec'] else 'UNKNOWN'
            if not node in new_nodes:
                new_nodes[node] = self._node(None)
                new_nodes[node]['action'] = 'NONE'

            # Ignore minion node agents
            if not pod['metadata']['name'].endswith(node):
               new_nodes[node]['pods'].append(pod)

        for node in new_nodes:
            if node == 'UNKNOWN':
                continue
            n = new_nodes[node]
            req = [ c['resources']['requests'] for sublist in [ p['spec']['containers'] for p in n['pods'] ] for c in sublist if 'requests' in c['resources'] ]
            cpu = [ self._suffix(r['cpu']) for r in req if 'cpu' in r ]
            memory = [ self._suffix(r['memory']) for r in req if 'memory' in r ]
            new_nodes[node]['status'] = {
                'pods_max': int(new_nodes[node]['data']['status']['capacity']['pods']) - 1, # except node daemon pod
                'pods': len(new_nodes[node]['pods']),
                'cpu_max': self._suffix(new_nodes[node]['data']['status']['capacity']['cpu']),
                'cpu': sum(cpu),
                'memory_max': self._suffix(new_nodes[node]['data']['status']['capacity']['memory']),
                'memory': sum(memory)
            }
            for key in self._overrides:
                new_nodes[node]['status'][key] = self._overrides[key]

        # TODO: use kubernetes history to update just changed data
        self._nodes = new_nodes

        self._average = {
            'pods': self._getStatusAverage('pods'),
            'cpu': self._getStatusAverage('cpu'),
            'memory': self._getStatusAverage('memory')
        }

    def printReport(self):
        print 'Report:'

        print '  Cluster:'
        for avg in self._average:
            print '    {}: {}'.format(avg, self._average[avg])

        print
        print '  Nodes:'
        for node in self._nodes:
            n = self._nodes[node]
            print '    {name}: # State: {state}, Action: {action}, Pods: {pods}/{pods_max}, CPU: {cpu}/{cpu_max}, Mem: {mem}/{mem_max}MB'.format(
                name = node,
                state = n['state'], action = n['action'],
                pods = n['status']['pods'], pods_max = n['status']['pods_max'],
                cpu = n['status']['cpu'], cpu_max = n['status']['cpu_max'],
                mem = n['status']['memory']/1048576, mem_max = n['status']['memory_max']/1048576
            )
            for pod in n['pods']:
                if not pod['metadata']['namespace'] in [ name.strip() for name in self._cfg['report/ignore-namespaces'].split(',') ]:
                    print '      %s %s: %s' % (pod['status']['phase'], pod['metadata']['namespace'], pod['metadata']['name'])

        print

    def addRecordsToMongoDB(self):
        mongo = MongoDBManager()
        for node in self._nodes:
            n = self._nodes[node]
            name = node
            cpu = n['status']['cpu']
            cpu_max = n['status']['cpu_max']
            mem = (n['status']['memory'] / 1048576)
            mem_max = (n['status']['memory_max'] / 1048576)
            record = {'hostname': name, 'cpu': cpu, 'cpu_max': cpu_max, 'memory': mem , 'memory_max': mem_max , 'create_at': datetime.date().strftime("%d-%m-%Y")}
            mongo.addRecord(record=record)

    def run(self):
        self.updateInfo()
        self.addRecordsToMongoDB()
