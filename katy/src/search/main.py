from array import array
from certifi import where
from weaviate import Client

""" 
Since you will have to add so many repositories, you will have to consider adding just a bunch of representatives for 
different topics and simply returning the k-nn of the repo which results of hnsw search and a search query of gh api which contains 
the parameters of the hnsw search result 
"""
def perform_search(client: Client, selected_properties: str, where_properties: array):
    
    # mirar nearText o nearVector para realizar esto
    where_filter = {
        'operator': 'And',
        'operands': where_properties
    } if len(where_properties) > 1 else where_properties[0]



    results = client.query.get('Repo', selected_properties)\
                        .with_limit(10)\
                        .with_where(where_filter)\
                        .do()
    
    return results

# This function may come in handy for v2 with the certainty clause in the query
def sort_by_relevance(vec: dict):
    pass
