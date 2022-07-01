
import weaviate
from weaviate.util import generate_uuid5
import asyncio


from spider import Crawler

from classification import classify_repository, build_reduced_db_instance
import asyncio

#client = weaviate.client.Client('http://192.168.0.23:8080')


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
    
    
    
    

    crawler = Crawler(crawl_inputs={})

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(crawler.crawl()) # Ref: https://peps.python.org/pep-0525/
        #...
    finally:
        loop.close()


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