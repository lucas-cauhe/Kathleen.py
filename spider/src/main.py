
import datetime
import weaviate
from weaviate.util import generate_uuid5
import asyncio


from spider import Crawler

import asyncio

client = weaviate.client.Client('http://192.168.0.23:8080')


repo_schema = {
    "languages",
    "header",
    "name",
    "keywords",
    "stars",
    "openIssues",
    "lastUpdated"
}

def has_to_update():

    # Implement better function

    if datetime.datetime.now().hour > 20:
        return True
    return False



async def main():
    
    
    crawl_inputs = {
        'q': {
            'language': 'language:Docker,Shell',
            'stars': 'stars:10..100',
            'in': 'test+in:description'
        },
        'order': 'desc',
        'props': {
            "languages": ['Docker', 'Shell'],
            "name": 'Kathleen',
            "header": 'test'
        },
        'update': False
    }
    

    crawler = Crawler(crawl_inputs, client)
    crawl_inputs = {**crawl_inputs, 'update': has_to_update()}

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(crawler.crawl()) # Ref: https://peps.python.org/pep-0525/
        #...
    finally:
        loop.close()


    

if __name__ == '__main__':
    asyncio.run(main())