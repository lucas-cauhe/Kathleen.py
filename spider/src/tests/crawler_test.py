

from pprint import PrettyPrinter
import unittest
import sys


import weaviate

sys.path.append('/Users/cinderella/Documents/Kathleen-back-weaviate/github-upload/spider/src')  # type: ignore
from spider import Crawler
from classification import classify_repository
from utils.constants import GHTOKEN
from utils.Repo import Repo
from utils.topics import Topics

import requests
import logging
import tracemalloc

from shared.crawler_inputs import CInputs

tracemalloc.start()
client = weaviate.client.Client("http://192.168.0.23:8080")

class AsyncCrawlerTest(unittest.IsolatedAsyncioTestCase):
    
    
    
    async def test_crawler(self):
        logging.disable(logging.WARN)
        logging.disable(logging.CRITICAL)
        logging.disable(logging.DEBUG)
        print("Client is ready? ", client.is_ready())
        
        crawl_inputs = {
            'q': {
                'language': 'language:Python,Shell',
                'stars': 'stars:10..100',
                'in': 'search+in:description'
            },
            'order': 'desc',
            'props': {
                "languages": ['Python', 'Shell'],
                "name": 'Kathleen',
                "header": 'search'
            },
            'update': False,
            'topics': {
                'general': True,
                'collaborators': False
            }
        }
        crawler = Crawler(crawl_inputs, client) # type: ignore

        """ REPO_INITIALIZER """
        
        repo1 = requests.get('https://api.github.com/repos/lucas-cauhe/Kathleen.py', headers={"Authorization": f"token {GHTOKEN}"}).json()
        repo2 = requests.get('https://api.github.com/repos/lucas-cauhe/Kathleen', headers={"Authorization": f"token {GHTOKEN}"}).json()
        
        repo1_init = await Repo(input_repo=repo1).build()
        repo2_init = await Repo(input_repo=repo2).build()

        self.assertEqual('Kathleen.py', repo1_init.repo.name)
        self.assertEqual('Kathleen', repo2_init.repo.name)

        self.assertEqual("Kathleen implemented with python via weaviate", repo1_init.repo.header)
        self.assertEqual("Search Engine for github repos", repo2_init.repo.header)

        self.assertListEqual(['Python'], repo1_init.repo.languages, msg="Languages incorrect for repo1")
        self.assertListEqual(['Rust', 'PLpgSQL'], repo2_init.repo.languages, msg="Languages incorrect for repo2")

        self.assertEqual('0', repo1_init.repo.stars)
        self.assertNotEqual('0', repo2_init.repo.stars)

        self.assertEqual('0', repo1_init.repo.openIssues)
        
        self.assertTrue(repo1_init.repo.isUpdated)

        

        """ FETCH_REPOS """

        
        """ 
        crawl_inputs = {**crawl_inputs, 'match': 'amigo', 'q': {**crawl_inputs['q'], 'in': 'in:readme'}}  
        crawler = Crawler(crawl_inputs, client)
        crawler_fetch_results = crawler.fetch_repos()
        print("CRAWLER FETCHED REPOS: ") 
        PrettyPrinter(sort_dicts=False).pprint(crawler_fetch_results)
        """
        # works

        """ REPO_GEN """

        """ 
        async for gen in crawler.repo_gen():
            print("LENGTH FOR GEN: ", len(gen))

        
        self.assertEqual(len(crawler.repos_to_crawl), 50)
        # works even if it throws several warnings
        """
        """ CRAWL """

        await crawler.crawl()
        """ t = Topics()

        print(t._topics)

        async for links in t.scrape():
            print(f"Last indexed topic: {t._last_indexed_topic}")
            print(f"List for topic {t._topics[t._last_indexed_topic]}: {links}")  
              
        t2 = Topics()
        print(f"{t is t2=}")
        print(f"Current page: {t._current_page}") """
        


        


if __name__ == '__main__':
    unittest.main()