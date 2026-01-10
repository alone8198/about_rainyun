#!/usr/bin/env python3
"""
GitHub 仓库全能管理工具
"""

import os
import sys
import json
import requests
import subprocess
from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

# ==================== 工具函数 ====================

def clear_screen():
    """跨平台清屏函数"""
    os.system('cls' if os.name == 'nt' else 'clear')

def wait_for_input():
    """等待用户按任意键继续，并清屏"""
    input("\n[按 Enter 键返回主菜单...] ")
    clear_screen()

# ==================== 配置类 ====================

class Visibility(Enum):
    PUBLIC = "public"
    PRIVATE = "private"

@dataclass
class RepoConfig:
    """仓库配置"""
    name: str
    description: str = ""
    private: bool = False
    auto_init: bool = True
    gitignore_template: str = ""
    license_template: str = ""
    has_issues: bool = True
    has_projects: bool = True
    has_wiki: bool = True

# ==================== GitHub API 客户端 ====================

class GitHubAPI:
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        self._user_info = None
    
    @property
    def username(self) -> str:
        if not self._user_info:
            self._user_info = self.get_user()
        return self._user_info['login']
    
    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        full_url = f"{self.BASE_URL}{url}" if not url.startswith("http") else url
        response = requests.request(method, full_url, headers=self.headers, **kwargs)
        if response.status_code >= 400:
            try:
                error = response.json().get("message", "Unknown error")
            except:
                error = response.text
            raise Exception(f"HTTP {response.status_code}: {error}")
        return response

    def get_user(self) -> Dict[str, Any]:
        return self._request("GET", "/user").json()
    
    def get_user_repos(self) -> List[Dict[str, Any]]:
        return self._request("GET", f"/user/repos?per_page=100").json()
    
    def get_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        return self._request("GET", f"/repos/{owner}/{repo}").json()
    
    def create_repo(self, config: RepoConfig) -> Dict[str, Any]:
        data = {
            "name": config.name,
            "description": config.description,
            "private": config.private,
            "auto_init": config.auto_init,
            "gitignore_template": config.gitignore_template,
            "license_template": config.license_template,
            "has_issues": config.has_issues,
            "has_projects": config.has_projects,
            "has_wiki": config.has_wiki,
        }
        return self._request("POST", "/user/repos", json=data).json()
    
    def delete_repo(self, owner: str, repo: str) -> None:
        self._request("DELETE", f"/repos/{owner}/{repo}")
    
    def update_repo(self, owner: str, repo: str, data: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("PATCH", f"/repos/{owner}/{repo}", json=data).json()
    
    def fork_repo(self, owner: str, repo: str) -> Dict[str, Any]:
        return self._request("POST", f"/repos/{owner}/{repo}/forks").json()
    
    def list_branches(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        return self._request("GET", f"/repos/{owner}/{repo}/branches").json()
    
    def create_branch(self, owner: str, repo: str, branch: str, base_sha: str) -> None:
        data = {
            "ref": f"refs/heads/{branch}",
            "sha": base_sha
        }
        self._request("POST", f"/repos/{owner}/{repo}/git/refs", json=data)
    
    def delete_branch(self, owner: str, repo: str, branch: str) -> None:
        self._request("DELETE", f"/repos/{owner}/{repo}/git/refs/heads/{branch}")
    
    def protect_branch(self, owner: str, repo: str, branch: str) -> None:
        url = f"/repos/{owner}/{repo}/branches/{branch}/protection"
        data = {
            "required_status_checks": None,
            "enforce_admins": True,
            "required_pull_request_reviews": None,
            "restrictions": None,
            "allow_force_pushes": False,
            "allow_deletions": False
        }
        self._request("PUT", url, json=data)
    
    def list_releases(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        return self._request("GET", f"/repos/{owner}/{repo}/releases").json()
    
    def create_release(self, owner: str, repo: str, tag: str, name: str, body: str, prerelease: bool = False) -> Dict[str, Any]:
        data = {
            "tag_name": tag,
            "name": name,
            "body": body,
            "prerelease": prerelease
        }
        return self._request("POST", f"/repos/{owner}/{repo}/releases", json=data).json
