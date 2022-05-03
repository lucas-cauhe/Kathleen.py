from weaviate import Client


def languages_where_filter(langs) -> dict:
    return {
        'operator': 'And',
        'operands': list(map(lambda lang: {
            'path': ['languages', 'Language', 'name'],
            'operator': 'Equal',
            'valueString': lang
        }, langs))
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

    if prop == 'popularity':
        return {
            'operator': 'Equal',
            'valueString': value,
            'path': ['hasPopularity', 'Popularity', 'tier']
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

def queryBuild(client: Client, iq: dict) -> str:

    selected_properties = ['name']
    where_properties = []
    for property in iq.items():
        if property[1] != None:
            selected_properties.append(property[0])
            where_properties.append(build_where_for(property[0], property[1]))
    
    return selected_properties, where_properties
