from array import array
from weaviate import Client

def perform_search(client: Client, selected_properties: array, where_properties: array):
    
    results = client.query.get('Repo', selected_properties)\
                        .with_limit(10)\
                        .with_where({
                            'operator': 'And',
                            'operands': where_properties
                        })\
                        .do()
    
    return results

# This function may come in handy for v2 with the certainty clause in the query
def sort_by_relevance(vec: dict):
    pass


# Para el spider
"""

def classify_intention():
    # Perform classification of repo's intention by their keywords and header

    intention_classification = client.classification.schedule().with_type('knn')\
                            .with_class_name('Repo')\
                            .with_based_on_properties(['keywords', 'header'])\
                            .with_classify_properties(['hasIntention'])\
                            .with_settings({'k': 5})\
                            .do()

    # Perform classification of repo's popularity by their stars
    popularity_classification = client.classification.schedule().with_type('knn')\
                            .with_class_name('Repo')\
                            .with_based_on_properties(['stars'])\
                            .with_classify_properties(['hasPopularity'])\
                            .with_settings({'k': 5})\
                            .do()


    # Check classification_results
    
"""