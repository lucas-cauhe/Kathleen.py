
# DESIGN FOR CRAWLING THROUGH GITHUB REPOS
from __future__ import annotations

import itertools
from typing import AsyncGenerator, Dict, Union
import time
import weaviate
from weaviate.util import generate_uuid5
from utils.Repo import Repo
from utils.constants import CRAWL_LIMIT,GH_BASE_SEARCH_URL, GH_QUERY_HEADERS

import requests
from classification import classify_repository
from utils.cluster import KMedoids
import numpy as np
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


   

class Crawler:

    def __init__(self, crawl_inputs: Dict[str, Union[int, str]], client: weaviate.client.Client) -> None:
        self.repos_to_crawl: list[Repo] = []
        self.crawl_inputs = crawl_inputs
        self.w_client = client

    # mirar también a los topics
    async def repo_gen(self) -> AsyncGenerator[list[Repo], None]:
        # The repos you now have to fetch is by searching along with crawl_inputs
        while len(self.repos_to_crawl) < CRAWL_LIMIT:
            new_repos = await self.fetch_repos()
            self.repos_to_crawl.extend(new_repos)
            yield new_repos

        

    async def fetch_repos(self) -> list[Repo]:
        match=self.crawl_inputs.get('match', '')
        within, stars, languages = self.crawl_inputs['q'].get('in', ''), self.crawl_inputs['q'].get('stars', ''), self.crawl_inputs['q'].get('language', '') # type: ignore
        query_params = f'{"+"+within if within else ""}{"+"+stars if stars else ""}{"+"+languages if languages else ""}' # type: ignore
        sort: str = self.crawl_inputs.get('sort', None) # type: ignore
        order: str = self.crawl_inputs.get('order', None) #type: ignore
        attach = f'?q={match}{query_params}{"&sort="+sort if sort else ""}{"&order="+order if order else ""}&per_page=10'

        
        res = requests.get(GH_BASE_SEARCH_URL+attach, headers=GH_QUERY_HEADERS).json()
        built_repos = [await Repo(self.w_client, input_repo=repo).build() for repo in res["items"]]
        return built_repos

    async def crawl(self) -> None:
        """ TAKES THE REPOS FROM <<repos_to_crawl>> AND ADDS THEM TO THE DB AND CLASSIFIES THEM """  
       
        # start kmedoids
        main_objects = self.w_client.data_object.get(with_vector=True)
        vectors = np.array([repo['vector'] for repo in main_objects['objects'] if repo["class"] == "Repo"])
        
        
        # Compute clusters
        # Clusters will be computed using K-Medoids
        cluster = KMedoids(vectors)
        
        cluster.cluster()

        print("Number of clusters: ", cluster.k)
        print("Members of each cluster: ", cluster.members)
        print("Data length: ", len(cluster.data))

        desirded_medoids = cluster.desired_medoids(self.crawl_inputs, self.w_client)
        print("Desired medoids: ", desirded_medoids)
        
        repos_to_delete = []
        async for generator in self.repo_gen():
            
            # Add repos to db (retrieving vectorized repo), retrieve nearest neighbors, if nearest neighbors are members of medoid
            # desired (decided by crawl_inputs), repo stays.
            # If no crawl_inputs are set, every repo close enough to a medoid will be added
            added_repos_ids = []
           
            
            for repo in generator:
                repo_id = generate_uuid5(repo.repo.name)
                added_repos_ids.append(repo_id)
                
                built_repo = await repo.build()
                
                self.w_client.batch.add_data_object(dict(built_repo.repo), 'Repo', uuid=repo_id)
                
            
            self.w_client.batch.create_objects()

            
            
            init_time = time.time()
            # Try making this concurrent
            vector_repos = list(map(lambda id, client:  client.data_object.get_by_id(id, with_vector=True).get("vector", None), 
                added_repos_ids,
                itertools.repeat(self.w_client)))
            end_time = time.time()

            print(f"Vectors fetched in {end_time-init_time} seconds")


            # Retrieve nearest neighbors  
            
            neighbors = [] 
            for vector in vector_repos:    
                near_vector = {
                    'vector': vector,
                    'limit': 10
                }
                
                
                near_neighbors = self.w_client.query.get("Repo", ["name"]) \
                    .with_near_vector(near_vector) \
                    .with_additional(['certainty', 'id']) \
                    .do()
                neighbors.append(near_neighbors)

            real_neighbors = []
            for neighborhood in neighbors:
                append_neighbors = []
                for neighbor in neighborhood['data']['Get']['Repo']:
                    if neighbor['_additional']['id'] not in added_repos_ids:
                        append_neighbors.append(neighbor)
                real_neighbors.append(append_neighbors)

            # Check if fetched neighbors are members of desired medoids
            # Delete from added_repos_ids those that are the closest to the medoid
           
            
            member_neighbors = []
            for i in range(len(added_repos_ids)):
                neigh_ids = [nei['_additional']['id'] for nei in real_neighbors[i]]
                obj = [repo for repo in main_objects['objects'] if repo["class"] == "Repo"]
                add_to_members = []
                for j in range(len(obj)):

                    if obj[j]['id'] in neigh_ids:
                        add_to_members.append(j)
                member_neighbors.append(add_to_members)
            
            medoid_members = cluster.members[member_neighbors]

            for i in range(len(medoid_members)):
                medoid = np.bincount(medoid_members[i]).argmax()
                
                if medoid in desirded_medoids:
                    added_repos_ids[i] = None
            repos_to_delete.extend([repo_id for repo_id in added_repos_ids if repo_id])
            

        # delete in batches unwanted repos
        
        print('Deleting unwanted fetched repos')
        for repo_id in repos_to_delete:
            try:
                self.w_client.data_object.delete(repo_id)
            except:
                print(f"Repo with id: {repo_id} not found while deleting it")
            time.sleep(0.5) 
         
        # run classification after having added the desired repos

        classify_repository(self.w_client)
          
        self.repos_to_crawl = []
    
    
    

