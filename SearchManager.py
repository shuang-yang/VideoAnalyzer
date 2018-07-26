import requests
import copy
import json
import azure.mgmt.search as search
import azure.mgmt.search.models as search_models
import http.client


class SearchManager(object):
    def __init__(self, name, api_version, url, admin_key):
        self.name = name
        self.api_version = api_version
        self.admin_key = admin_key
        self.search_client = SearchService(api_version, url, admin_key)

    def create_data_source(self, datasource_name, connection_string, collection_id, collection_query):
        url = "https://" + self.name + ".search.windows.net/datasources/" + datasource_name + "?api-version=" + self.api_version
        headers = {
            'Content-Type': 'application/json',
            'api-key': self.admin_key
        }
        data = {
            "name": datasource_name,
            "type": "documentdb",
            "credentials": {
                "connectionString": connection_string
            },
            "container": {"name": collection_id, "query": collection_query},
            "dataChangeDetectionPolicy": {
                "@odata.type": "#Microsoft.Azure.Search.HighWaterMarkChangeDetectionPolicy",
                "highWaterMarkColumnName": "_ts"
            },
            "dataDeletionDetectionPolicy": {
                "@odata.type": "#Microsoft.Azure.Search.SoftDeleteColumnDeletionDetectionPolicy",
                "softDeleteColumnName": "isDeleted",
                "softDeleteMarkerValue": "true"
            }
        }
        response = requests.put(url, headers=headers, data=json.dumps(data))
        print("create datasource:" + str(response))

    def create_index(self, index_name):
        url = 'https://' + self.name + '.search.windows.net/indexes/' + index_name + '?api-version=' + self.api_version
        headers = {
            'Content-Type': 'application/json',
            'api-key': self.admin_key
        }
        data = {
         "name": index_name,
         "fields": [
          {"name": "id", "type": "Edm.String", "key": True, "searchable": False},
          {"name": "video_id", "type": "Edm.String", "filterable": True},
          {"name": "video_url", "type": "Edm.String"},
          {"name": "filename", "type": "Edm.String", "filterable": True},
          {"name": "index", "type": "Edm.Int64", "searchable": False, "filterable": False, "facetable": False},
          {"name": "time", "type": "Edm.Int64", "searchable": False, "filterable": False, "facetable": False},
          {"name": "url", "type": "Edm.String"},
          {"name": "tags", "type": "Edm.String"},
          {"name": "captions", "type": "Edm.String"},
          {"name": "categories", "type": "Edm.String"},
          {"name": "celebrities", "type": "Edm.String"},
          {"name": "landmarks", "type": "Edm.String"},
          {"name": "dominant_colors", "type": "Edm.String"},
          {"name": "foreground_color", "type": "Edm.String"},
          {"name": "background_color", "type": "Edm.String"},
          {"name": "isBwImg", "type": "Edm.Boolean", "searchable": False},
          {"name": "height", "type": "Edm.Int32", "searchable": False},
          {"name": "width", "type": "Edm.Int32", "searchable": False}
         ],
         "suggesters": [
          {
           "name": "celeb",
           "searchMode": "analyzingInfixMatching",
           "sourceFields": ["celebrities", "landmarks"]
          }
         ]
        }
        response = requests.put(url, headers=headers, data=json.dumps(data))
        print(response)

    def create_indexer(self, indexer_name, datasource_name, index_name):
        url = 'https://' + self.name + '.search.windows.net/indexers/' + indexer_name + '?api-version=' + self.api_version
        headers = {
            'Content-Type': 'application/json',
            'api-key': self.admin_key
        }
        data = {
            "name": indexer_name,
            "dataSourceName": datasource_name,
            "targetIndexName": index_name
        }
        response = requests.put(url, headers=headers, data=json.dumps(data))
        print("create indexer: " + str(response))

    def run_indexer(self, indexer_name):
        url = 'https://' + self.name + '.search.windows.net/indexers/' + indexer_name + '/run?api-version=' + self.api_version
        headers = {'api-key': self.admin_key}
        response = requests.post(url, headers=headers)
        print("run indexer: " + str(response))

    def get_indexer_status(self, indexer_name):
        url = 'https://' + self.name + '.search.windows.net/indexers/' + indexer_name + '/status?api-version=' + self.api_version
        headers = {'api-key': self.admin_key}
        response = requests.get(url, headers=headers)
        print("get indexer status: " + str(response))

    def search(self, index_name, query):
        url = 'https://' + self.name + '.search.windows.net/indexes/' + index_name + '/docs/search?api-version=' + self.api_version
        headers = {
            'Content-Type': 'application/json',
            'api-key': self.admin_key
        }
        data = {"search": query}
        response = requests.post(url, headers=headers, data=json.dumps(data))
        return response


class SearchService(object):
    def __init__(self, api_version, url, admin_key):
        self.api_version = api_version
        self.url = url
        self.admin_key = admin_key

    def query_path(self, endpoint):
        return self.url + '/' + endpoint if endpoint else self.url

    def query_params(self, extra={}):
        params = copy.deepcopy(extra)
        params.update({'api-version': self.api_version})
        return params

    def query_headers(self, extra={}):
        headers = copy.deepcopy(extra)
        headers.update({'Content-Type': 'application/json', 'api-key': self.admin_key})
        return headers

    def get(self, data={}, endpoint=None):
        return requests.get(
            self.query_path(endpoint),
            params=self.query_params(),
            headers=self.query_headers(),
            json=data
        )

    def post(self, data={}, endpoint=None):
        return requests.post(
            self.query_path(endpoint),
            params=self.query_params(),
            headers=self.query_headers(),
            json=data
        )

    def put(self, data={}, endpoint=None):
        return requests.put(
            self.query_path(endpoint),
            params=self.query_params(),
            headers=self.query_headers(),
            json=data
        )

    def delete(self, data={}, endpoint=None):
        return requests.delete(
            self.query_path(endpoint),
            params=self.query_params(),
            headers=self.query_headers(),
            json=data
        )