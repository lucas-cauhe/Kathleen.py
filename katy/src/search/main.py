
from typing import Dict, Union
from weaviate import Client
import requests
from src.main import GHTOKEN

GH_QUERY_HEADERS={"accept": "application/vnd.github.v3+json",
                "authorization": f"token {GHTOKEN}"}
GH_BASE_SEARCH_URL='https://api.github.com/search/repositories'

""" 
Since you will have to add so many repositories, you will have to consider adding just a bunch of representatives for 
different topics and simply returning the k-nn of the repo which results of hnsw search and a search query of gh api which contains 
the parameters of the hnsw search result 
"""
def perform_boolean_search(client: Client, selected_properties: str, where_properties: list[str]):
    
    # mirar nearText o nearVector para realizar esto
    where_filter = {
        'operator': 'And',
        'operands': where_properties
    } if len(where_properties) > 1 else where_properties[0]



    results = client.query.get('Repo', selected_properties)\
                        .with_limit(10)\
                        .with_where(where_filter)\
                        .do()
    
    return results['data']['Get']['Repo']

def perform_fuzzy_search(client: Client, query_filters: Dict[str, Union[str, int]]):
    
    near_text = {
        'concepts': [query_filters['intention']],
        'certainty': 0.8,
        'moveTo': {
            'concepts': [query_filters['most_valuable']],
            'force': 0.05
        }
    }
    
    res = client.query.get('Repo', ['name'])\
        .with_additional(['certainty'])\
        .with_near_text(near_text)\
        .with_limit(query_filters['limit'])\
        .do()

    return res['data']['Get']['Repo']

def fetch_similar_repos(**kwargs):

    match=kwargs['intention']
    stars, languages = kwargs['stars'], kwargs['languages'] # type: ignore
    query_params = f'+in:description{"+"+stars if stars else ""}{"+"+languages if languages else ""}' # type: ignore
    attach = f'?q={match}{query_params}&per_page=10'

    
    res = requests.get(GH_BASE_SEARCH_URL+attach, headers=GH_QUERY_HEADERS).json()

    return res['items']
