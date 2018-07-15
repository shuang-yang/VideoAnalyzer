import requests
import copy
import json


class SearchManager(object):
    def __init__(self, name, api_version, path, url, admin_key):
        self.name = name
        self.api_version = api_version
        self.admin_key = admin_key
        self.search_service = SearchService(api_version, path, url, admin_key)

    def create_data_source(self, datasource_name, connection_string, collection_id, collection_query):
        url = 'https://' + self.name + 'search.windows.net/datasource?api-version=' + self.api_version
        headers = {
            'Content-Type': 'application/json',
            'api-key': self.admin_key
        }
        params = {
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
        requests.post(url, params=json.dump(params), headers=headers)


class SearchService(object):
    def __init__(self, api_version, path, url, admin_key):
        self.api_version = api_version
        self.path = '/' + path
        self.url = url
        self.admin_key = admin_key

    def query_path(self, endpoint):
        return self.url + self.path + '/' + endpoint if endpoint else self.url + self.path

    def query_params(self, extra={}):
        params = copy.deepcopy(extra)
        params.update({'api-version': self.api_version})
        return query_parames

    def query_headers(self, extra={}):
        headers = copy.deepcopy(extra)
        headers.update({'api-key': self.admin_key})
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