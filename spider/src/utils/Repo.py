from __future__ import annotations
from ctypes import Union
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional
from dateutil.relativedelta import relativedelta
import asyncio
import httpx
import itertools
from utils.constants import GH_QUERY_HEADERS

@dataclass
class RepoInfo:
    
    name: str
    header: str
    languages: list[str]
    stars: str
    openIssues: str
    isUpdated: bool
    url: Optional[str] = None
    keywords: list[str] = field(default_factory=list)
    hasIntention: Optional[list[Dict[str, str]]] = field(default_factory=list)
    hasPopularity: Optional[list[Dict[str, str]]] = field(default_factory=list)

    def __iter__(self):
        yield 'languages', self.languages
        yield 'header', self.header
        yield 'name', self.name
        yield 'stars', self.stars
        yield 'openIssues', self.openIssues
        yield 'isUpdated', self.isUpdated
        yield 'keywords', self.keywords
    
    

@dataclass
class Repo():

    
    input_repo: dict[str, Union[str, dict[str, str]]] # type:ignore
    repo: Optional[RepoInfo] = None

    
    async def build(self, for_embedings=False) -> Repo:
        
        if for_embedings:
            self.repo = RepoInfo(**self.input_repo)
            return Repo(repo=self.repo, input_repo=self.input_repo)

        now = datetime.now()
        sub_date = now - relativedelta(months=6)
        updated_since = sub_date.strftime("%Y-%m-%dT%H:%M:%SZ")

        repo_owner = self.input_repo['owner']['login'] # type: ignore
        

        base_string = f'https://api.github.com/repos/{repo_owner}/{self.input_repo["name"]}/'
        repo_params = ['languages', 'issues', f'commits?since={updated_since}', 'stargazers']
        
        client = httpx.AsyncClient()
        
        languages, open_issues, last_updated, stars = await asyncio.gather( # type: ignore
            *map(lambda param, client: (await client.get(base_string+param, headers=GH_QUERY_HEADERS) for _ in '_').__anext__(),  # type: ignore
            repo_params, 
            itertools.repeat(client),)
        ) 
        
        
        
        info: Dict[str, Union[str, list[str], int]] = {'url': self.input_repo['url'], # type: ignore
            'name': self.input_repo.get("name", "Not found"),
            'header': self.input_repo['description'],
            'languages': list(languages.json().keys()), # type:ignore
            'stars': str(len(stars.json())),                 # type: ignore
            'openIssues': str(len(open_issues.json())),      # type: ignore
            'isUpdated': len(last_updated.json()) > 0 # type: ignore
        }
        self.repo = RepoInfo(**info) # type: ignore
        return Repo(repo=self.repo, input_repo=self.input_repo)





