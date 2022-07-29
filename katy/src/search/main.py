
from typing import Dict, Union
from weaviate import Client
import requests
import sys
sys.path.append('/Users/cinderella/Documents/Kathleen-back-weaviate/github-upload/katy/src')
from utils.format import customDict



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
    print(f"{results=}")
    return results['data']['Get']['Repo']

def perform_fuzzy_search(client: Client, query_filters: Dict[str, Union[str, int]]):
    
    near_text = customDict({
        'concepts': query_filters['intention'].split(' '),
        'certainty': 0.8,
        'moveTo': {
            'concepts': query_filters['most_valuable'],
            'force': 0.05
        }
    })
    res = client.query.get('Repo', ['name', 'stars', 'languages', "_additional { distance, id } "])\
        .with_near_text(near_text)\
        .do()
    print(f"other response: {res}")
    return res['data']['Get']['Repo']

def fetch_similar_repos(gh_base, gh_headers, **kwargs):

    match=kwargs['intention']
    stars, languages = kwargs['stars'], kwargs['languages'] # type: ignore
    query_params = f'+in:description{"+"+stars if stars else ""}{"+"+",".join(languages) if languages else ""}' # type: ignore
    attach = f'?q={match}{query_params}&per_page=10'

    
    res = requests.get(gh_base+attach, headers=gh_headers).json()

    return res['items']
