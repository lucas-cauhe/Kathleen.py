
# DESIGN FOR CRAWLING THROUGH GITHUB REPOS
from __future__ import annotations
import enum

import itertools
from select import kevent
from typing import AsyncGenerator, Dict, Union
import time
import weaviate
import uuid
from utils.Repo import Repo
from utils.constants import CRAWL_LIMIT,GH_BASE_SEARCH_URL, GH_QUERY_HEADERS

import requests
from classification import classify_repository
from utils.cluster import KMedoids
import numpy as np

from utils.deduplicates import del_duplicates
from utils.topics import Topics



"""
 TODO: Enhance repos fetching, perhaps tweaking crawl inputs generation -> Go through each collaborator in repos of some topics adding
        their most important repos as well and classifying their intention (for next version)
        
        Implement intent recognition for the description field from the user input


"""



class Crawler:

    def __init__(self, crawl_inputs: Dict[str, Union[int, str]], client: weaviate.client.Client, t: Topics) -> None:
        self.repos_to_crawl: list[Repo] = []
        self.crawl_inputs = crawl_inputs
        self.w_client = client
        self.topics = t
        
        while self.topics._topics == []:
            print("topics not yet initialized")
            time.sleep(5)
            self.topics.__init__()
    
    async def repo_gen(self) -> AsyncGenerator[list[Repo], None]:
        
        it = 0
        
        while len(self.repos_to_crawl) < CRAWL_LIMIT:
            working_repos = []
            if self.crawl_inputs['update'] == 'True':
                working_repos = [await Repo(input_repo=repo['properties']).build(for_embedings=True) for repo in self.w_client.data_object.get()['objects'] if repo['class'] == 'Repo']
            elif self.crawl_inputs['topics']['general'] == 'True':
                try:
                    if self.topics._scrape_state == None:
                        self.topics._scrape_state = self.topics.scrape()
                    working_repos = await self.topics._scrape_state.__anext__()
                        
                except: 
                    print('Error on topics')
            else:

                working_repos = await self.fetch_repos(it)
                
            it += 1
            working_repos_ = del_duplicates(self.w_client, working_repos)
            self.repos_to_crawl.extend(working_repos_)
            yield working_repos_

        

    async def fetch_repos(self, page: int) -> list[Repo]:
        match=self.crawl_inputs.get('match', '')
        within, stars, languages = self.crawl_inputs['q'].get('in', ''), self.crawl_inputs['q'].get('stars', ''), self.crawl_inputs['q'].get('language', '') # type: ignore
        query_params = f'{"+"+within if within else ""}{"+"+stars if stars else ""}{"+"+languages if languages else ""}' # type: ignore
        sort: str = self.crawl_inputs.get('sort', None) # type: ignore
        order: str = self.crawl_inputs.get('order', None) #type: ignore
        attach = f'?q={match}{query_params}{"&sort="+sort if sort else ""}{"&order="+order if order else ""}&per_page=10&page={page}'

        
        res = requests.get(GH_BASE_SEARCH_URL+attach, headers=GH_QUERY_HEADERS).json()
        built_repos = [await Repo(input_repo=repo).build() for repo in res["items"]]
        return built_repos

    async def crawl(self) -> None:
        """ TAKES THE REPOS FROM <<repos_to_crawl>> AND ADDS THEM TO THE DB AND CLASSIFIES THEM """  

        cluster = None
        desirded_medoids = None

        if self.cinputs_by_search():
            # start kmedoids
            # you have to change this since at most it will retrieve QUERY_DEFAULTS_LIMIT objects
            # Making a query should return them all
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
        repos_added = []
        async for generator in self.repo_gen():
            
            # Add repos to db (retrieving vectorized repo), retrieve nearest neighbors, if nearest neighbors are members of medoid
            # desired (decided by crawl_inputs), repo stays.
            # If no crawl_inputs are set, every repo close enough to a medoid will be added
            added_repos_ids = []
           
            
            for repo in generator:
                repo_id = uuid.uuid5(uuid.NAMESPACE_URL, repo.repo.name) # This will handle duplicates
                added_repos_ids.append(str(repo_id))
                
                self.w_client.batch.add_data_object(dict(repo.repo), 'Repo', uuid=str(repo_id)) # Will only add non duplicate object ids
            
            try:
                print("Shape before: ", self.w_client.batch.shape)
                response = self.w_client.batch.create_objects()
                print("Shape after: ", self.w_client.batch.shape)
            except:
                print('Batches may not have been added')

            if self.crawl_inputs['topics']['general'] == 'True':
                self.topics.update_intention(self.w_client, added_repos_ids)
            
            if self.cinputs_by_search():
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
                for k, _ in enumerate(added_repos_ids):
                    neigh_ids = [nei['_additional']['id'] for nei in real_neighbors[k]]
                    obj = [repo for repo in main_objects['objects'] if repo["class"] == "Repo"]
                    add_to_members = []
                    for k_, val in enumerate(obj):

                        if val['id'] in neigh_ids:
                            add_to_members.append(k_)
                    member_neighbors.append(add_to_members)
                
                medoid_members = cluster.members[member_neighbors]

                for k, val in enumerate(medoid_members):
                    medoid = np.bincount(val).argmax()
                    
                    if medoid in desirded_medoids:
                        repos_added.append(added_repos_ids[k])
                        added_repos_ids[k] = None
                        
                repos_to_delete.extend(list(filter(None, added_repos_ids)))
            

        # delete in batches unwanted repos
        
        print('Deleting unwanted fetched repos')
        for repo_id in repos_to_delete:
            try:
                self.w_client.data_object.delete(repo_id)
            except:
                print(f"Repo with id: {repo_id} not found while deleting it")
            time.sleep(0.5) 
         
        # run classification after having added the desired repos
        print("Topics: ", self.topics._topics)
        if self.crawl_inputs['topics']['general'] != 'True':
            classify_repository(self.w_client)
        
            
            

          
        self.repos_to_crawl = []
    
    
    def cinputs_by_search(self) -> bool:
        return not self.crawl_inputs['update'] == 'True' and not self.crawl_inputs['topics']['general'] == 'True'

    
