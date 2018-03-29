from django.conf import settings

from elasticsearch import Elasticsearch

#from DDR import docstore
from DDR.docstore import *


class Docstore(Docstore):

    def __init__(self, hosts=settings.DOCSTORE_HOSTS, index=settings.DOCSTORE_INDEX, connection=None):
        self.hosts = hosts
        self.indexname = index
        if connection:
            self.es = connection
        else:
            self.es = Elasticsearch(hosts)
