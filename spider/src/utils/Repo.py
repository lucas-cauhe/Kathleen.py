
from ctypes import Union
from dataclasses import dataclass, field
from weaviate import Client

@dataclass
class Repo():

    w_client: Client
    repo: dict[str, Union[str, dict[str, str]]] # type:ignore
    properties: list[str] = field(init=False, default_factory=list)
    

    def __post_init__(self):

        schema = self.w_client.schema.get()
        repo_class = dict(filter(lambda c: c["class"] == "Repo", schema["classes"]))

        self.properties = [prop["name"] for prop in repo_class["properties"]]
    
    def get_properties(self) -> list[str]:
        return self.properties





