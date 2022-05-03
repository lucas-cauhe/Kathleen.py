
from weaviate import Client
import json
import time
import uuid
import requests

from schema import instantiate_schema
from search.main import perform_search
from utils.query import queryBuild
from dotenv import load_dotenv
import os


load_dotenv()
WEAVIATE_URL = os.getenv('WEAVIATE_URL')
client = Client(WEAVIATE_URL)

query_model = {
    "intention": "string",
    "languages": "string",
    "popularity": "string",
    "open_issues": "int",
    "is_updated": "bool"
}

# For v2, I will make available search by url (find most similar repositories to the one given in the url)


def main():
    # Create API to be listening to for incoming requests
    #incoming_query = 
    # Test schema is ok, you need to update something...
    # Perform search and classification
    current_schema = client.schema.get()
    if len(current_schema['classes']) == 0:
        current_schema = instantiate_schema(client)

    d_objects = client.data_object.get()

    gql_query = queryBuild(incoming_query) # Mirar más a fondo las queries que se pueden hacer a weaviate
    search_results = perform_search(gql_query)

    #sorted_results = sort_by_relevance(search_results)

    # Send sorted results

if __name__ == "__main__":
    main()



