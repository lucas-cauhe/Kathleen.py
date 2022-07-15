
from time import sleep
import weaviate
import asyncio
import json
from spider import Crawler

from utils.constants import CINPUTS_PATH, DB_LIMIT
from utils.topics import Topics


def weaviate_setup(client: weaviate.client.Client):

    # Batch config
    client.batch.configure(
        batch_size=10,
        timeout_retries=3,
        callback=None
    )


async def main(crawler: Crawler, client: weaviate.client.Client):
    
    n_repos = len(list(filter(lambda r: r['class']=='Repo', client.data_object.get()['objects'])))
    if n_repos > DB_LIMIT:
        print("Repositories threshold reached, none will be added until space is freed")
    
    # Get crawl_inputs from shared file between envs
    with open(CINPUTS_PATH, 'r') as file:
        crawl_inputs = json.load(file)

    
    crawler.crawl_inputs = crawl_inputs
    await crawler.crawl()


    

if __name__ == '__main__':
    client = weaviate.client.Client(url='http://192.168.0.23:8080', timeout_config=(5, 20))
    weaviate_setup(client)
    t = Topics()
    crawler = Crawler({}, client=client, t=t)
    while True:
        sleep(2)
        asyncio.run(main(crawler, client))