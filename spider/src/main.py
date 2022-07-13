
import weaviate
import asyncio
import json
from spider import Crawler

from utils.constants import DB_LIMIT


client = weaviate.client.Client('http://192.168.0.23:8080')


async def main():
    
    n_repos = len(list(filter(lambda r: r['class']=='Repo', client.data_object.get()['objects'])))
    if n_repos > DB_LIMIT:
        print("Repositories threshold reached, none will be added until space is freed")
    
    # Get crawl_inputs from shared file between envs
    with open('../../common/crawl_inputs.json', 'r') as file:
        crawl_inputs = json.load(file)

    crawler = Crawler(crawl_inputs, client)

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(crawler.crawl()) # Ref: https://peps.python.org/pep-0525/
        #...
    finally:
        loop.close()


    

if __name__ == '__main__':
    while True:
        asyncio.run(main())