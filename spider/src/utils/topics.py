from __future__ import annotations
import asyncio
import re
from time import sleep
from typing import AsyncGenerator, Optional, Tuple
import uuid
from bs4 import BeautifulSoup
import requests

from utils.Repo import Repo
import httpx
import itertools
from weaviate.client import Client
from utils.constants import GH_QUERY_HEADERS


BASE_GH_REPOS = 'https://api.github.com/repos/'

class Topics:

    _BASE_URL = 'https://github.com/topics'
    _instance = None
    _last_indexed_topic = 0
    _topics = []
    _current_page = 1
    _client = httpx.AsyncClient()
    _scrape_state: Optional[AsyncGenerator] = None

    

    def __new__(cls: type[Topics]) -> Topics:
        
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        
        return cls._instance

    def __init__(self) -> None:
           
        if self._current_page > 6:
            print('All topics have been crawled')
            raise SyntaxError # Substitute by custom exception
        print(self._last_indexed_topic)
        if self._last_indexed_topic == 0:
            html_res = requests.get(self._BASE_URL+f'?page={self._current_page}').text 
            self._topics = self.get_curr_page_topics(html_res)
    

    
    async def scrape(self) -> AsyncGenerator[list[Repo], None]:

        for topic in self._topics[self._last_indexed_topic:]:
            
            topic_repos = self.crawl_topic(topic)
            while len(topic_repos) == 0:
                sleep(5) # Github robots.txt specifies a crawl-delay: 1
                topic_repos = self.crawl_topic(topic)

            fetched_repos = await asyncio.gather(
                *map(lambda repo, client: (await client.get(BASE_GH_REPOS+repo[1]+'/'+repo[0], headers=GH_QUERY_HEADERS) for _ in '_').__anext__(),  # type: ignore
                    topic_repos, 
                    itertools.repeat(self._client),)
            )
            print(self._last_indexed_topic)
            
            yield [await Repo(repo.json()).build() for repo in fetched_repos]
            self._last_indexed_topic = (self._last_indexed_topic+1)%len(self._topics) # Because there are multiple pages

            if self._last_indexed_topic == 0:
                self._current_page += 1
            
            

            
            
            
        
    # Perhaps listing sub paths of the base url would be much faster than scraping the entire page
    # If you know how I'd like to hear it!
    def get_curr_page_topics(self, page:str) -> list[str]:
        soup = BeautifulSoup(page, 'html.parser')

        all_links = soup.find_all('a', href=re.compile('topics'))
        filtered_list = set([param[7:] for link in all_links if '/topics/' in (param := link.get('href'))]) # Delete duplicates and unwanted links
        
        return list(filtered_list)

    def crawl_topic(self, topic: str) -> list[Tuple[str, str]]: # [(<<repo name>>, <<repo owner>>)]
        
        topic_page = requests.get(self._BASE_URL+topic).text
        soup = BeautifulSoup(topic_page, 'html.parser')

        all_links = soup.find_all('a', 'text-bold wb-break-word')
        repos_list = list(map(self.parse_tuple, all_links[:5]))
        print(f"Repos selected to index: {repos_list}")
        
        return repos_list

    def parse_tuple(self, link) -> Tuple[str, str]:
        url = link.get('href')[1:].split('/')
        return (url[1], url[0])

    
    def update_intention(self, client: Client, repos_ids: list[str]) -> None:
        current_topic = self._topics[self._last_indexed_topic][1:]
        tp_id = uuid.uuid5(uuid.NAMESPACE_URL, current_topic)
        if client.data_object.exists(tp_id):
            print(f'Topic with id {tp_id} already exists')
            return 
        client.data_object.create({'type': current_topic}, 'Intention', uuid=str(tp_id))
        
        for repo_id in repos_ids:
            client.batch.add_reference(repo_id, "Repo", "hasIntention", str(tp_id))
        
        client.batch.flush()
        

