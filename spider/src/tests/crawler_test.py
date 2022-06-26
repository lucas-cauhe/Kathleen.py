
import unittest
from unittest import IsolatedAsyncioTestCase
import sys
sys.path.append('/Users/cinderella/Documents/Kathleen-back-weaviate/github-upload/spider/src')  # type: ignore
from spider import Crawler, RepoGraph, RepoNode, RepoNodeInfo 
import requests
from main import GHTOKEN
import asyncio
import logging
class TestCrawler(unittest.TestCase):

    def test_repo_graph(self):
        # Since trending repos api is broken right now, I had to do it like this
        info_dict = {
            'url': 'https://github.com/CatVodTVOfficial/TVBoxOSC', 
            'name':'TVBoxOSC', 
            'header':'', 
            'languages':['Java', 'CSS'],
            'lastUpdated':True, 
            'openIssues':0, 
            'stars':454
        }
        info = RepoNodeInfo(**info_dict) # type: ignore
        node = RepoNode(info)
        test_graph = RepoGraph(node)

        node_info = {**info_dict, 'name': 'dolt', 'url': 'https://github.com/dolthub/dolt', 'languages': ['Go', 'Python']}
        node2 = RepoNode(RepoNodeInfo(**node_info)) # type:ignore
        node_info = {**info_dict, 'name': 'YOLOv6', 'url': 'https://github.com/meituan/YOLOv6', 'languages': ['Python', 'Shell']}
        node3 = RepoNode(RepoNodeInfo(**node_info)) # type:ignore
        node_info = {**info_dict, 'name': 'dospring-cloud-tencentlt', 'url': 'https://github.com/Tencent/spring-cloud-tencent', 'languages': ['Java']}
        node4 = RepoNode(RepoNodeInfo(**node_info)) # type:ignore

        nodes = [node2, node3, node4]
        indices = []
        for node in nodes:
            res = test_graph.append_node(node)
            indices.append(res) # type: ignore
        
        self.assertEqual(1, test_graph.find_node(nodes[0]))
        self.assertEqual(2, test_graph.find_node(nodes[1]))
        self.assertNotEqual(1, test_graph.find_node(nodes[2]))

        test_graph.update_node_at(3, 1)
        self.assertEqual(1, test_graph.find_node(nodes[2]))

class AsyncTests(IsolatedAsyncioTestCase):
    
    
    async def test_crawler(self):
        logging.disable(logging.CRITICAL)
        crawler = Crawler()

        repo1 = requests.get('https://api.github.com/repos/lucas-cauhe/Kathleen.py', headers={"Authorization": f"token {GHTOKEN}"}).json()
        repo2 = requests.get('https://api.github.com/repos/lucas-cauhe/Kathleen', headers={"Authorization": f"token {GHTOKEN}"}).json()
        
        repo1_init = await crawler.repo_initializer(repo1)
        repo2_init = await crawler.repo_initializer(repo2)

        self.assertEqual('Kathleen.py', repo1_init.name)
        self.assertEqual('Kathleen', repo2_init.name)

        self.assertEqual("Kathleen implemented with python via weaviate", repo1_init.header)
        self.assertEqual("Search Engine for github repos", repo2_init.header)

        self.assertListEqual(['Python'], repo1_init.languages, msg="Languages incorrect for repo1")
        self.assertListEqual(['Rust', 'PLpgSQL'], repo2_init.languages, msg="Languages incorrect for repo2")

        self.assertEqual(0, repo1_init.stars)
        self.assertNotEqual(0, repo2_init.stars)

        self.assertEqual(0, repo1_init.openIssues)
        
        self.assertTrue(repo1_init.lastUpdated)



if __name__ == '__main__':
    unittest.main()
