import os
from dotenv import load_dotenv
load_dotenv()

TRENDING_REPOS_BASE_URL = 'https://gh-trending-api.herokuapp.com/repositories'
GH_BASE_SEARCH_URL='https://api.github.com/search/repositories'
CRAWL_LIMIT = 50
GHTOKEN = os.environ['GHTOKEN']
GH_QUERY_HEADERS={"accept": "application/vnd.github.v3+json",
                "authorization": f"token {GHTOKEN}"}
        

