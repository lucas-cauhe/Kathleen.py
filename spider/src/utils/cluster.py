from dataclasses import dataclass, field
from typing import Tuple, Optional
import numpy as np



""" OPT. 2 -> THE NEIGHBOR VECTORS FORM A VECTOR SPACE, HENCE BY COMPUTING A BASE FOR IT WILL GIVE SOME REPRESENTATIVE VECTORS """
""" OPT. 3 -> REVERSE HNSW """

@dataclass 
class KMedoids():
    # FasterPAM k-medoids clustering

    data: np.ndarray[np.ndarray[np.float64]]
    k: Optional[int] = None # if left to default None, the algorithm will find for itself the k that best suits the dataset
    compute_k: bool = field(init=False, default=False)
    # Since you want to return some representative vectors of the db you may consider keeping a list of those n vectors with lower cost
    min_cost: float = field(init=False) # -> list[float] ??? This way you will be considering several possible combinations of medoids which may be repeated in different combinations
    
    medoids: np.ndarray[np.ndarray[np.float64]] = field(init=False) # if you implement the above, the type would be: list[list[list[st]]] (consider making this a generator (anyway))
    max_k: int = 6
    members: np.ndarray[np.float64] = field(init=False, default_factory=np.ndarray) # type: ignore
    def __post_init__(self) -> None:
        
        if self.k is None:
            self.compute_k = True
            self.k = 2

    def cluster(self) -> None:

        
        k_costs = np.zeros(self.max_k)
        k_medoids = []
        k_members = []

        while True:
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
                self.medoids = self.data[medoids_inds]
                self.members = curr_members[:] # shallow copy so that garbage collector cleans the array
                break

            k_costs[self.k] = tot_cost
            k_medoids[self.k] = medoids_inds[:]
            k_members[self.k] = curr_members[:]
            self.k += 1
            
        if self.compute_k:
            self.elbow_method(k_costs, k_medoids, k_members)

        

    def initial_medoids(self) -> np.ndarray[int]:
        indices = np.array([])  
        for i in range(self.k):
            while True:
                ind = np.random.randint(0, len(self.data))
                if ind not in indices:
                    indices[i] = ind
                    break
        return indices


    def compute_cost(self, medoids) -> Tuple[np.ndarray[np.float64], np.ndarray[np.float64], list[np.float64]]: # type:ignore

        dist_table = np.zeros((len(self.data), self.k)) # type: ignore
        for i in range(self.k):                         # type: ignore
            medoid = self.data[medoids[i]]
            for j in range(len(self.data)):
                if j != medoids[i]:
                    dist_table[j][i] = self.compute_distance(medoid, self.data[j])

        cluster_members_inds = np.argmin(dist_table, axis=1)
        members = np.zeros(len(self.data))
        costs = np.zeros(self.k)
        for i in range(self.k):
            members_inds = np.argwhere(cluster_members_inds==i)
            members[members_inds] = i
            costs[i] = np.sum(dist_table[members_inds][i])
        return members, costs, sum(costs)

    def compute_distance(self, medoid, vec) -> np.float64:
        return np.sqrt(np.sum((medoid-vec)**2))      

    def elbow_method(self, k_costs, k_medoids, k_members):
        # Not taking derivatives
        max_slope = (0, 0)
        max_cost = 0
        for k in range(2, self.max_k+1):
            cost = k_costs[k]-k_costs[k+1]
            if max_cost < cost:
                max_slope = (k, k+1)
                max_cost = cost


        self.k = max_slope[1]
        self.medoids = self.data[k_medoids[self.k]]
        self.members = k_members[self.k]

            


 

            
                


    