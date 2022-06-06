
# DESIGN FOR CRAWLING THROUGH GITHUB REPOS
import requests

# LISTA DE URLS 

# Haces una maner de ciclar entre varios repositorios a partir del más trending y cada vez que recorras el ciclo,
# para cada nodo del grafo te preguntas si el nodo actual es el mismo repositorio que el ciclo que estás construyendo
# con los repos que encuentras
# Si coinciden, miras si ha cambiado algo (lo clasificas con weaviate y según los resultados de la clasificación lo actualizas o no, si no
# miras si se ha cambiado algo en el repositorio)
# Si no coinciden tienes que actualizar el grafo incluyendo el nuevo repo

# Investigar cual es el mejor tipo de grafo o árbol para esto

class RepoNode:

    def __init__(self, node_info) -> None:
        self.url = node_info.url
        self.name = None
        self.languages = None
        self.header = None
        self.keywords = None
        self.stars = None
        self.openIssues = None
        self.lastUpdated = None
        self.nextRepo = None
        self.previousRepo = None
    

class RepoGraph:

    def __init__(self) -> None:
        self.head = None

    def append_node(self, node_info) -> int:
        node = RepoNode(node_info)
        if (self.head == None):
            self.head  = node
            return 0
        index = 1
        iter_node = self.head
        while iter_node.nextRepo != None:
            iter_node = iter_node.nextRepo
            index += 1
        iter_node.nextRepo = node
        return index
    
    def update_node_at(self, node_info, from_position, to_position):
        node = RepoNode(node_info)

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



    def find_node(self, node_info) -> int:
        index = 0
        node = RepoNode(node_info)
        iter_node = self.head
        while iter_node.url != node.url:
            iter_node = iter_node.nextRepo
            index += 1
        return index



class TrendingReposGraph(RepoGraph):

    def __init__(self) -> None:
        super().__init__()
    

    def traverse_online_graph(self, online_repo):
        current_repo = self.head
        current_online_repo = online_repo
        
        while current_repo.nextRepo != None or self.next_online_repo(current_online_repo) != None:

            if (current_online_repo.url != current_repo.url):
                self.analyze_priority(current_repo, current_online_repo)
            
            current_repo = current_repo.nextRepo
            current_online_repo = self.next_online_repo(current_online_repo)
            
        
        

    def analyze_priority(self):
        pass


class Crawler:

    def __init__(self, ) -> None:
        self.repos_to_crawl = []


    # mirar también a los topics
    def fetch_repos(self) -> None:
        trending_repos = requests.get('https://gh-trending-api.herokuapp.com/repositories', headers={"accept": "application/json"}).json()
        
        for repo in trending_repos:
            repo_graph = TrendingReposGraph()
            repo_graph.traverse_online_graph()

    




