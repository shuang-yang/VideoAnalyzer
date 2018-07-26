import sys
import json
from SearchManager import *

def search(keyword):
    search_manager = SearchManager("video-analyzer-search", "2017-11-11",
                                   'https://video-analyzer-search.search.windows.net',
                                   '40BCFD3875D09243AB49A3175FE9AD99')
    response = search_manager.search('frames-index', keyword)
    return response.json()


if __name__ == '__main__':
	result = search(sys.argv[1])
	print(json.dumps(result))
	sys.stdout.flush()
