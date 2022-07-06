
from weaviate import client
from utils.Repo import Repo
import uuid
from uuid import uuid5

def del_duplicates(w_client: client.Client, repos: list[Repo]) -> list[Repo]:

    res = w_client.query.get("Repo", ["_additional {id}"]).do()
    res_ = res['data']['Get']['Repo']
    existing_keys = set([key['_additional']['id'] for key in res_])
    new_keys = set([uuid5(uuid.NAMESPACE_URL, r.repo.name) for r in repos])
    diff_keys = existing_keys.intersection(new_keys)
    
    ret_list = []
    for key, val in  enumerate(new_keys):
        if not val in diff_keys:
            ret_list.append(repos[key])
    
    return ret_list
