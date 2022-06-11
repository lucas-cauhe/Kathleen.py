
# DESIGN FOR CRAWLING THROUGH GITHUB REPOS
import requests
from dataclasses import dataclass, field
import os
from datetime import datetime
from dateutil.relativedelta import relativedelta
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

@dataclass
class RepoNode:

    url: str
    name: str = None
    header: str = None
    languages: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    stars: int = 0
    openIssues: int = 0
    lastUpdated: int = 0
    nextRepo = None
    previousRepo = None
    
    
@dataclass
class RepoGraph:

    head: RepoNode = None

    def append_node(self, node: RepoNode, based_on_stars=False) -> int:
        
        
        if (self.head == None):
            self.head  = node
            return 0
        index = 1
        iter_node = self.head
        while iter_node.nextRepo != None:
            if based_on_stars and iter_node.nextRepo.stars < node.stars:
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
    

    def traverse_online_graph(self, online_repo: RepoNode):
        current_repo = self.head
        current_online_repo = online_repo

        if current_online_repo == None:
            self.head = online_repo
            return
        
        while current_repo.nextRepo != None or current_online_repo.nextRepo != None:

            if (current_online_repo.url != current_repo.url):
                self.analyze_priority(current_repo, current_online_repo)
            
            current_repo = current_repo.nextRepo
            current_online_repo = current_online_repo.nextRepo
            
        
        

    def analyze_priority(self, curr_repo, curr_onrepo):
        """ UPON BUILDING THE ONLINE REPOS GRAPH YOU'LL KNOW HOW TO ANALYZE PRIORITIES """

    


class Crawler:

    def __init__(self, ) -> None:
        self.repos_to_crawl = []


    # mirar también a los topics
    def fetch_repos(self) -> None:
        trending_repos = requests.get('https://gh-trending-api.herokuapp.com/repositories', headers={"accept": "application/json"}).json()
        


        for repo in trending_repos:
            repo_graph = TrendingReposGraph()
            online_graph = self.build_online_graph_analysis(RepoNode(list(self.repo_initializer().values())), [author['url'] for author in repo['builtBy']]) 
            repo_graph.traverse_online_graph(online_graph)
    
    def repo_initializer(self, repo) -> dict:
        gh_token = os.environ['GHTOKEN']

        now = datetime.now()
        sub_date = now - relativedelta(months=6)
        updated_since = sub_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        repo_owner = repo["builtBy"][0]["username"]
        languages = requests.get(f'https://api.github.com/repos/{repo_owner}/{repo["repositoryName"]}/languages',
            headers={"accept": "application/vnd.github.v3+json",
                     "authorization": f"token {gh_token}"})
        
        open_issues = requests.get(f'https://api.github.com/repos/{repo_owner}/{repo["repositoryName"]}/issues',
            headers={"accept": "application/vnd.github.v3+json",
                    "authorization": f"token {gh_token}"})
        last_updated = requests.get(f'https://api.github.com/repos/{repo_owner}/{repo["repositoryName"]}/commits?since={updated_since}',
            headers={"accept": "application/vnd.github.v3+json",
                    "authorization": f"token {gh_token}"})
        return {
            'url': repo['url'],
            'name': repo['repositoryName'],
            'header': repo['description'],
            'languages': list(languages.keys()),
            'stars': repo['totalStars'],
            'openIssues': open_issues[0]['number'],
            'lastUpdated': last_updated
        }
    
    # for now it simply picks the most starred projects from the authors
    # if in a new round a repo has escalated in stars, the graph will place it before the previous ones
    # for analyzing the priorities i'll grab the classification from them both and pick the one more similar to the starter repo
    # The classification results that most alike to the starter repo
    def build_online_graph_analysis(self, starter_node: RepoNode, authors) -> RepoGraph:
        """ FOLLOWS A STRATEGY FOR LOOPING OVER SOME REPOSITORIES ONLINE AND PICKS THEIR DATA """

        authors_repos: list[list[str]] = self.get_authors_repos(authors) # Repos will be returned in starring order
        described_authors_repos: list[list[RepoNode]] = self.describe_url(authors_repos)
        online_graph = RepoGraph(starter_node)
        
        for repo in described_authors_repos[0]:
            online_graph.append_node(repo)

        
        for repos in described_authors_repos[1:]:
            for repo in repos:
                online_graph.append_node(repo, based_on_stars=True)
        
        return online_graph

            
            



    



