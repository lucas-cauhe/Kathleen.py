from array import array
from typing import Tuple, Union
from weaviate import Client

def build_where_for(prop: str, value: Union[str,int,bool, list[str]]) -> dict:

    if prop == 'hasIntention':
        return {
            'operator': 'Equal',
            'valueString': value,
            'path': ['hasIntention', 'Intention', 'type']
        }   
    if prop == 'languages':
        
        return {
            'operator': 'Equal',
            'valueString': value,
            'path': ['languages']
        }

    if prop == 'stars':
        return {
            'operator': 'Equal',
            'valueText': value,
            'path': ['stars']
        }

    if prop == 'openIssues':
        return {
            'operator': 'Equal',
            'valueText': value,
            'path': ['openIssues']
        }
    if prop == 'isUpdated':
        return {
            'operator': 'Equal',
            'valueBoolean': value,
            'path': ['isUpdated']
        }


properties_query_dict = {
    'languages': 'languages',
    'hasIntention': 'hasIntention { ... on Intention { type } }',
    'stars': 'stars',
    'openIssues': 'openIssues',
    'isUpdated': 'isUpdated'
}

def queryBuild(client: Client, iq: dict) -> Tuple[str, list[str]]:

    selected_properties = ['name']
    where_properties = []
    for property in iq.items():
        print(f"{property=}")
        if property[1] != None:
            selected_properties.append(properties_query_dict[property[0]])
            where_properties.append(build_where_for(property[0], property[1]))
    
    return ', '.join(selected_properties), where_properties
