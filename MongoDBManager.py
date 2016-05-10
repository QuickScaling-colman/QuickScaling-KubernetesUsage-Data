from pymongo import MongoClient
from datetime import datetime


class MongoDBManager(object):
    def __init__(self):
        self.connection = MongoClient("Connection String")
        self.db = self.connection.quicksacling

    def addRecord(self, record):
       self.db.insert(record)
       # should we continue?
       flag = input('Enter another record? (Y/N) ')
       if (flag[0].upper() == 'N'):
          flag = False

    def printAllRecord(self):
        # find all documents
        results = self.db.find()

        print()
        print('+-+-+-+-+-+-+-+-+-+-+-+-+-+-')

        # display documents from collection
        for record in results:
            print(record['hostname'] + ',',record['cpu'] + ',', record['memory'] + ',', record['create_at'])

        print()

    def closeConnection(self):
        # close the connection to MongoDB
        self.connection.close()