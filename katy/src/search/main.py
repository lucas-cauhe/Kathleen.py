from array import array
from certifi import where
from weaviate import Client

def perform_search(client: Client, selected_properties: str, where_properties: array):
    

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
