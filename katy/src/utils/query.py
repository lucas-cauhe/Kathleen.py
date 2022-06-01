from array import array
from typing import Tuple
from weaviate import Client


def languages_where_filter(langs) -> dict:
    if len(langs) > 1:
        return {
            'operator': 'And',
            'operands': list(map(lambda lang: {
                'path': ['languages', 'Language', 'name'],
                'operator': 'Equal',
                'valueString': lang
            }, langs))
        }
    return {
        'operator': 'Equal',
        'valueString': langs[0],
        'path': ['languages', 'Language', 'name']
    }

def build_where_for(prop: str, value: str or int or bool) -> dict:

    if prop == 'intention':
        return {
            'operator': 'Equal',
            'valueString': value,
            'path': ['hasIntention', 'Intention', 'type']
        }   
    if prop == 'languages':
        
        return languages_where_filter(value)

    if prop == 'stars':
        return {
            'operator': 'Equal',
            'valueInt': value,
            'path': ['stars']
        }

    if prop == 'openIssues':
        return {
            'operator': 'And',
            'operands': [
                {
                    'path': ['openIssues'],
                    'operator': 'GreaterThanEqual',
                    'valueInt': value-10
                },
                {
                    'path': ['openIssues'],
                    'operator': 'LessThanEqual',
                    'valueInt': value+10
                }
            ]
        }
    if prop == 'isUpdated':
        return {
            'operator': 'Equal',
            'valueBoolean': value,
            'path': ['isUpdated']
        }


properties_query_dict = {
    'languages': 'languages { ... on Language { name } }',
    'hasIntention': 'hasIntention { ... on Intention { type } }',
    'stars': 'stars',
    'openIssues': 'openIssues',
    'isUpdated': 'isUpdated'
}

def queryBuild(client: Client, iq: dict) -> Tuple[str, array]:

    selected_properties = ['name']
    where_properties = []
    for property in iq.items():
        if property[1] != None:
            selected_properties.append(properties_query_dict[property[0]])
            where_properties.append(build_where_for(property[0], property[1]))
    
    return ' '.join(selected_properties), where_properties
