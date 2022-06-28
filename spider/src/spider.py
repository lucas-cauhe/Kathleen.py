
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
class RepoNodeInfo:
    url: str
    name: str
    header: str
    languages: list[str]
    stars: int
    openIssues: int
    lastUpdated: bool
    keywords: list[str] = field(default_factory=list)

   

@dataclass
class RepoNode:
    info: RepoNodeInfo 
    nextRepo: Optional[RepoNode] = None
    previousRepo: Optional[RepoNode] = None
    
    
@dataclass
class RepoGraph:

    id: Optional[int] = field(init=False)
    head: Optional[RepoNode] = None
    
    def __post_init__(self) -> None:
        self.id = hash(self.head.info.name) if self.head else None

    def append_node(self, node: RepoNode, based_on_stars:bool=False) -> int:
        
        
        if (not self.head):
            self.head  = node
            self.__post_init__()
            return 0
        index = 1
        iter_node = self.head
        while iter_node.nextRepo:
            if based_on_stars and iter_node.nextRepo.info.stars < node.info.stars:
                node.nextRepo = iter_node.nextRepo
                iter_node.nextRepo = node
                return index

            iter_node = iter_node.nextRepo
            index += 1
        iter_node.nextRepo = node
        return index

        

    def update_node_at(self, from_position:int, to_position:int):
        
        
        iter_node = self.head
        
        while iter_node and from_position-1:
            iter_node = iter_node.nextRepo
            from_position -= 1

        moved_node = iter_node.nextRepo # type: ignore
        iter_node.nextRepo = moved_node.nextRepo # type: ignore

        iter_node = self.head
        while iter_node and to_position-1:
            iter_node = iter_node.nextRepo
            to_position -= 1
        
        moved_node.nextRepo = iter_node.nextRepo # type: ignore
        iter_node.nextRepo = moved_node          # type: ignore

        


    def find_node(self, node: RepoNode) -> int:
        index = 0
        
        iter_node = self.head
        while iter_node and iter_node.info.url != node.info.url:
            iter_node = iter_node.nextRepo
            index += 1
        return index



class StructuredReposGraph(RepoGraph):

    def __init__(self, head: Union[RepoNode, None] = None) -> None:
        super().__init__(head)
    

    def traverse_online_graph(self, online_repo: RepoNode) -> list[RepoNodeInfo]:
        
        current_online_repo = online_repo
        final_graph_list: list[RepoNodeInfo] = []

        if not self.head:
            self.head = online_repo
            self.__post_init__()
        current_repo = self.head
        while current_repo and  current_online_repo and (current_repo.nextRepo or current_online_repo.nextRepo): 

            if (current_online_repo.info.url != current_repo.info.url): 
                self.analyze_priority(current_repo, current_online_repo) 
            
            final_graph_list.append(current_repo.info)
            current_repo = current_repo.nextRepo
            current_online_repo = current_online_repo.nextRepo


        return final_graph_list
        
        

    def analyze_priority(self, curr_repo: RepoNode, curr_onrepo: RepoNode) -> None:
        """ UPON BUILDING THE ONLINE REPOS GRAPH YOU'LL KNOW HOW TO ANALYZE PRIORITIES """
        # Here you have to load the representative DB from weaviate and classify the <<curr_onrepo>> 
        # and compare it against the curr_repo (taking its classification from the true DB)
        # Those repos that result far from what's expected (crawler_inputs) will be left out from the repos to crawl

        # Return the update Data Structure upon having analyzed both repos 


class Crawler:

    def __init__(self, crawl_inputs: Dict[str, str], reduced_db_instance=None) -> None:
        self.repos_to_crawl: list[RepoNodeInfo] = []
        self.structured_repos_graphs: list[RepoGraph] = []
        self.structured_repos_graphs_ids: list[int] = [] # only head nodes ids
        self.crawl_inputs = crawl_inputs
        self.reduced_db_instance = reduced_db_instance # type: ignore (it's a weaviate instance)


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

    async def crawl(self) -> list[Dict[str, int]]:
        """ TAKES THE REPOS FROM <<repos_to_crawl>> AND ADDS THEM TO THE DB AND CLASSIFIES THEM """  
       
        classified_repos: list[Dict[str, int]] = [] # {"index", "classification_result"}, index in <<repos_to_crawl>>
        async for generator in self.repo_gen():
            # Add repos to reduced db

            pass

            # Classify them
            # Take classification results into classified_repos
            
            

        sorted_repos = self.sort_classified_repos(classified_repos)    
        self.repos_to_crawl = []
        return sorted_repos

    def sort_classified_repos(self, repos: list[Dict[str, int]]) -> list[Dict[str, int]]:
        return [{"d": 0}]
    
    async def repo_initializer(self, repo: Dict[str, Union[str, Dict[str, str]]]) -> RepoNodeInfo:
        

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
        return RepoNodeInfo(**info) # type: ignore
    



