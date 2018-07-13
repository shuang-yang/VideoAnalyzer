import pydocumentdb
import pydocumentdb.document_client as dc
import pydocumentdb.errors as errors


class DBManager(object):
    def __init__(self, endpoint, masterkey):
        self.endpoint = endpoint
        self.masterkey = masterkey
        self.client = dc.DocumentClient(endpoint, {'masterKey': masterkey})

    def create_database(self, id):

        try:
            database = self.client.CreateDatabase({"id": id})
            print('Database with id \'{0}\' created'.format(id))
            return database

        except errors.DocumentDBError as e:
            if e.status_code == 409:
               print('A database with id \'{0}\' already exists'.format(id))
            else:
                raise errors.HTTPFailure(e.status_code)

    def read_database(self, id):

        try:
            database_link = 'dbs/' + id

            database = self.client.ReadDatabase(database_link)
            print('Database with id \'{0}\' was found, it\'s _self is {1}'.format(id, database['_self']))
            return database

        except errors.DocumentDBError as e:
            if e.status_code == 404:
                print('A database with id \'{0}\' does not exist'.format(id))
            else:
                raise errors.HTTPFailure(e.status_code)

    def find_databases(self, id):

        databases = list(self.client.QueryDatabases({
            "query": "SELECT * FROM r WHERE r.id=@id",
            "parameters": [
                {"name": "@id", "value": id}
            ]
        }))

        if len(databases) > 0:
            print('Database with id \'{0}\' was found'.format(id))
        else:
            print('No database with id \'{0}\' was found'.format(id))

        return databases

    def delete_database(self, id):

        try:
            database_link = 'dbs/' + id
            self.client.DeleteDatabase(database_link)

            print('Database with id \'{0}\' was deleted'.format(id))

        except errors.DocumentDBError as e:
            if e.status_code == 404:
                print('A database with id \'{0}\' does not exist'.format(id))
            else:
                raise errors.HTTPFailure(e.status_code)

    def list_databases(self):

        print('Databases:')

        databases = list(self.client.ReadDatabases())

        if not databases:
            return

        for database in databases:
            print(database['id'])

    def find_collections(self, database_id, id):
        database_link = 'dbs/' + database_id

        collections = list(self.client.QueryCollections(
            database_link,
            {
                "query": "SELECT * FROM r WHERE r.id=@id",
                "parameters": [
                    {"name": "@id", "value": id}
                ]
            }
        ))

        if len(collections) > 0:
            print('Collection with id \'{0}\' was found'.format(id))
        else:
            print('No collection with id \'{0}\' was found'.format(id))

        return collections

    def create_collection(self, database_id, id, offer_enable_ru_per_min_throughput, offer_version, offer_throughput):
        database_link = 'dbs/' + database_id
        options = {
            'offerEnableRUPerMinuteThroughput': offer_enable_ru_per_min_throughput,
            'offerVersion': offer_version,
            'offerThroughput': offer_throughput
        }

        try:
            collection = self.client.CreateCollection(database_link, {"id": id}, options)
            print('Collection with id \'{0}\' created'.format(id))
            return collection

        except errors.DocumentDBError as e:
            if e.status_code == 409:
                print('A collection with id \'{0}\' already exists'.format(id))
            else:
                raise errors.HTTPFailure(e.status_code)

    def read_collection(self, database_id, id):
        database_link = 'dbs/' + database_id
        try:
            collection_link = database_link + '/colls/{0}'.format(id)

            collection = self.client.ReadCollection(collection_link)
            print('Collection with id \'{0}\' was found, it\'s _self is {1}'.format(collection['id'],
                                                                                    collection['_self']))
            return collection
        except errors.DocumentDBError as e:
            if e.status_code == 404:
                print('A collection with id \'{0}\' does not exist'.format(id))
            else:
                raise errors.HTTPFailure(e.status_code)

    def list_collections(self, database_id):
        database_link = 'dbs/' + database_id

        print('Collections:')

        collections = list(self.client.ReadCollections(database_link))

        if not collections:
            return

        for collection in collections:
            print(collection['id'])

    def delete_collection(self, database_id, id):
        database_link = 'dbs/' + database_id
        try:
           collection_link = database_link + '/colls/{0}'.format(id)
           self.client.DeleteCollection(collection_link)

           print('Collection with id \'{0}\' was deleted'.format(id))

        except errors.DocumentDBError as e:
            if e.status_code == 404:
               print('A collection with id \'{0}\' does not exist'.format(id))
            else:
                raise errors.HTTPFailure(e.status_code)

    # TODO - change get_collection_link to collection['_self']

    def create_doc(self, database_id, collection_id, doc):
        docs = self.find_doc(database_id, collection_id, doc['id'])
        if len(docs) != 0:
            return docs[0]
        try:
            collection_link = self.get_collection_link(database_id, collection_id)
            doc = self.client.CreateDocument(collection_link, doc)
            return doc

        except errors.DocumentDBError as e:
            if e.status_code == 404:
               print('A document with id \'{0}\' does not exist'.format(doc["id"]))
            else:
                raise errors.HTTPFailure(e.status_code)

    def query_doc(self, database_id, collection_id, query):
        collection_link = self.get_collection_link(database_id, collection_id)
        result = self.client.QueryDocuments(collection_link, query)
        return list(result)

    def replace_doc(self, doc):
        self.client.ReplaceDocument(doc['_self'], doc)

    def find_doc(self, database_id, collection_id, id):
        docs = list(self.client.QueryDocuments(
            self.get_collection_link(database_id, collection_id),
            {
                "query": "SELECT * FROM r WHERE r.id=@id",
                "parameters": [
                    {"name": "@id", "value": id}
                ]
            }
        ))

        return docs

    @staticmethod
    def get_collection_link(database_id, collection_id):
        return 'dbs/' + database_id + '/colls/' + collection_id

    def get_next_id(self, database_id, collection_id):
        query = {'query': 'SELECT * FROM c ORDER BY c._ts DESC'}
        query_result = self.query_doc(database_id, collection_id, query)
        return '1' if len(query_result) == 0 else query_result[0]['_ts']

