import urllib3
import json, time
from threading import Timer
from datetime import datetime

from Request import Request
from KuberneteaAPI import KubernetesApi
from MongoDBManager import MongoDBManager
from Autoscaling import Autoscalling

if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(usage='./%(prog)s [options] [@argsfile]', description=__doc__, fromfile_prefix_chars='@')
    parser.add_argument("--kubernetes-api-url", dest="kubernetes/api-url", metavar="APIURL", help="Kubernetes: url api like https://<host>/api/v1")
    parser.add_argument("--kubernetes-user", dest="kubernetes/user", metavar="NAME", help="Kubernetes: user name or service account")
    parser.add_argument("--kubernetes-token", dest="kubernetes/token", metavar="TOKEN", help="Kubernetes: token or user password")
    parser.add_argument("--kubernetes-max-minions", dest="kubernetes/max-minions", type=int, default=100, metavar="NUM", help="Kubernetes: maximum cluster size")
    parser.add_argument("--create-pods", dest="create/pods", type=float, metavar="0<NUM<1", help="Create new node threshold: num of pods per node")
    parser.add_argument("--delete-pods", dest="delete/pods", type=float, metavar="0<NUM<1", help="Delete node threshold: num of pods per node")
    parser.add_argument("--create-cpu", dest="create/cpu", type=float, metavar="0<NUM<1", help="Create new node threshold: CPU limit per CPUs in cluster")
    parser.add_argument("--delete-cpu", dest="delete/cpu", type=float, metavar="0<NUM<1", help="Delete node threshold: CPU limit per CPUs in cluster")
    parser.add_argument("--create-memory", dest="create/memory", type=float, metavar="0<NUM<1", help="Create new node threshold: CPU limit per CPUs in cluster")
    parser.add_argument("--delete-memory", dest="delete/memory", type=float, metavar="0<NUM<1", help="Delete node threshold: CPU limit per CPUs in cluster")
    parser.add_argument("--delay-create", dest="delay/create", type=int, default=0, metavar="SEC", help="Create new node only if threshold overcome for a number of seconds")
    parser.add_argument("--delay-delete", dest="delay/delete", type=int, default=600, metavar="SEC", help="Delete if the parameter is below the threshold for a number of seconds")
    parser.add_argument("--override-pods-max", dest="override/pods_max", type=int, metavar="NUM", help="Override pods maximum per node")
    parser.add_argument("--sleep-time", dest="sleep-time", type=int, default=10, metavar="SEC", help="Timeout between update cycle")
    parser.add_argument("--report-ignore-namespaces", dest="report/ignore-namespaces", default="kube-system", metavar="N(,N...)", help="Report: comma-separated ignoring namespaces")
    options = vars(parser.parse_args())

    try:
        autoscaling = Autoscalling(options, KubernetesApi(Request(
            api_url  = options['kubernetes/api-url'],
            user     = options['kubernetes/user'],
            password = options['kubernetes/token'])))

        autoscaling.run()

    except Exception as e:
        parser.error(str(e))