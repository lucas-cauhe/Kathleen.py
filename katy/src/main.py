
from weaviate import Client
import json
import time
import uuid
import requests
from fastapi import FastAPI
from typing import Optional
from pydantic import BaseModel

from schema import instantiate_schema
from search.main import perform_search
from utils.client import json_print
from utils.query import queryBuild
from dotenv import load_dotenv
import os


load_dotenv()
WEAVIATE_URL = os.getenv('WEAVIATE_URL')
client = Client(WEAVIATE_URL)

app = FastAPI()
crawl_inputs = CInputs()

class QueryModel(BaseModel):
    hasIntention: Optional[str] = None
    languages: list[str]
    stars: Optional[int] = None
    openIssues: Optional[int] = None
    isUpdated: Optional[bool] = None

# For v2, I will make available search by url (find most similar repositories to the one given in the url)

@app.post('/query')
def query_received(query: QueryModel):

    return main(query)

@app.post('/manager')
def handle_manager(crawler_inputs: Optional[CInputs] = None, **kwargs):
    if crawl_inputs is not None:
        # Make request to crawler
        ...
    
    return kwargs


def main(query: QueryModel):
   
    current_schema = client.schema.get()
    if len(current_schema['classes']) == 0:
        current_schema = instantiate_schema(client)

    #json_print(current_schema)
    print('Schema fetched')
    #d_objects = client.data_object.get()
    json_print(query.dict())
    selected_properties, where_properties = queryBuild(client, query.dict()) # Mirar más a fondo las queries que se pueden hacer a weaviate
    print(selected_properties, where_properties)
    search_results = perform_search(client, selected_properties, where_properties)
    print(search_results)
    return search_results
    #sorted_results = sort_by_relevance(search_results)

    # Send sorted results

if __name__ == "__main__":
    main()



