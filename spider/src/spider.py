
# DESIGN FOR CRAWLING THROUGH GITHUB REPOS
from __future__ import annotations

from dataclasses import dataclass, field
from typing import AsyncGenerator, Dict, Optional, Union
from dotenv import load_dotenv
load_dotenv()
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
import itertools
import asyncio
import httpx
import requests
from classification import classify_repository
from utils.cluster import KMedoids
# LISTA DE URLS 

# Haces una maner de ciclar entre varios repositorios a partir del más trending y cada vez que recorras el ciclo,
# para cada nodo del grafo te preguntas si el nodo actual es el mismo repositorio que el ciclo que estás construyendo
# con los repos que encuentras
# Si coinciden, miras si ha cambiado algo (lo clasificas con weaviate y según los resultados de la clasificación lo actualizas o no, si no
# miras si se ha cambiado algo en el repositorio)
# Si no coinciden tienes que actualizar el grafo incluyendo el nuevo repo

# Investigar cual es el mejor tipo de grafo o árbol para esto



# Para la siguiente versión habrá que considerar una estructura que, dentro del grafo de repos similares a uno, permita establecer para
# cada repo en ese grafo, cuales son los más similares a él -> lo utilizas en analyze priority
TRENDING_REPOS_BASE_URL = 'https://gh-trending-api.herokuapp.com/repositories'
GH_BASE_SEARCH_URL='https://api.github.com/search/repositories'
CRAWL_LIMIT = 50
GHTOKEN = os.environ['GHTOKEN']
GH_QUERY_HEADERS={"accept": "application/vnd.github.v3+json",
                "authorization": f"token {GHTOKEN}"}
        
@dataclass
class RepoInfo:
    url: str
    name: str
    header: str
    languages: list[str]
    stars: int
    openIssues: int
    lastUpdated: bool
    keywords: list[str] = field(default_factory=list)

   

class Crawler:

    def __init__(self, crawl_inputs: Dict[str, str]) -> None:
        self.repos_to_crawl: list[RepoInfo] = []
        self.crawl_inputs = crawl_inputs


    # mirar también a los topics
    async def repo_gen(self) -> AsyncGenerator[list[Dict[str, Union[str, Dict[str, str]]]], None]:
        # The repos you now have to fetch is by searching along with crawl_inputs
        while len(self.repos_to_crawl) < CRAWL_LIMIT:
            new_repos = self.fetch_repos()
            self.repos_to_crawl.extend([await self.repo_initializer(repo) for repo in new_repos])
            yield new_repos

        

    def fetch_repos(self) -> list[Dict[str, Union[str, Dict[str, str]]]]:
        match=self.crawl_inputs.get('match', '')
        within, stars, languages = self.crawl_inputs['q'].get('in', ''), self.crawl_inputs['q'].get('stars', ''), self.crawl_inputs['q'].get('language', '') # type: ignore
        query_params = f'{"+"+within if within else ""}{"+"+stars if stars else ""}{"+"+languages if languages else ""}' # type: ignore
        sort: str = self.crawl_inputs.get('sort', None) # type: ignore
        order: str = self.crawl_inputs.get('order', None) #type: ignore
        attach = f'?q={match}{query_params}{"&sort="+sort if sort else ""}{"&order="+order if order else ""}&per_page=10'

        
        res = requests.get(GH_BASE_SEARCH_URL+attach, headers=GH_QUERY_HEADERS).json()
        
        return res['items']

    async def crawl(self) -> None:
        """ TAKES THE REPOS FROM <<repos_to_crawl>> AND ADDS THEM TO THE DB AND CLASSIFIES THEM """  
       
        classified_repos: list[Dict[str, int]] = [] # {"index", "classification_result"}, index in <<repos_to_crawl>>
        # start kmedoids
        main_objects = client.data_object.get(with_vector=True)
        vectors = np.array([repo['vector'] for repo in main_objects['objects']]) #type: ignore

        # Compute clusters
        # Clusters will be computed using K-Medoids
        cluster = KMedoids(data=vectors)
        cluster.cluster()
        # decide what medoid we are looking for depending on crawl_inputs, if crawl_inputs are None, return whole medoids
        async for generator in self.repo_gen():
            
            # Add repos to db (retrieving vectorized repo), retrieve nearest neighbors, if nearest neighbors are members of medoid
            # desired (decided by crawl_inputs), repo stays.
            # If no crawl_inputs are set, every repo close enough to a medoid will be added


            # Add repos to db
                # Add each new self-class-property in the repo to its own classes by batches and keep their beacons
                # Create each new repo object (requesting its vector representation (check it is the same before and after adding the references)) 
                # and add previous references all by batches
                # If references change the vector representation of the repo, retrieve back the repos with their vector representation
                
                


            # Retrieve nearest neighbors   
                # get with near_vector, pick some
                    """ near_vector = {
                    'vector': vector
                    }
                    clause = {
                        'token': "certainty"
                    }
                    settings = {
                        'properties': repo_properties,
                    }
                    medoids_repo = self.main_client.query.get("Repo", repo_properties) \
                        .with_near_vector(near_vector) \
                        .with_additional((clause, settings)) \
                        .do() """
                


            # Check response with medoid
                
                # look in kmedoids results for the neighbors that are present in the desired medoid(s) members
                # don't delete those repos whose found neighbors are closest (certainty) to the desired medoid(s) from the database
                # keep track of those to delete and delete them in batches
        
        # delete in batches unwanted repos
        # run classification after having added the desired repos


            
            
            

          
        self.repos_to_crawl = []

    def sort_classified_repos(self, repos: list[Dict[str, int]]) -> list[Dict[str, int]]:
        return [{"d": 0}]
    
    async def repo_initializer(self, repo: Dict[str, Union[str, Dict[str, str]]]) -> RepoInfo:
        

        now = datetime.now()
        sub_date = now - relativedelta(months=6)
        updated_since = sub_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        repo_owner = repo.get('builtBy', [{'a':'b'}])[0].get('username', None) or repo['owner']['login'] # type: ignore
        

        base_string = f'https://api.github.com/repos/{repo_owner}/{repo.get("repositoryName", repo["name"])}/'
        repo_params = ['languages', 'issues', f'commits?since={updated_since}', 'stargazers']
        
        client = httpx.AsyncClient()
        
        languages, open_issues, last_updated, stars = await asyncio.gather( # type: ignore
            *map(lambda param, client: (await client.get(base_string+param, headers=GH_QUERY_HEADERS) for _ in '_').__anext__(),  # type: ignore
            repo_params, 
            itertools.repeat(client),)
        ) 
        
        
        
        info: Dict[str, Union[str, list[str], int]] = {'url': repo['url'], # type: ignore
            'name': repo.get("name", "Not found"),
            'header': repo['description'],
            'languages': list(languages.json().keys()), # type:ignore
            'stars': len(stars.json()),                 # type: ignore
            'openIssues': len(open_issues.json()),      # type: ignore
            'lastUpdated': len(last_updated.json()) > 0 # type: ignore
        }
        return RepoInfo(**info) # type: ignore
    



