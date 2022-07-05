
from weaviate.client import Client

def classify_repository(client: Client):
    
    
    

    intention_classification = client.classification.schedule().with_type('knn')\
                            .with_class_name('Repo')\
                            .with_based_on_properties(['header'])\
                            .with_classify_properties(['hasIntention'])\
                            .with_settings({'k': 3})\
                            .with_wait_for_completion()\
                            .do()
   
    # Perhaps in future versions
    """ # Perform classification of repo's popularity by their stars
    popularity_classification = client.classification.schedule().with_type('knn')\
                            .with_class_name('Repo')\
                            .with_based_on_properties(['stars'])\
                            .with_classify_properties(['hasPopularity'])\
                            .with_settings({'k': 5})\
                            .with_wait_for_completion()\
                            .do()
     """
    print('intention_classification_results: ', intention_classification)
    #print('popularity_classification_results: ', popularity_classification)
    
    
