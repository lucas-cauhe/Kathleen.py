import weaviate
from weaviate.client import Client

def classify_repository(client: Client):
    
    """ 
    Classification when training data is available, I'll first use zeroshot classification
    # Perform classification of repo's intention by their keywords and header

    intention_classification = client.classification.schedule().with_type('knn')\
                            .with_class_name('Repo')\
                            .with_based_on_properties(['keywords', 'header'])\
                            .with_classify_properties(['hasIntention'])\
                            .with_settings({'k': 5})\
                            .with_wait_for_completion()\
                            .do()

    # Perform classification of repo's popularity by their stars
    popularity_classification = client.classification.schedule().with_type('knn')\
                            .with_class_name('Repo')\
                            .with_based_on_properties(['stars'])\
                            .with_classify_properties(['hasPopularity'])\
                            .with_settings({'k': 5})\
                            .with_wait_for_completion()\
                            .do()
     """

    intention_classification_results = client.classification.schedule().with_type('zeroshot')\
        .with_class_name('Repo')\
        .with_classify_properties(["hasIntention"])\
        .with_based_on_properties(['keywords', 'header'])\
        .with_wait_for_completion()\
        .do()
    popularity_classification_results = client.classification.schedule().with_type('zeroshot')\
        .with_class_name('Repo')\
        .with_classify_properties(["hasPopularity"])\
        .with_based_on_properties(['stars'])\
        .with_wait_for_completion()\
        .do()
    # Check classification_results

    print('intention_classification_results: ', intention_classification_results)
    print('popularity_classification_results: ', popularity_classification_results)
    
    
def build_reduced_db_instance():
    pass