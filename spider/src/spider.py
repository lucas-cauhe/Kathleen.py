
# DESIGN FOR CRAWLING THROUGH GITHUB REPOS
from __future__ import annotations
from dataclasses import dataclass, field
from typing import AsyncGenerator, Dict, Optional, Union
from main import GHTOKEN
from datetime import datetime
from dateutil.relativedelta import relativedelta
import itertools
import asyncio
import httpx
import requests
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



class TrendingReposGraph(RepoGraph):

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
        
    


class Crawler:

    def __init__(self) -> None:
        self.repos_to_crawl: list[RepoNodeInfo] = []
        self.trend_repos_graphs: list[RepoGraph] = []
        self.trend_repos_graphs_ids: list[int] = [] # only head nodes ids


    # mirar también a los topics
    async def fetch_repos(self) -> None:
        trending_repos = requests.get(TRENDING_REPOS_BASE_URL, headers={"accept": "application/json"}).json()
        


        for repo in trending_repos:
            online_graph = await self.build_online_graph_analysis(RepoNode(await self.repo_initializer(repo)), 
                [author['url'] for author in repo['builtBy']])
            repo_graph = TrendingReposGraph()
            if online_graph.id in self.trend_repos_graphs_ids:
                repo_graph = self.trend_repos_graphs[online_graph.id]
            else:
                self.trend_repos_graphs_ids.append(online_graph.id) # type: ignore
                self.trend_repos_graphs[online_graph.id] = online_graph # type: ignore

            self.repos_to_crawl += repo_graph.traverse_online_graph(online_graph.head)  # type: ignore

        

    def crawl(self, graph: RepoGraph) -> None:
        print("Crawling throughout GITHUB...")           
    
    async def repo_initializer(self, repo: Dict[str, Union[str, Dict[str, str]]]) -> RepoNodeInfo:
        

        now = datetime.now()
        sub_date = now - relativedelta(months=6)
        updated_since = sub_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        repo_owner = repo.get('builtBy', [{'a':'b'}])[0].get('username', None) or repo['owner']['login'] # type: ignore
        query_headers = {"accept": "application/vnd.github.v3+json",
                    "authorization": f"token {GHTOKEN}"}

        base_string = f'https://api.github.com/repos/{repo_owner}/{repo.get("repositoryName", repo["name"])}/'
        repo_params = ['languages', 'issues', f'commits?since={updated_since}']
        
        client = httpx.AsyncClient()
        
        languages, open_issues, last_updated = await asyncio.gather( # type: ignore
            *map(lambda param, client: (await client.get(base_string+param, headers=query_headers) for _ in '_').__anext__(),  # type: ignore
            repo_params, 
            itertools.repeat(client),)
        ) 
        
        fetch_stars = lambda : len(requests.get(base_string+'stargazers').json())
        
        info: Dict[str, Union[str, list[str], int]] = {'url': repo['url'], # type: ignore
            'name': repo.get('repositoryName', repo["name"]),
            'header': repo['description'],
            'languages': list(languages.json().keys()), # type:ignore
            'stars': repo.get('totalStars', fetch_stars()),
            'openIssues': len(open_issues.json()),
            'lastUpdated': len(last_updated.json()) > 0 # type: ignore
        }
        return RepoNodeInfo(**info) # type: ignore
        
    
    # for now it simply picks the most starred projects from the authors
    # if in a new round a repo has escalated in stars, the graph will place it before the previous ones
    # for analyzing the priorities i'll grab the classification from them both and pick the one more similar to the starter repo
    # The classification results that most alike to the starter repo
    async def build_online_graph_analysis(self, starter_node: RepoNode, authors: list[str]) -> TrendingReposGraph:
        """ FOLLOWS A STRATEGY FOR LOOPING OVER SOME REPOSITORIES ONLINE AND PICKS THEIR DATA """

        #authors_repos: list[list[str]] = self.get_authors_repos(authors) # Repos will be returned in starring order
        #described_authors_repos: list[list[RepoNode]] = self.describe_url(authors_repos)

        parsed_authors_repos = await self.parse_repos(authors)
        online_graph = TrendingReposGraph(starter_node)

        
        for repo in parsed_authors_repos:
            online_graph.append_node(repo, based_on_stars=True)
        
        return online_graph

    async def get_authors_repos(self, authors: list[str]) -> AsyncGenerator[str, str]:
        """ QUERY EACH <<authors>> REPOS AND MAKE THEM INTO A LIST, RETURN THE LIST OF PREVIOUS LISTS """
        # Since each repo description might contain a ton of unwanted info, this is a generator
        
        request = lambda url: requests.get(f'{url}/repos', headers={"authorization": f"token {GHTOKEN}"}).json() # type: ignore
        res =  await asyncio.gather(*[request(url) for url in authors])
        for repo in res:
            yield repo
            

    async def parse_repos(self, authors: list[str]) -> list[RepoNode]:
        """ PARSE EACH AUTHOR'S REPOSITORIES INTO A LIST """
        
        authors_repos = self.get_authors_repos(authors)
        nodes_list: list[RepoNode] = []
        async for repo in authors_repos:
            repo_info = await self.repo_initializer(repo) #type: ignore
            nodes_list.append(RepoNode(repo_info))
        return nodes_list
    



