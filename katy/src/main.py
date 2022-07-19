
from weaviate import Client
import json
from typing import Dict, Union
from fastapi import FastAPI
from typing import Optional
from pydantic import BaseModel

from search.main import perform_boolean_search, perform_fuzzy_search, fetch_similar_repos
from utils.query import queryBuild
from dotenv import load_dotenv
import os


load_dotenv()
WEAVIATE_URL = os.getenv('WEAVIATE_URL')
GHTOKEN = os.getenv('GHTOKEN')
client = Client(WEAVIATE_URL)
DEFAULT_QUERY_LIMIT = 5

app = FastAPI()


class QueryModel(BaseModel):
    hasIntention: Optional[str] = None
    languages: list[str]
    stars: Optional[int] = None
    openIssues: Optional[int] = None
    isUpdated: Optional[bool] = None
    url: Optional[str] = None

class CInputs(BaseModel):
    q: Dict[str, str]
    order: Optional[str]
    props: Dict[str, Union[list[str], str]]
    update: bool
    topics: Dict[str, bool]
# For v2, I will make available search by url (find most similar repositories to the one given in the url)

@app.post('/query')
def query_received(query: QueryModel):

    return main(query)

@app.post('/manager')
def handle_manager(crawler_inputs: Optional[CInputs] = None, **kwargs):
    if crawler_inputs is not None:
        # Dump inputs to common/crawler_inputs.json

        with open("../../common/crawler_inputs.json", "w") as file:
            json.dump(dict(crawler_inputs), file)
    
    return kwargs


def main(query: QueryModel):

    selected_properties, where_properties = queryBuild(client, query.dict()) # Mirar más a fondo las queries que se pueden hacer a weaviate
    print(selected_properties, where_properties)
    final_repos = perform_boolean_search(client, selected_properties, where_properties)
    if len(final_repos) < DEFAULT_QUERY_LIMIT:
        
        if query.hasIntention is None:
            # for v2
            # if query.url:
                # intent_rekon(query.url)
            # else:
            query.hasIntention = query.languages[0]

        
        query_filters = {
            'limit': DEFAULT_QUERY_LIMIT-len(final_repos),
            'intention': query.hasIntention,
            'most_valuable': query.languages
        }
        final_repos.extend(perform_fuzzy_search(client, query_filters))
    
    final_repos.extend(fetch_similar_repos(stars=final_repos[0]['stars'], languages=final_repos[0]['languages'], intention=query.hasIntention))

    return final_repos
    




