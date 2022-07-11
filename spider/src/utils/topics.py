
import asyncio
from typing import AsyncGenerator, Tuple
from bs4 import BeautifulSoup
import requests
from __future__ import annotations
from utils.Repo import Repo
import httpx
import itertools


BASE_GH_REPOS = 'https://api.github.com/repos/'

class Topics:

    _BASE_URL = 'https://github.com/topics'
    _instance = None
    _last_indexed_topic = 0
    _topics = []
    _current_page = 1
    _client = httpx.AsyncClient()

    

    def __new__(cls: type[Topics], *props) -> Topics:
        
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        
        return cls._instance

        

    

    async def scrape(self) -> AsyncGenerator[list[Repo], None]:

        if self._current_page > 6:
            raise SyntaxError # Substitute by custom exception
        
        if self._last_indexed_topic == 0:
            html_res = requests.get(self._BASE_URL+f'?page={self._current_page}').text
            self._topics = self.get_curr_page_topics(html_res)
        
        for topic in self._topics[self._last_indexed_topic:]:
            topic_repos = self.crawl_topic(topic)

            built_repos = await asyncio.gather(
                *map(lambda repo, client: (await client.get(BASE_GH_REPOS+repo[1]+'/'+repo[0], headers=GH_QUERY_HEADERS) for _ in '_').__anext__(),  # type: ignore
                    topic_repos, 
                    itertools.repeat(self._client),)
            )
            yield [await Repo(repo.json()).build() for repo in built_repos]
                
            self._last_indexed_topic = (self._last_indexed_topic+1)%len(self._topics) # Because there are multiple pages

            if self._last_indexed_topic == 0:
                self._current_page += 1
        

    def get_curr_page_topics(self, page:str) -> list[str]:
        soup = BeautifulSoup(page, 'html.parser')
        soup.find_all(...)
    

    def crawl_topic(self, topic: str) -> list[Tuple[str, str]]:
        pass
