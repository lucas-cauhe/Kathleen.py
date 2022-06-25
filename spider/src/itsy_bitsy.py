
# DESIGN FOR CRAWLING THROUGH GITHUB REPOS
from hashlib import md5
import itertools
from typing import Generator
import requests
from dataclasses import dataclass, field
from main import GH_TOKEN
from datetime import datetime
from dateutil.relativedelta import relativedelta
import asyncio
import httpx
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
    name: str = None
    header: str = None
    languages: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    stars: int = 0
    openIssues: int = 0
    lastUpdated: int = 0

@dataclass
class RepoNode:
    nextRepo = None
    previousRepo = None
    info: RepoNodeInfo = None
    
    
@dataclass
class RepoGraph:

    id: int = field(init=False)
    head: RepoNode = None
    
    def __post_init__(self) -> None:
        self.id = md5().update(self.head.info.name)

    def append_node(self, node: RepoNode, based_on_stars=False) -> int:
        
        
        if (self.head == None):
            self.head  = node
            return 0
        index = 1
        iter_node = self.head
        while iter_node.nextRepo != None:
            if based_on_stars and iter_node.nextRepo.info.stars < node.info.stars:
                node.nextRepo = iter_node.nextRepo
                iter_node.nextRepo = node
                return index

            iter_node = iter_node.nextRepo
            index += 1
        iter_node.nextRepo = node
        return index

        

    def update_node_at(self, from_position, to_position):
        

        iter_node = self.head

        for i in range(from_position-1): 
            iter_node = iter_node.nextRepo
        
        moved_node = iter_node.nextRepo
        iter_node.nextRepo = moved_node.nextRepo

        iter_node = self.head
        for i in range(to_position-1):
            iter_node = iter_node.nextRepo
        
        moved_node.nextRepo = iter_node.nextRepo
        iter_node.nextRepo = moved_node



    def find_node(self, node: RepoNode) -> int:
        index = 0
        
        iter_node = self.head
        while iter_node.url != node.url:
            iter_node = iter_node.nextRepo
            index += 1
        return index



class TrendingReposGraph(RepoGraph):

    def __init__(self) -> None:
        super().__init__()
    

    def traverse_online_graph(self, online_repo: RepoNode) -> list[RepoNodeInfo]:
        current_repo = self.head
        current_online_repo = online_repo
        final_graph_list = []

        if current_repo == None:
            self.head = online_repo
        
        while current_repo.nextRepo != None or current_online_repo.nextRepo != None:

            if (current_online_repo.info.url != current_repo.info.url):
                self.analyze_priority(current_repo, current_online_repo)
            
            final_graph_list.append(current_repo.info)
            current_repo = current_repo.nextRepo
            current_online_repo = current_online_repo.nextRepo


        return final_graph_list
        
        

    def analyze_priority(self, curr_repo, curr_onrepo):
        """ UPON BUILDING THE ONLINE REPOS GRAPH YOU'LL KNOW HOW TO ANALYZE PRIORITIES """
        
    


class Crawler:

    def __init__(self, ) -> None:
        self.repos_to_crawl = []
        self.trend_repos_graphs = []
        self.trend_repos_graphs_ids = [] # only head nodes ids


    # mirar también a los topics
    async def fetch_repos(self) -> None:
        trending_repos = requests.get(TRENDING_REPOS_BASE_URL, headers={"accept": "application/json"}).json()
        


        for repo in trending_repos:
            online_graph = self.build_online_graph_analysis(RepoNode(RepoNodeInfo(**await self.repo_initializer(repo).values())), [author['url'] for author in repo['builtBy']]) 
            repo_graph = RepoGraph()
            if online_graph.id in self.trend_repos_graphs_ids:
                repo_graph = self.trend_repos_graphs[online_graph.id]
            else:
                self.trend_repos_graphs_ids.append(online_graph.id)
                self.trend_repos_graphs[online_graph.id] = online_graph

            self.repos_to_crawl += repo_graph.traverse_online_graph(online_graph.head)

        self.crawl(repo_graph)

    def crawl(self, graph) -> None:
        pass           
    
    async def repo_initializer(self, repo) -> dict:
        

        now = datetime.now()
        sub_date = now - relativedelta(months=6)
        updated_since = sub_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        repo_owner = repo.get('builtBy', None)[0].get('username', None) or repo['owner']['login']
        query_headers = {"accept": "application/vnd.github.v3+json",
                    "authorization": f"token {GH_TOKEN}"}

        base_string = f'https://api.github.com/repos/{repo_owner}/{repo.get("repositoryName", "name")}'
        repo_params = ['languages', 'issues', f'commits?since={updated_since}']

        async with httpx.AsyncClient() as client:
            languages, open_issues, last_updated = await asyncio.gather(
                *map(lambda param: await client.get(base_string+param, headers=query_headers).json()
                , repo_params, 
                itertools.repeat(client),)
            ) 
        
        fetch_stars = lambda *x: len(await requests.get(base_string+'/stargazers').json()[0])

        return {
            'url': repo['url'],
            'name': repo.get('repositoryName', 'name'),
            'header': repo['description'],
            'languages': list(languages.keys()),
            'stars': repo.get('totalStars', fetch_stars()),
            'openIssues': open_issues[0]['number'],
            'lastUpdated': len(last_updated) > 0
        }
    
    # for now it simply picks the most starred projects from the authors
    # if in a new round a repo has escalated in stars, the graph will place it before the previous ones
    # for analyzing the priorities i'll grab the classification from them both and pick the one more similar to the starter repo
    # The classification results that most alike to the starter repo
    def build_online_graph_analysis(self, starter_node: RepoNode, authors) -> TrendingReposGraph:
        """ FOLLOWS A STRATEGY FOR LOOPING OVER SOME REPOSITORIES ONLINE AND PICKS THEIR DATA """

        #authors_repos: list[list[str]] = self.get_authors_repos(authors) # Repos will be returned in starring order
        #described_authors_repos: list[list[RepoNode]] = self.describe_url(authors_repos)

        parsed_authors_repos = self.parse_repos(authors)
        online_graph = TrendingReposGraph(starter_node)

        
        for repo in parsed_authors_repos:
            online_graph.append_node(repo, based_on_stars=True)
        
        return online_graph

    async def get_authors_repos(self, authors) -> Generator[dict]:
        """ QUERY EACH <<authors>> REPOS AND MAKE THEM INTO A LIST, RETURN THE LIST OF PREVIOUS LISTS """
        # Since each repo description might contain a ton of unwanted info, this is a generator
        
        request = lambda url: requests.get(f'{url}/repos', headers={"authorization": f"token {GH_TOKEN}"}).json()
        res =  await asyncio.gather(*[request(url) for url in authors])
        for repos in res:
            yield repos
            

    async def parse_repos(self, authors) -> list[RepoNode]:
        """ PARSE EACH AUTHOR'S REPOSITORIES INTO A LIST """
        
        authors_repos = await self.get_authors_repos(authors)
        nodes_list = []
        for repo in authors_repos:
            repo_info = RepoNodeInfo(**await self.repo_initializer(repo))
            nodes_list.append(RepoNode(repo_info))
        return nodes_list
    



