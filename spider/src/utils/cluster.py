
from dataclasses import dataclass, field

from typing import Tuple, Optional, Dict, Union
import numpy as np
import weaviate




""" OPT. 2 -> THE NEIGHBOR VECTORS FORM A VECTOR SPACE, HENCE BY COMPUTING A BASE FOR IT WILL GIVE SOME REPRESENTATIVE VECTORS """
""" OPT. 3 -> REVERSE HNSW """

@dataclass 
class KMedoids:
    # FasterPAM k-medoids clustering

    data: np.ndarray[int, np.dtype[np.float64]]
    
    k: Optional[int] = None # if left to default None, the algorithm will find for itself the k that best suits the dataset
    compute_k: bool = field(init=False, default=False)
    # Since you want to return some representative vectors of the db you may consider keeping a list of those n vectors with lower cost
    min_cost: float = field(init=False) # -> list[float] ??? This way you will be considering several possible combinations of medoids which may be repeated in different combinations
    
    medoids: np.ndarray[int, np.dtype[np.int64]] = field(init=False) # if you implement the above, the type would be: list[list[list[st]]] (consider making this a generator (anyway))
    max_k: int = 6
    members: np.ndarray[int, np.dtype[np.int64]] = field(init=False) # type: ignore
    def __post_init__(self) -> None:
        
        if self.k is None:
            self.compute_k = True
            self.k = 1

    def cluster(self) -> None:

        self.data = np.array(self.data)
        k_costs = np.zeros(self.max_k+1)
        k_medoids = [0]
        k_members = [0]

        while self.k <= self.max_k:
            
            medoids_inds = self.initial_medoids()
           
            curr_members, curr_costs, tot_cost = self.compute_cost(medoids_inds)
            
            for i in range(self.k):
                
                for j in range(len(self.data)):
                    if j not in medoids_inds:
                        
                        new_medoids = medoids_inds[:] # if it is later changed to taking more medoids, make a deepcopy
                        new_medoids[i] = j
                        new_members, new_costs, new_tot_cost = self.compute_cost(new_medoids)
                        if tot_cost > new_tot_cost:
                            curr_members, curr_costs, tot_cost = new_members, new_costs, new_tot_cost
                            medoids_inds = new_medoids
            
            if not self.compute_k:
                self.medoids = medoids_inds
                self.members = curr_members[:] # shallow copy so that garbage collector cleans the array
                break
            
            
                
            k_costs[self.k] = tot_cost
            k_medoids.append(medoids_inds[:])
            k_members.append(curr_members[:])
            print("k: ", self.k)
            self.k += 1
            
        if self.compute_k:
            self.elbow_method(k_costs, k_medoids, k_members)

        

    def initial_medoids(self) -> np.ndarray[int, np.dtype[np.float64]]:
        indices = []
        while len(indices) < self.k:
            ind = np.random.randint(0, len(self.data))
            if not ind in indices: 
                indices.append(ind)
                
        
        return np.array(indices)


    def compute_cost(self, medoids) -> Tuple[np.ndarray[int, np.dtype[np.float64]], np.ndarray[int, np.dtype[np.float64]], list[np.float64]]: # type:ignore

        dist_table = np.zeros((len(self.data), self.k)) # type: ignore
        for i in range(self.k):                         # type: ignore
            
            medoid = self.data[medoids[i]]
            for j in range(len(self.data)):
                if j != medoids[i]:
                    dist_table[j][i] = self.compute_distance(medoid, self.data[j])
                
        
        cluster_members_inds = np.argmin(dist_table, axis=1)
        members = np.zeros(len(self.data), dtype=np.int64)
        costs = np.zeros(self.k)
        for i in range(self.k):
            members_inds = np.where(cluster_members_inds==i)
            members[members_inds] = i
            
            costs[i] = np.sum([m[i] for m in dist_table[members_inds]])
        
        return members, costs, sum(costs)

    def compute_distance(self, medoid, vec) -> np.float64:
        return np.sqrt(np.sum((medoid-vec)**2))      

    def elbow_method(self, k_costs, k_medoids, k_members):
        # Not taking derivatives
        max_slope = (0, 0)
        max_cost = 0
        for k in range(1, self.max_k-1):
            cost = k_costs[k]-k_costs[k+1]
            if max_cost < cost:
                max_slope = (k, k+1)
                max_cost = cost


        self.k = max_slope[1]
        self.medoids = k_medoids[self.k]
        self.members = k_members[self.k]

            
    def desired_medoids(self, inp: Dict[str, Union[int, str]], client: weaviate.client.Client, n: int = 1) -> list[int]:

        medoids_counts = np.zeros(shape=self.k, dtype=np.float64)
        weights = {"name": lambda x, y: 0.25 if x==y else 0, 
            "languages": lambda c, x: c/(10*x), 
            "header": lambda x, y: 0.25 if x==y else 0,
            "stars": lambda x, y: 0.1 if int(x)//10 == int(y)//10 else 0,
            "openIssues": lambda x, y: 0.1 if int(x)//10 == int(y)//10 else 0,
            "isUpdated": lambda x, y: 0.05 if x==y else 0}
        current_medoid = 0
        for medoid in self.medoids:
            near_vector = {
                'vector': self.data[medoid],
            }
            
            medoid_repo = client.query.get("Repo", ["name", "languages", "header", "stars", "openIssues", "isUpdated", "keywords"]) \
                .with_near_vector(near_vector) \
                .with_additional(['certainty', 'id']) \
                .do()
            
            
            medoid_repo = medoid_repo['data']['Get']['Repo'][0]
            for prop in list(inp["props"].keys()):
                if prop == "languages":
                    
                    medoids_counts[current_medoid] += weights[prop](sum([1 if lang in medoid_repo['languages'] else 0 for lang in inp["props"]["languages"]]), len(medoid_repo['languages']))
                elif prop in ["header", "name"]:
                     medoids_counts[current_medoid] += weights[prop](medoid_repo[prop], inp["props"][prop])
                else:    
                    medoids_counts[current_medoid] += weights[prop](medoid_repo[prop], getattr(inp, prop))

            current_medoid += 1
        wanted_medoids = []
        
        for _ in range(n):
            curr_max = np.argmax(medoids_counts, axis=0)
            medoids_counts[curr_max] = 0
            wanted_medoids.append(curr_max)
        
        return wanted_medoids
        
    
    
             
                
            
                


    