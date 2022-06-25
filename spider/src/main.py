
import weaviate
from weaviate.util import generate_uuid5
import os
import asyncio
from dotenv import load_dotenv
load_dotenv()
from classification import classify_repository

client = weaviate.client.Client('http://192.168.0.23:8080')
GHTOKEN = os.environ['GHTOKEN']


repo_schema = {
    "languages",
    "header",
    "name",
    "keywords",
    "stars",
    "openIssues",
    "lastUpdated"
}

async def main():
    # Buscas los siguientes x repos
    # Extraes las features
    # query_header = 
    # query_name =
    # query_keywords = 
    # query_stars = 
    # query_issues =
    # last_updated = 

    # Añades las features
    # parte de weaviate
    current_languages = query_languages(client)
    header_upload = {
        "list": query_header
    }
    client.batch(batch_size=4)
    header_beacon = generate_uuid5(f'{query_header}')
    client.batch.add_data_object(header_upload, 'Header', header_beacon)
    languages_beacons = []
    for language in current_languages:
        languages_beacons.append(generate_uuid5(f'{language}'))
        client.batch.add_data_object({'name': language}, 'Language', languages_beacons[-1])
    
    repo_obj = {
        'name': query_name,
        'keywords': query_keywords,
        'stars': query_stars,
        'openIssues': query_issues,
        'isUpdated': last_updated < 6
    }

    repo_uuid = generate_uuid5(f'{query_name}')
    client.batch.add_data_object(repo_obj, 'Repo', repo_uuid)
    client.batch.add_reference(repo_uuid, 'Repo', 'header', header_beacon)
    for beacon in languages_beacons:
        client.batch.add_reference(repo_uuid, 'Repo', 'languages', beacon)
    # You need to flush everything left in the batch that has not been filled
    client.batch.flush()
    classify_repository(client)


if __name__ == '__main__':
    asyncio.run(main())